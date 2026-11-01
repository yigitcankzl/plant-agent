"""Every engine check on one design answer, as one flat list: what the engineering loop (plantagent/loop.py) reads.

Rows: {check, engine, title, status: pass|fail|open, numbers, source}. No model call; each part reuses its cache
(gates.json, curves.json, uncertainty.json) when the design is unchanged. A part that cannot run is an `open` row,
never a pass.
"""
import math

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


def separation_checks(spec, solved):
    """Hydraulic screens for phase separators and flooding screens for columns."""
    streams, results, limits = solved.get("streams") or {}, solved.get("units") or {}, spec.get("limits") or {}
    rows = []

    def row(check, engine, title, value, limit, unit, source, higher_is_worse=True):
        util = value / limit if higher_is_worse else limit / value if value else 9.99
        rows.append({"check": check, "engine": engine, "title": title, "status": "fail" if util > 1 else "pass",
                     "numbers": {"value": round(value, 3), "limit": round(limit, 3), "unit": unit,
                                 "utilisation": round(util, 3)}, "source": source})

    for u in spec.get("units") or []:
        uid, kind, lim = u.get("id"), u.get("type"), (limits.get(u.get("id")) or {})
        if kind in ("flash", "separator", "component_separator"):
            names = [u.get(k) for k in ("vapor", "liquid", "product", "reject") if u.get(k)]
            names += list(u.get("out") or []) if isinstance(u.get("out"), list) else ([u.get("out")] if u.get("out") else [])
            phase = [streams[n] | {"name": n} for n in dict.fromkeys(names) if n in streams and not streams[n].get("error")]
            vap = max(phase, key=lambda s: s.get("vapour_frac", 0), default=None)
            liq = min(phase, key=lambda s: s.get("vapour_frac", 1), default=None)
            if not vap or not liq or vap is liq or vap.get("vapour_frac", 0) < 0.5 or liq.get("vapour_frac", 1) > 0.5:
                rows.append(_open(f"separation.{uid}.vapour_velocity", "Souders-Brown", f"{uid}: open: needs vapour and liquid outlet states"))
                rows.append(_open(f"separation.{uid}.residence", "vessel sizing", f"{uid}: open: needs liquid outlet state"))
                continue
            diameter = u.get("diameter_m") or lim.get("diameter_m")
            k_factor = u.get("K_factor_m_s") or lim.get("K_factor_m_s")
            rho_v = vap.get("kg_h") / vap.get("m3_h") if vap.get("m3_h") else None
            rho_l = liq.get("kg_h") / liq.get("m3_h") if liq.get("m3_h") else None
            if diameter and k_factor and rho_v and rho_l and rho_l > rho_v:
                area = math.pi * float(diameter) ** 2 / 4
                velocity = float(vap["m3_h"]) / 3600 / area
                allowable = float(k_factor) * math.sqrt((rho_l - rho_v) / rho_v)
                row(f"separation.{uid}.vapour_velocity", "Souders-Brown",
                    f"{uid}: vapour velocity {velocity:.2f} vs Souders–Brown {allowable:.2f} m/s",
                    velocity, allowable, "m/s", "Souders–Brown velocity using the supplied vessel diameter and K-factor")
            else:
                rows.append(_open(f"separation.{uid}.vapour_velocity", "Souders-Brown",
                                  f"{uid}: open: needs vessel diameter / K-factor and phase densities"))
            level = u.get("normal_liquid_level_pct") or lim.get("normal_liquid_level_pct")
            max_level = u.get("max_liquid_level_pct") or lim.get("max_liquid_level_pct")
            if level is not None and max_level:
                level, max_level = float(level), float(max_level)
                row(f"separation.{uid}.level", "vessel sizing", f"{uid}: normal liquid level {level:g} vs {max_level:g} % maximum",
                    float(level), float(max_level), "%", "supplied vessel level limits")
            liquid_volume = u.get("liquid_volume_m3") or lim.get("liquid_volume_m3")
            total_volume = u.get("volume_m3") or lim.get("volume_m3")
            if liquid_volume is None and total_volume and level is not None:
                liquid_volume = float(total_volume) * float(level) / 100
            residence_limit = u.get("min_residence_min") or lim.get("min_residence_min")
            if liquid_volume and residence_limit and liq.get("m3_h"):
                residence = float(liquid_volume) / float(liq["m3_h"]) * 60
                row(f"separation.{uid}.residence", "vessel sizing",
                    f"{uid}: liquid residence {residence:.2f} vs {float(residence_limit):g} min minimum",
                    residence, float(residence_limit), "min", "liquid holdup divided by solved liquid outlet flow", higher_is_worse=False)
            elif level is None or max_level is None:
                rows.append(_open(f"separation.{uid}.residence", "vessel sizing",
                                  f"{uid}: open: needs liquid volume / residence criterion or level limits"))
        if kind in ("column", "distillation"):
            r = results.get(uid) or {}
            flood = r.get("flood_frac")
            if flood is None:
                rows.append(_open(f"separation.{uid}.flooding", "Fair/Souders-Brown", f"{uid}: open: needs internals"))
            else:
                maximum = float(lim.get("flood_frac_max", 0.8))
                row(f"separation.{uid}.flooding", "Fair/Souders-Brown",
                    f"{uid}: column flooding {float(flood) * 100:.1f} vs {maximum * 100:.0f} %",
                    float(flood), maximum, "fraction of flood", "DWSIM tray traffic with Fair capacity-factor correlation")
    return rows


