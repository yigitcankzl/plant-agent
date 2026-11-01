"""How sure is the design? Latin-hypercube sampling of the inputs a case marks as assumed, illustrative, provisional or
measured (cases/<case>/uncertainty.json), each varied by a ± band set by its kind, and N re-solves of the combined design:
maximum throughput (capacity bisection) and the solve at the target. Output: P10/P50/P90 of maximum throughput, which item
limits it, the limiting item's load at the target, and the probability the target is met. Deterministic (fixed seed), no
model call. DWSIM samples run on a small pool of solver workers. Cached next to the model (uncertainty.json).
CLI: python -m plantagent.uncertainty <case> [N]
"""
import copy
import hashlib
import json
import os
import random
import select
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAND_PCT = {"documented": 3, "measured": 5, "provisional rating": 10, "assumed": 10, "illustrative": 15}  # ± % per input kind
SEED, N_DEFAULT = 20261101, 40


def _get(spec, path):
    kind, oid, field = path.split(".", 2)
    if kind == "units":
        return next((u.get(field) for u in spec.get("units") or [] if u.get("id") == oid), None)
    return ((spec.get(kind) or {}).get(oid) or {}).get(field)


def lhs(n, k, rng):
    """n Latin-hypercube points in [0, 1)^k."""
    cols = []
    for _ in range(k):
        c = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(c)
        cols.append(c)
    return [[cols[j][i] for j in range(k)] for i in range(n)]


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def samples(spec, inputs, n, seed=SEED):
    """[(factors {path: multiplier}, patched spec)] for n Latin-hypercube points."""
    from .plant import patch
    rng = random.Random(seed)
    out = []
    for pt in lhs(n, len(inputs), rng):
        f = {i["path"]: 1 + (2 * u - 1) * i["band_pct"] / 100 for i, u in zip(inputs, pt)}
        out.append((f, patch(spec, [{"path": p, "value": _get(spec, p) * m} for p, m in f.items()])))
    return out


def _pool(payloads, workers):
    """Run DWSIM worker payloads on `workers` long-lived solver processes (plantagent.process --serve protocol)."""
    procs = [subprocess.Popen([sys.executable, "-m", "plantagent.process", "--serve"], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=ROOT) for _ in range(workers)]
    todo, busy, out = list(enumerate(payloads)), {}, [None] * len(payloads)
    try:
        while todo or busy:
            for p in procs:
                if p not in busy and todo:
                    i, pl = todo.pop(0)
                    p.stdin.write(json.dumps(pl) + "\n")
                    p.stdin.flush()
                    busy[p] = (i, time.time())
            ready, _, _ = select.select([p.stdout for p in busy], [], [], 900)
            if not ready:
                raise RuntimeError("DWSIM workers did not answer within 900 s")
            for p in [q for q in busy if q.stdout in ready]:
                i, _ = busy.pop(p)
                r = json.loads(p.stdout.readline() or '{"worker_error": "worker exited"}')
                out[i] = r
    finally:
        for p in procs:
            p.kill()
    return out


def key(w, ans, inputs, n):
    from .prefeed import gates_key
    blob = json.dumps({"design": gates_key(w, ans)["content"], "inputs": inputs, "n": n, "seed": SEED, "bands": BAND_PCT},
                      sort_keys=True, default=str)
    return hashlib.sha1(blob.encode()).hexdigest()


def _config(w):
    from . import drafts
    cfg = drafts.case_file(w.name, "uncertainty.json", ROOT)  # the engineer's file, else the draft of the assumed inputs
    if not cfg:
        return None
    return cfg, [{**i, "band_pct": i.get("band_pct") or BAND_PCT[i["kind"]]} for i in cfg["inputs"]]


