"""Transmission-grid engine: a pandapower AC load flow of a network spec, limit checks against protection settings,
a transit-capacity search and an N-1 contingency screen. Used by grid cases (case.json engine 'pandapower').

pandapower runs in its own venv (.venv-electrical), one subprocess per call, like plantagent/electrical.py.
Usage (worker): .venv-electrical/bin/python -m plantagent.grid --op run < {"spec": ..., "scale": 1.0}
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv-electrical" / "bin" / "python"
KINDS = ("buses", "lines", "trafos", "switches", "gens", "loads", "ext_grids")

SPEC_HELP = (
    "Grid spec (pandapower AC load flow), every element has a unique `id` (use the drawing's names): "
    "{\"grid\": true, \"buses\": [{id, vn_kv}], "
    "\"lines\": [{id, from, to, length_km, r_ohm_per_km, x_ohm_per_km, c_nf_per_km, max_i_ka, parallel (circuits, default 1), "
    "in_service (default true)}], \"trafos\": [{id, hv, lv, sn_mva, vn_hv_kv, vn_lv_kv, vk_percent, vkr_percent, in_service}], "
    "\"switches\": [{id, bus_a, bus_b, closed}] (bus couplers), \"gens\": [{id, bus, p_mw, vm_pu}] (fixed-P injections), "
    "\"loads\": [{id, bus, p_mw, q_mvar}], \"ext_grids\": [{id, bus, vm_pu, va_degree}] (strong grid equivalents; with two or "
    "more, their angle difference sets the transit between them), "
    "\"limits\": {element id: {max_A, where, source}} (protection trip or alarm current per element; a line without a "
    "limits entry is checked against its max_i_ka x parallel thermal rating)}. "
    "`scale` multiplies every gen and load P and every ext_grid angle (the transit through the area). "
    "Changes are path changes: 'switches.<id>.closed' = true/false, 'lines.<id>.in_service' = false, 'gens.<id>.p_mw' = 1400, "
    "'ext_grids.<id>.va_degree' = -4.0.")


def is_grid(spec):
    return isinstance(spec, dict) and bool(spec.get("grid"))


def available():
    return PY.exists()


# ---------------------------------------------------------------- changes (main process, no pandapower needed)

def _index(spec):
    return {(k, e.get("id")): e for k in KINDS for e in spec.get(k) or [] if isinstance(e, dict)}


def change_errors(spec, changes, require_evidence=True):
    idx, errors = _index(spec), []
    for i, c in enumerate(changes or []):
        if not isinstance(c, dict) or not isinstance(c.get("path"), str):
            errors.append(f"change {i + 1}: a grid change is a path change {{path, value}}, e.g. switches.<id>.closed")
            continue
        parts = c["path"].split(".", 2)
        if len(parts) != 3:
            errors.append(f"change {i + 1}: bad path {c['path']}")
            continue
        kind, oid, _ = parts
        if kind == "limits":
            continue  # verify() refuses limit changes on proposals
        if kind not in KINDS:
            errors.append(f"change {i + 1}: unknown element kind {kind} (one of {', '.join(KINDS)})")
        elif (kind, oid) not in idx:
            errors.append(f"change {i + 1}: no {kind[:-1]} with id {oid}")
    return errors


def patch(spec, changes):
    errors = change_errors(spec, changes, require_evidence=False)
    if errors:
        raise ValueError("; ".join(errors))
    s = copy.deepcopy(spec)
    idx = _index(s)
    for c in changes or []:
        kind, oid, field = c["path"].split(".", 2)
        if kind == "limits":
            s.setdefault("limits", {}).setdefault(oid, {})[field] = c["value"]
        else:
            idx[(kind, oid)][field] = c["value"]
    return s


def describe(c):
    kind, oid, field = c["path"].split(".", 2)
    if kind == "switches" and field == "closed":
        return f"{'close' if c['value'] else 'open'} bus coupler {oid}"
    if field == "in_service":
        return f"{'return' if c['value'] else 'switch off'} {kind[:-1]} {oid}"
    return f"{oid} {field} = {c['value']}"


def review(spec, result, basis=""):
    """Deterministic review of a submitted grid model: it solves, every element connects to a defined bus, limits name
    real elements, at least one grid equivalent, and the protection settings cited in the data sheet are on the model."""
    def finding(sev, check, evidence, items=None):
        f = {"severity": sev, "check": check, "evidence": evidence[:500]}
        if items:
            f["items"] = list(dict.fromkeys(items))
        return f
    findings, buses = [], {b.get("id") for b in spec.get("buses") or []}
    for k, ends in (("lines", ("from", "to")), ("trafos", ("hv", "lv")), ("switches", ("bus_a", "bus_b")),
                    ("gens", ("bus",)), ("loads", ("bus",)), ("ext_grids", ("bus",))):
        for e in spec.get(k) or []:
            bad = [e.get(x) for x in ends if e.get(x) not in buses]
            if bad:
                findings.append(finding("block", "unknown bus", f"{k[:-1]} {e.get('id')} connects to undefined bus {bad}", [e.get("id")]))
    if not spec.get("ext_grids"):
        findings.append(finding("block", "no grid equivalent", "a transmission model needs at least one ext_grid (slack) equivalent"))
    ids = {e.get("id") for k in KINDS for e in spec.get(k) or []}
    for lid in spec.get("limits") or {}:
        if lid not in ids:
            findings.append(finding("block", "limit on unknown element", f"limits.{lid} names no element of the model", [lid]))
    if result and result.get("errors"):
        findings.append(finding("block", "load flow does not solve", "; ".join(result["errors"])[:400]))
    if not (spec.get("limits") or {}):
        findings.append(finding("warn", "no protection settings", "no element carries a protection trip/alarm current; only thermal ratings are checked"))
    findings.sort(key=lambda f: (0 if f["severity"] == "block" else 1, f["check"]))
    blocking = sum(f["severity"] == "block" for f in findings)
    return {"status": "model needs review" if blocking else "ok", "findings": findings, "blocking": blocking,
            "energy": {"method": "pandapower", "note": "AC load flow: power balance closes by construction at the slack."}}


# ---------------------------------------------------------------- calls into the pandapower venv

def _call(payload, timeout=240):
    if not available():
        raise RuntimeError(f"pandapower venv missing ({PY}); see docs/electrical.md")
    r = subprocess.run([str(PY), "-m", "plantagent.grid", "--worker"], input=json.dumps(payload),
                       capture_output=True, text=True, cwd=ROOT, timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"pandapower failed: {r.stderr[-800:]}")
    return json.loads(r.stdout)


def run(spec, scale=1.0):
    return _call({"op": "run", "spec": spec, "scale": scale})


def capacity(spec):
    return _call({"op": "capacity", "spec": spec})


def n_minus_1(spec, scale=1.0, elements=None):
    return _call({"op": "n1", "spec": spec, "scale": scale, "elements": elements})


# ---------------------------------------------------------------- worker side (runs inside .venv-electrical)

def _net(spec, scale):
    import pandapower as pp
    net = pp.create_empty_network()
    bus = {b["id"]: pp.create_bus(net, float(b["vn_kv"]), name=b["id"]) for b in spec["buses"]}
    for s in spec.get("switches") or []:
        pp.create_switch(net, bus[s["bus_a"]], bus[s["bus_b"]], et="b", closed=bool(s.get("closed")), name=s["id"])
    for ln in spec.get("lines") or []:
        pp.create_line_from_parameters(net, bus[ln["from"]], bus[ln["to"]], float(ln["length_km"]), float(ln["r_ohm_per_km"]),
                                       float(ln["x_ohm_per_km"]), float(ln.get("c_nf_per_km") or 0), float(ln.get("max_i_ka") or 1.0),
                                       name=ln["id"], parallel=int(ln.get("parallel") or 1), in_service=ln.get("in_service", True) is not False)
    for t in spec.get("trafos") or []:
        pp.create_transformer_from_parameters(net, bus[t["hv"]], bus[t["lv"]], float(t["sn_mva"]), float(t["vn_hv_kv"]), float(t["vn_lv_kv"]),
                                              float(t.get("vkr_percent") or 0.3), float(t["vk_percent"]), 0.0, 0.0, name=t["id"],
                                              in_service=t.get("in_service", True) is not False)
    for g in spec.get("gens") or []:
        pp.create_gen(net, bus[g["bus"]], float(g["p_mw"]) * scale, vm_pu=float(g.get("vm_pu") or 1.0), name=g["id"])
    for ld in spec.get("loads") or []:
        pp.create_load(net, bus[ld["bus"]], float(ld["p_mw"]) * scale, q_mvar=float(ld.get("q_mvar") or 0) * scale, name=ld["id"])
    for e in spec.get("ext_grids") or []:
        pp.create_ext_grid(net, bus[e["bus"]], vm_pu=float(e.get("vm_pu") or 1.0), va_degree=float(e.get("va_degree") or 0) * scale, name=e["id"])
    return net


def _num(x):
    x = float(x)
    return 0.0 if x != x else x  # NaN: element in a de-energised island


def _solve(spec, scale=1.0):
    import pandapower as pp
    try:
        net = _net(spec, scale)
        pp.runpp(net, numba=False, max_iteration=50)
    except Exception as e:  # noqa: BLE001 - a non-converged case is a result the agent must see
        return {"scale": scale, "errors": [f"load flow did not solve: {type(e).__name__}: {e}"[:300]], "streams": {}, "units": {}, "buses": {}, "checks": []}
    limits = spec.get("limits") or {}
    units, checks = {}, []
    for i, row in net.line.iterrows():
        res = net.res_line.loc[i]
        i_a = 0.0 if not row.in_service else _num(res.i_ka) * 1000
        units[row["name"]] = {"type": "line", "from": spec_line_end(spec, row["name"], "from"), "to": spec_line_end(spec, row["name"], "to"),
                              "p_mw": round(_num(res.p_from_mw), 1) if row.in_service else 0.0,
                              "q_mvar": round(_num(res.q_from_mvar), 1) if row.in_service else 0.0,
                              "i_A": round(i_a), "in_service": bool(row.in_service), "circuits": int(row.parallel)}
    for i, row in net.trafo.iterrows():
        res = net.res_trafo.loc[i]
        units[row["name"]] = {"type": "transformer", "p_mw": round(_num(res.p_hv_mw), 1), "i_A": round(_num(res.i_hv_ka) * 1000),
                              "loading_pct": round(_num(res.loading_percent), 1), "in_service": bool(row.in_service)}
    for i, row in net.switch.iterrows():
        units[row["name"]] = {"type": "bus coupler", "closed": bool(row.closed)}
    for i, row in net.gen.iterrows():
        units[row["name"]] = {"type": "injection", "p_mw": round(_num(net.res_gen.p_mw[i]), 1), "q_mvar": round(_num(net.res_gen.q_mvar[i]), 1)}
    for i, row in net.ext_grid.iterrows():
        units[row["name"]] = {"type": "grid equivalent", "p_mw": round(float(net.res_ext_grid.p_mw[i]), 1),
                              "q_mvar": round(float(net.res_ext_grid.q_mvar[i]), 1)}
    for uid, u in units.items():
        if u["type"] not in ("line", "transformer") or not u.get("in_service", True):
            continue
        lim = limits.get(uid) or {}
        if lim.get("max_A"):
            checks.append({"id": uid, "check": f"current vs {lim.get('where') or 'protection setting'}", "value": u["i_A"],
                           "limit": float(lim["max_A"]), "unit": "A", "utilisation": round(u["i_A"] / float(lim["max_A"]), 4),
                           "source": lim.get("source")})
        elif u["type"] == "line":
            row = net.line[net.line.name == uid].iloc[0]
            rating = float(row.max_i_ka) * 1000 * int(row.parallel)
            checks.append({"id": uid, "check": "current vs thermal rating", "value": u["i_A"], "limit": round(rating),
                           "unit": "A", "utilisation": round(u["i_A"] / rating, 4)})
        else:
            checks.append({"id": uid, "check": "loading vs nameplate", "value": u["loading_pct"], "limit": 100.0, "unit": "%",
                           "utilisation": round(u["loading_pct"] / 100, 4)})
    buses = {net.bus.name[i]: {"vm_pu": round(_num(net.res_bus.vm_pu[i]), 4), "va_degree": round(_num(net.res_bus.va_degree[i]), 3),
                               "kv": round(_num(net.res_bus.vm_pu[i]) * float(net.bus.vn_kv[i]), 1)} for i in net.bus.index}
    checks.sort(key=lambda c: -c["utilisation"])
    return {"scale": scale, "errors": [], "streams": {}, "units": units, "buses": buses, "checks": checks}


def spec_line_end(spec, lid, end):
    return next((ln.get(end) for ln in spec.get("lines") or [] if ln.get("id") == lid), None)


def _worst(r):
    return max(r["checks"], key=lambda c: c["utilisation"]) if r["checks"] else None


def _capacity(spec):
    """Largest transit multiple at which every check is within 100 %, by bisection (non-convergence counts as over)."""
    def over(s):
        r = _solve(spec, s)
        return bool(r["errors"]) or (_worst(r) or {}).get("utilisation", 0) > 1, r
    lo, hi = 0.0, 3.0
    if over(1e-3)[0]:
        return {"capacity_multiple": 0.0, "limited_by": _worst(_solve(spec, 1e-3)), "checks_at_capacity": []}
    if not over(hi)[0]:
        lo = hi
    else:
        for _ in range(30):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if over(mid)[0] else (mid, hi)
    r = _solve(spec, lo)
    return {"capacity_multiple": round(lo, 3), "limited_by": _worst(r), "checks_at_capacity": r["checks"][:12]}


def _n1(spec, scale, elements):
    """Outage of each line/transformer (or the listed ones): which limits are exceeded. N-1 secure = none."""
    base = _solve(spec, scale)
    ids = elements or [e["id"] for k in ("lines", "trafos") for e in spec.get(k) or [] if e.get("in_service", True) is not False]
    cases = []
    for eid in ids:
        kind = "lines" if any(ln["id"] == eid for ln in spec.get("lines") or []) else "trafos"
        r = _solve(patch(spec, [{"path": f"{kind}.{eid}.in_service", "value": False}]), scale)
        over = [c for c in r["checks"] if c["utilisation"] > 1]
        cases.append({"out": eid, "errors": r["errors"], "over": over[:6], "worst": _worst(r)})
    cases.sort(key=lambda c: -((c["worst"] or {}).get("utilisation") or 9))
    bad = [c for c in cases if c["over"] or c["errors"]]
    return {"scale": scale, "secure": not bad and not base["errors"], "violations": len(bad), "base_worst": _worst(base), "cases": cases}


if __name__ == "__main__":
    if "--worker" in sys.argv:
        a = json.loads(sys.stdin.read())
        op = a["op"]
        out = (_solve(a["spec"], float(a.get("scale") or 1.0)) if op == "run" else _capacity(a["spec"]) if op == "capacity"
               else _n1(a["spec"], float(a.get("scale") or 1.0), a.get("elements")))
        print(json.dumps(out))
        raise SystemExit
    # self-check: two buses split by an open coupler; closing it moves flow onto the parallel path
    spec = {"grid": True, "buses": [{"id": b, "vn_kv": 380} for b in ("A", "B", "C", "D")],
            "switches": [{"id": "CPL", "bus_a": "A", "bus_b": "B", "closed": False}],
            "lines": [{"id": "A-C", "from": "A", "to": "C", "length_km": 50, "r_ohm_per_km": 0.03, "x_ohm_per_km": 0.26, "max_i_ka": 2},
                      {"id": "B-C", "from": "B", "to": "C", "length_km": 20, "r_ohm_per_km": 0.03, "x_ohm_per_km": 0.26, "max_i_ka": 2},
                      {"id": "A-D", "from": "A", "to": "D", "length_km": 60, "r_ohm_per_km": 0.03, "x_ohm_per_km": 0.26, "max_i_ka": 2}],
            "gens": [{"id": "G", "bus": "D", "p_mw": 800, "vm_pu": 1.03}, {"id": "GB", "bus": "B", "p_mw": 400, "vm_pu": 1.03}],
            "ext_grids": [{"id": "S", "bus": "C", "vm_pu": 1.03}], "limits": {"A-C": {"max_A": 1500, "where": "test relay"}}}
    r = run(spec)
    assert not r["errors"] and r["checks"][0]["id"] in ("A-C", "B-C", "A-D"), r
    closed = run(patch(spec, [{"path": "switches.CPL.closed", "value": True}]))
    assert closed["units"]["A-C"]["p_mw"] != r["units"]["A-C"]["p_mw"]
    n1 = n_minus_1(spec)
    assert n1["cases"] and "secure" in n1
    print("ok", r["units"]["A-C"]["p_mw"], "->", closed["units"]["A-C"]["p_mw"], "N-1 secure:", n1["secure"])