def purity_checks(w, spec, solved, scale, purity_cfg):
    """Product purity of each column against its spec (cases/<case>/purity.json or the draft), and the lowest reflux that
    still holds the spec at this throughput (DWSIM bisection on the column as built: its stages, feed stage, reboiler spec)."""
    from . import drafts
    from .plant import patch
    rows, cols = [], (purity_cfg or {}).get("columns") or {}
    pre = f"{drafts.DRAFT}: " if drafts.is_draft(purity_cfg) else ""
    src = "drafted purity spec (runs/ws/<case>/drafts/purity.json)" if pre else "product spec (cases/<case>/purity.json)"
    for u in spec.get("units") or []:
        uid = u.get("id")
        if u.get("type") not in ("column", "distillation"):
            continue
        cs = cols.get(uid)
        if not cs:
            rows.append(_open(f"separation.{uid}.purity", "DWSIM", f"{uid}: open: needs a product purity specification"))
            continue

        def meets(sol):
            k = drafts.column_keys(spec, sol, uid)
            if not k:
                return None, {}
            got = {p: next((v / sum((sol["streams"][s].get("components_kg_h") or {}).values())
                            for c_, v in (sol["streams"][s].get("components_kg_h") or {}).items() if c_ == cs[p]["component"]), 0.0)
                   for p, (s, _, _) in k.items() if p in cs}
            return all(got[p] >= cs[p]["min_mass_frac"] for p in got), got

        ok, got = meets(solved)
        if ok is None:
            rows.append(_open(f"separation.{uid}.purity", "DWSIM", f"{uid}: open: product streams did not solve"))
            continue
        for p, f in got.items():
            c = cs[p]
            rows.append({"check": f"separation.{uid}.purity_{p}", "engine": "DWSIM", "status": "pass" if f >= c["min_mass_frac"] else "fail",
                         "title": f"{pre}{uid} {p} {c['component']} {f * 100:.1f} vs {c['min_mass_frac'] * 100:.1f} mass-% minimum",
                         "numbers": {"value": round(f, 4), "limit": c["min_mass_frac"], "unit": "mass fraction",
                                     "utilisation": round(c["min_mass_frac"] / f, 3) if f else 9.99}, "source": f"{src} on the DWSIM solve"})
        r = u.get("reflux_ratio")
        if not isinstance(r, (int, float)):
            continue

        def ok_at(rr):  # ponytail: assumes purity rises with reflux (true away from azeotropes and pinches)
            try:
                return meets(w._solve(patch(spec, [{"path": f"units.{uid}.reflux_ratio", "value": rr}]), scale))[0]
            except Exception:  # noqa: BLE001 - an unsolved reflux counts as not meeting the spec
                return False
        lo, hi = (0.05, float(r)) if ok else (float(r), max(5.0, 4 * float(r)))
        if not ok and not ok_at(hi):
            rows.append(_open(f"separation.{uid}.min_reflux", "DWSIM", f"{uid}: the purity spec is not met at any reflux up to "
                                                                       f"{hi:g} on {u.get('stages')} stages: needs more stages or a different spec"))
            continue
        if ok and ok_at(lo):
            hi = lo
        else:
            for _ in range(7):
                mid = (lo + hi) / 2
                lo, hi = (lo, mid) if ok_at(mid) else (mid, hi)
        rmin = hi
        rows.append({"check": f"separation.{uid}.min_reflux", "engine": "DWSIM", "status": "pass" if ok else "fail",
                     "title": f"{pre}{uid} reflux {float(r):g} vs {rmin:.2f} minimum to hold the purity spec at {scale * 100:.0f} %",
                     "numbers": {"value": float(r), "limit": round(rmin, 3), "unit": "reflux ratio",
                                 "utilisation": round(rmin / float(r), 3) if r else 9.99},
                     "source": f"DWSIM bisection on reflux, {u.get('stages')} stages as built; {src}"})
    return rows


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
        pre = drafts.label(ov)
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
                             "source": ("engineer-uploaded curves merged over the case file (runs/ws/<case>/inputs/resolved/curves.json)"
                                        if drafts.uploaded(ov) else
                                        "drafted curve templates (runs/ws/<case>/drafts/curves.json)" if drafts.is_draft(ov) else
                                        "performance curves (cases/<case>/curves.json, ILLUSTRATIVE unless vendor)") + " on a DWSIM solve"})
        except Exception as ex:  # noqa: BLE001
            rows.append(_open("curves", "curves", f"curves could not run: {type(ex).__name__}: {ex}"))
    try:
        from .plant import patch
        design_spec = patch(w.spec, curves.design_changes(w, answer_index))
        equipment = [u for u in design_spec.get("units") or [] if u.get("type") in
                     ("pump", "compressor", "flash", "separator", "component_separator", "column", "distillation")]
        if equipment:
            try:
                solved = w._solve(design_spec, float(w.cfg.get("target_scale", 1.0)))
            except Exception:  # each equipment row below remains open instead of disappearing with the failed solve
                solved = {"streams": {}, "units": {}}
            rows += separation_checks(design_spec, solved)
            if any(u.get("type") in ("column", "distillation") for u in equipment):
                try:
                    rows += purity_checks(w, design_spec, solved, float(w.cfg.get("target_scale", 1.0)),
                                          drafts.case_file(w.name, "purity.json"))
                except Exception as ex:  # noqa: BLE001
                    rows.append(_open("separation.purity", "DWSIM", f"purity check could not run: {type(ex).__name__}: {ex}"))
            starts = transient.startup_checks(w, design_spec, solved)
            rows += starts
            if starts:
                status = "fail" if any(r["status"] == "fail" for r in starts) else "open" if any(r["status"] == "open" for r in starts) else "pass"
                rows.append({"check": "startup", "engine": "transient", "status": status,
                             "title": f"general start-up screen: {sum(r['status'] == 'pass' for r in starts)} pass, "
                                      f"{sum(r['status'] == 'fail' for r in starts)} fail, {sum(r['status'] == 'open' for r in starts)} open",
                             "numbers": {"rows": len(starts)}, "source": "motor start, acceleration and compressor-ramp screens"})
    except Exception as ex:  # noqa: BLE001
        rows.append(_open("startup", "transient", f"general equipment checks could not run: {type(ex).__name__}: {ex}"))
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