def assess(w, answer=None, n=None, refresh=False, workers=None):
    """Monte Carlo of the design answer (or answers[answer]); cached in uncertainty.json next to the model."""
    from . import revb
    from .plant import patch
    conf = _config(w)
    if not conf:
        return {"error": f"no uncertainty.json for {w.name}"}
    cfg, inputs = conf
    ans = (w.answers[int(answer)] if answer is not None and -len(w.answers) <= int(answer) < len(w.answers)
           else revb.design_answer(w.answers))
    props = [p for p in (ans or {}).get("proposals") or [] if p.get("verified")]
    if not props:
        return {"error": "no verified design answer to assess"}
    n = int(n or cfg.get("n") or N_DEFAULT)
    k = key(w, ans, inputs, n)
    cache = w.model_file.with_name("uncertainty.json")
    if not refresh and cache.exists():
        old = json.loads(cache.read_text())
        if old.get("key") == k:
            return old
    t0 = time.time()
    target = float(w.cfg.get("target_scale") or 1.0)
    spec_d = patch(copy.deepcopy(w.spec), [c for p in props for c in p.get("changes") or []])
    missing = [i["path"] for i in inputs if not isinstance(_get(spec_d, i["path"]), (int, float))]
    if missing:
        return {"error": f"inputs not numeric in the design model: {missing}"}
    pts = samples(spec_d, inputs, n)
    if not w.cfg.get("engine"):  # DWSIM: parallel solver workers
        workers = workers or max(1, min(4, (os.cpu_count() or 2) // 4, n))
        res = _pool([pl for _, s in pts for pl in ({"op": "capacity", "spec": s}, {"op": "run", "spec": s, "scale": target})], workers)
        pairs = [(res[2 * i], res[2 * i + 1]) for i in range(n)]
    else:
        workers = 1
        pairs = [(w._capacity_of(s), w._solve(s, target)) for _, s in pts]
    rows, failed = [], 0
    for (f, _), (cap, at) in zip(pts, pairs):
        lim = cap.get("limited_by") or {}
        # no capacity but a named limit: the design is over that limit at every throughput (e.g. a set point above a supply margin)
        infeasible = cap.get("capacity_multiple") is None and bool(lim) and not cap.get("errors")
        if "worker_error" in cap or "worker_error" in at or (cap.get("capacity_multiple") is None and not infeasible):
            failed += 1
            continue
        checks = [c for c in at.get("checks") or [] if c.get("utilisation") is not None]
        rows.append({"factors": {p: round(m, 4) for p, m in f.items()}, "capacity": cap.get("capacity_multiple"),
                     "infeasible": infeasible, "limited_by": f"{lim.get('id')}: {lim.get('check')}",
                     "at_target": {f"{c['id']}: {c['check']}": c["utilisation"] for c in checks}})
    if not rows:
        return {"error": f"all {n} samples failed to solve"}
    feasible = [r for r in rows if not r["infeasible"]]
    caps = [r["capacity"] for r in feasible] or [0.0]
    share = {}
    for r in rows:
        share[r["limited_by"]] = share.get(r["limited_by"], 0) + 1
    limiting = [{"item": item, "share": round(c / len(rows), 3)} for item, c in sorted(share.items(), key=lambda x: -x[1])]
    top = limiting[0]["item"]
    loads = [r["at_target"].get(top) for r in rows if r["at_target"].get(top) is not None]
    p_target = sum((r["capacity"] or 0) >= target - 1e-9 for r in rows) / len(rows)
    # which input moves capacity most: the mean capacity of each input's high half minus its low half (infeasible = 0)
    drivers = []
    for i in inputs:
        lo = [r["capacity"] or 0.0 for r in rows if r["factors"][i["path"]] < 1]
        hi = [r["capacity"] or 0.0 for r in rows if r["factors"][i["path"]] >= 1]
        if lo and hi:
            drivers.append({"path": i["path"], "kind": i["kind"], "effect": round(statistics.fmean(hi) - statistics.fmean(lo), 4)})
    drivers.sort(key=lambda d: -abs(d["effect"]))
    q = {f"p{int(x * 100)}": round(pct(caps, x), 4) for x in (0.1, 0.5, 0.9)}
    out = {"key": k, "made": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "case": w.name, "answer_headline": ans.get("headline"),
           "method": f"Latin hypercube, {n} samples (seed {SEED}), uniform ± band per input kind; each sample re-solved "
                     f"({'DWSIM' if not w.cfg.get('engine') else w.cfg['engine']}): capacity bisection plus the solve at the target",
           "n": n, "solved": len(rows), "failed": failed, "workers": workers, "seconds": round(time.time() - t0, 1),
           "target": target, "bands_pct": BAND_PCT,
           "inputs": [{"path": i["path"], "kind": i["kind"], "band_pct": i["band_pct"], "base": _get(spec_d, i["path"]),
                       "source": i.get("source")} for i in inputs],
           "capacity": q, "capacity_basis": f"{len(feasible)} feasible samples", "p_target": round(p_target, 3),
           "infeasible_share": round(1 - len(feasible) / len(rows), 3),
           "limiting": limiting,
           "limiting_load_at_target": {"item": top, **{f"p{int(x * 100)}": round(pct(loads, x), 3) for x in (0.1, 0.5, 0.9)}} if loads else None,
           "drivers": drivers,
           "summary": f"Target {target:.0%} met in {p_target:.0%} of {len(rows)} samples"
                      + (f"; {1 - len(feasible) / len(rows):.0%} are over a limit at any throughput ({top})" if len(feasible) < len(rows) else "")
                      + f"; max throughput P10/P50/P90 {q['p10']:.0%} / {q['p50']:.0%} / {q['p90']:.0%}"
                      + (" of the feasible samples" if len(feasible) < len(rows) else "")
                      + f"; most often limited by {top} ({limiting[0]['share']:.0%})"
                      + (f"; biggest driver {drivers[0]['path']} ({drivers[0]['kind']})" if drivers else "") + ".",
           "samples": rows}
    cache.write_text(json.dumps(out, indent=1))
    return out


def cached(w, ans):
    """The cached result for this answer, or None if missing or stale (no solve)."""
    conf = _config(w)
    f = w.model_file.with_name("uncertainty.json")
    if not (conf and ans and f.exists()):
        return None
    u = json.loads(f.read_text())
    return u if u.get("key") == key(w, ans, conf[1], u.get("n")) else None


def markdown(u):
    if not u or u.get("error"):
        return []
    md = ["", "### Uncertainty of the design (Monte Carlo over assumed and illustrative inputs)", "", f"- {u['summary']}",
          f"- Method: {u['method']}; {u['solved']} of {u['n']} samples solved.", "",
          "| Input | Kind | Base | ± band |", "|---|---|---|---|"]
    md += [f"| {i['path']} | {i['kind']} | {i['base']} | {i['band_pct']} % |" for i in u["inputs"]]
    if u.get("limiting_load_at_target"):
        lt = u["limiting_load_at_target"]
        md += ["", f"- {lt['item']} at the target: load P10/P50/P90 {lt['p10']:.0%} / {lt['p50']:.0%} / {lt['p90']:.0%}."]
    return md


if __name__ == "__main__":
    rng = random.Random(1)
    pts = lhs(10, 2, rng)
    assert all(sorted(int(p[j] * 10) for p in pts) == list(range(10)) for j in range(2))  # one point per stratum
    assert pct([1, 2, 3, 4, 5], 0.5) == 3
    if len(sys.argv) > 1:
        from .plant import PlantWorkspace
        r = assess(PlantWorkspace(sys.argv[1]), n=int(sys.argv[2]) if len(sys.argv) > 2 else None, refresh=True)
        print(json.dumps({k: v for k, v in r.items() if k != "samples"}, indent=1))
    print("ok")
