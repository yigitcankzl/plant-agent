"""Every engine check on one design answer, as one flat list: what the engineering loop (plantagent/loop.py) reads.

Rows: {check, engine, title, status: pass|fail|open, numbers, source}. No model call; each part reuses its cache
(gates.json, curves.json, uncertainty.json) when the design is unchanged. A part that cannot run is an `open` row,
never a pass.
"""
ENGINE = {"process": "DWSIM", "robustness": "DWSIM", "mechanical": "rating screen", "electrical": "pandapower",
          "heat_transfer": "ht/fluids", "combustion": "Cantera", "piping_utilities": "none", "controls": "none",
          "process_safety": "none", "civil_structural": "none"}
P_TARGET_PASS = 0.8
UNCERTAINTY_N = 48


def _worst(rows):
    rows = [c for c in rows or [] if isinstance(c, dict) and c.get("utilisation") is not None]
    if not rows:
        return {}
    c = max(rows, key=lambda r: r["utilisation"])
    return {k: c.get(k) for k in ("id", "check", "value", "limit", "unit", "utilisation")}


def _open(check, engine, why):
    return {"check": check, "engine": engine, "title": why[:240], "status": "open", "numbers": {}, "source": engine}


def checks_for_design(w, answer_index):
    """Flat check rows for w.answers[answer_index]'s verified proposals taken together (the design)."""
    from . import curves, drafts, prefeed, transient, uncertainty
    rows = []
    try:  # a plant without the engineer's discipline files gets drafts (assumed values), so its checks still run
        drafts.ensure(w)
    except Exception as ex:  # noqa: BLE001
        rows.append(_open("drafts", "drafts", f"discipline drafts could not be made: {type(ex).__name__}: {ex}"))
    try:
        g = prefeed.discipline_gates(w, answer_index)
        if g.get("error"):
            rows.append(_open("process", "DWSIM", g["error"]))
        for d in g.get("disciplines") or []:
            st = d.get("status")
            if st == "not affected":
                continue
            rows.append({"check": d["id"], "engine": ENGINE.get(d["id"], d.get("source") or ""),
                         "title": str(d.get("summary") or d["id"])[:240],
                         "status": st if st in ("pass", "fail") else "open",
                         "numbers": _worst(d.get("checks")), "source": d.get("source") or ""})
    except Exception as ex:  # noqa: BLE001 - a broken part stays open, never green
        rows.append(_open("process", "DWSIM", f"discipline gates could not run: {type(ex).__name__}: {ex}"))
    ov = curves.overlay(w.name)
    if ov:
        pre = f"{drafts.DRAFT}: " if drafts.is_draft(ov) else ""
        try:
            ev = curves.evaluate(w, answer=answer_index)
            target = f"{ev['target_scale']:.2f}"
            for sc, label in ((target, "at the target"), ("1.00", "at today's throughput")):
                r = (ev.get("scales") or {}).get(sc)
                if not r or (sc == "1.00" and target == "1.00"):
                    continue
                if r.get("error"):
                    rows.append(_open(f"curves_{sc}", "curves", f"curve solve {label} failed: {r['error']}"))
                    continue
                over = [c for c in r["checks"] if c.get("utilisation", 0) > 1.0]
                w_ = _worst(r["checks"])
                title = (f"{pre}compressor/pump curves {label}: " +
                         ("; ".join(f"{c['id']} {c['check']} {c['utilisation'] * 100:.0f} %" for c in over[:3]) if over
                          else f"all within curve limits (worst {w_.get('id')} {w_.get('check')} {(w_.get('utilisation') or 0) * 100:.0f} %)"))
                rows.append({"check": "curves" if sc == target else "curves_today", "engine": "curves", "title": title,
                             "status": "fail" if over else "pass", "numbers": w_,
                             "source": ("drafted curve templates (runs/ws/<case>/drafts/curves.json)" if pre else
                                        "performance curves (cases/<case>/curves.json, ILLUSTRATIVE unless vendor)") + " on a DWSIM solve"})
        except Exception as ex:  # noqa: BLE001
            rows.append(_open("curves", "curves", f"curves could not run: {type(ex).__name__}: {ex}"))
    if ov and not drafts.is_draft(ov):  # ponytail: the start-up screen is the salt K-202 model; a general one replaces this gate
        try:
            t = transient.k202_startup(w, save=False, answer=answer_index)
            if t.get("error"):
                rows.append(_open("startup", "transient", t["error"]))
            else:
                bad = [c for c in t["checks"] if not c["pass"]]
                rows.append({"check": "startup", "engine": "transient",
                             "title": "start-up screen: " + ("; ".join(f"{c['check']} ({c['value']} vs {c['limit']} {c['unit']})" for c in bad)
                                                             if bad else "all start-up checks pass"),
                             "status": t["status"], "numbers": {c["check"]: {"value": c["value"], "limit": c["limit"], "unit": c["unit"]} for c in t["checks"]},
                             "source": "lumped start-up screen (plantagent/transient.py), ILLUSTRATIVE parameters"})
        except Exception as ex:  # noqa: BLE001
            rows.append(_open("startup", "transient", f"start-up screen could not run: {type(ex).__name__}: {ex}"))
    try:
        ans = w.answers[int(answer_index)]
        u = uncertainty.cached(w, ans) or uncertainty.assess(w, answer_index, n=UNCERTAINTY_N, workers=4)
        if u and not u.get("error"):
            p = u["p_target"]
            rows.append({"check": "confidence", "engine": "uncertainty",
                         "title": (f"{drafts.DRAFT}: " if drafts.is_draft(drafts.case_file(w.name, "uncertainty.json")) else "") +
                                  f"target met in {p * 100:.0f} % of {u['solved']} re-solves with uncertain inputs varied"
                                  + (f"; most often limited by {u['limiting'][0]['item']}" if u.get("limiting") else ""),
                         "status": "pass" if p >= P_TARGET_PASS else "fail",
                         "numbers": {"p_target": p, **{k: v for k, v in (u.get("capacity") or {}).items()}, "n": u["solved"]},
                         "source": f"{u['method']} (pass at P(target) ≥ {P_TARGET_PASS:.0%})"})
        elif u and "no uncertainty.json" not in u["error"]:
            rows.append(_open("confidence", "uncertainty", u["error"]))
    except Exception as ex:  # noqa: BLE001
        rows.append(_open("confidence", "uncertainty", f"uncertainty could not run: {type(ex).__name__}: {ex}"))
    return rows
