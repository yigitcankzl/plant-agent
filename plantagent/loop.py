"""Engineering loop: Muse proposes, the engines re-solve and run every check, the failed checks go back to Muse with their
numbers, Muse fixes them; repeat until everything passes, Muse declares the rest unsolvable, or the round/budget limit.
Writes one work log per run (docs/worklog.md). The language model never decides pass/fail: the check rows do."""
import json
import time
from pathlib import Path

from . import llm

UNSOLVABLE = "UNSOLVABLE:"


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def work_dir(w):
    return Path(w.model_file).with_name("work")


def incident_checks(w, idx):
    """Grid and trapped-line cases: limits re-solved with the proposed actions; the grid also gets its N-1 screen.
    (The plant gates are capacity questions and do not apply to an incident scenario.)"""
    from .plant import _is_grid, patch
    ch = [c for p in w.answers[idx].get("proposals") or [] if p.get("verified") for c in p.get("changes") or []]
    v = w.verify({"changes": ch})
    lb, over = v.get("limited_by") or {}, v.get("over_limits_at_target") or []
    eng = "pandapower" if _is_grid(w.cfg) else "DWSIM"
    rows = [{"check": "limits", "engine": eng, "status": "pass" if v.get("reaches_target") and not over else "fail",
             "title": f"{lb.get('id')} {str(lb.get('check'))[:80]}: {lb.get('value')} vs {lb.get('limit')} {lb.get('unit', '')}".strip(),
             "numbers": {"utilisation_pct": round(100 * lb["utilisation"], 1)} if lb.get("utilisation") is not None else None,
             "source": f"{eng} re-solve of the proposed actions"}]
    rows += [{"check": "limits", "engine": eng, "status": "fail", "title": f"{o.get('id')} {o.get('check')} at {round(100 * o.get('utilisation', 0))} %"} for o in over]
    if v.get("relief_basis"):
        rows.append({"check": "relief capacity", "engine": "none", "status": "open", "title": v["relief_basis"]})
    if _is_grid(w.cfg):
        from . import grid
        n1 = grid.n_minus_1(patch(w.built["spec"], ch))
        rows.append({"check": "N-1", "engine": "pandapower", "status": "pass" if n1["secure"] else "fail",
                     "title": "N-1 secure" if n1["secure"] else f"N-1 not secure: {n1['violations']} outage cases over limits",
                     "numbers": {"violations": n1["violations"]}})
    return rows


def checks(w, idx):
    """Flat check rows {check, engine, title, status, numbers?, source?} for the design in answer idx."""
    if w.cfg.get("engine") in ("pandapower", "trapped"):
        return incident_checks(w, idx)
    try:
        from .designchecks import checks_for_design
        return checks_for_design(w, idx)
    except ImportError:  # ponytail: gates only until designchecks.py lands; it adds curves, start-up and uncertainty
        from . import prefeed
        g = prefeed.discipline_gates(w, idx, refresh=True)
        if g.get("error"):
            return [{"check": "process", "engine": "DWSIM", "title": g["error"], "status": "fail"}]
        st = {"pass": "pass", "fail": "fail"}
        return [{"check": r["id"], "engine": r.get("source", "")[:40], "title": r.get("summary", r["id"]),
                 "status": st.get(r.get("status"), "open"), "source": r.get("source")} for r in g.get("disciplines", [])]


def _fix_prompt(goal, issues, last):
    rows = "\n".join(f"- {i['check']}: {i['title']}" + (f" ({json.dumps(i['numbers'])})" if i.get("numbers") else "")
                     for i in issues)
    kept = [p.get("title") for p in (last or {}).get("proposals") or [] if p.get("verified")]
    return (f"Engineering loop, next round. Goal: {goal}\n"
            f"The current design (verified changes: {'; '.join(kept) or 'none'}) was re-solved and checked by the engines. "
            f"These checks FAIL:\n{rows}\n"
            "Propose physical changes that fix each failed check (equipment, ratings with a real item behind them, "
            "operating settings within documented limits), cheapest first. Return the FULL design as proposals: every earlier "
            "verified change you keep plus the new ones, so the design answer stands on its own. Do not edit a limit to pass a "
            f"check. If a failure cannot be fixed with the information available, start the headline with '{UNSOLVABLE}' and "
            "say why and what data would settle it.")


def _muse_step(ans, kind, usd, seconds):
    props = ans.get("proposals") or []
    return {"actor": "muse", "kind": kind, "status": "info", "usd": round(usd, 4), "seconds": round(seconds),
            "title": "; ".join(p.get("title", "") for p in props) or ans.get("headline", ""),
            "detail": ans.get("headline", ""),
            "changes": [c for p in props for c in p.get("changes") or []]}


def run(w, goal, max_rounds=4, budget_usd=12.0, label=None):
    rid = time.strftime("%Y%m%d-%H%M%S")
    out = work_dir(w) / rid
    out.mkdir(parents=True, exist_ok=True)
    log = {"id": rid, "case": w.name, "goal": goal, "label": label, "status": "running", "started": _now(),
           "usd_total": 0.0, "seconds_total": 0, "rounds": [], "result": None, "deliverables": [], "needs_human": []}
    save = lambda: (out / "worklog.json").write_text(json.dumps(log, indent=1, ensure_ascii=False))  # noqa: E731
    t0, usd0 = time.time(), llm.spent()
    issues, last, rows = [], None, []
    try:
        for n in range(1, max_rounds + 1):
            t, u = time.time(), llm.spent()
            ans = w.ask(goal if n == 1 else _fix_prompt(goal, issues, last))
            idx = len(w.answers) - 1
            rnd = {"n": n, "answer_index": idx, "steps": [_muse_step(ans, "propose" if n == 1 else "fix", llm.spent() - u, time.time() - t)]}
            log["rounds"].append(rnd)
            for p in ans.get("proposals") or []:
                rnd["steps"].append({"actor": "engine", "engine": "server verify", "kind": "solve", "title": p.get("title", ""),
                                     "status": "pass" if p.get("verified") else "fail",
                                     "detail": p.get("unverified_reason") or "",
                                     "numbers": {"capacity_pct": round(p["capacity_multiple"] * 100, 1)} if p.get("capacity_multiple") else None})
            last = ans
            save()
            if str(ans.get("headline", "")).startswith(UNSOLVABLE):
                log["status"] = "unsolved"
                break
            if not any(p.get("verified") for p in ans.get("proposals") or []):
                issues = [{"check": "process", "title": "no proposal verified on the server: " +
                           "; ".join(p.get("unverified_reason", "") for p in ans.get("proposals") or [])[:400] or "no proposal made"}]
                rnd["open_issues"] = issues
            else:
                rows = checks(w, idx)
                rnd["steps"] += [{"actor": "engine", "kind": "check", **r} for r in rows]
                issues = [r for r in rows if r.get("status") == "fail"]
                rnd["open_issues"] = [{"check": r["check"], "detail": r.get("title", "")} for r in issues]
                if not issues:
                    log["status"] = "done"
                    save()
                    break
            save()
            if llm.spent() - usd0 >= budget_usd:
                log["status"] = "budget"
                break
        else:
            log["status"] = "max_rounds"
        final = log["rounds"][-1]["answer_index"] if log["rounds"] else None
        log["result"] = {"answer_index": final, "headline": (last or {}).get("headline"),
                         "passes": [r["check"] for r in rows if r.get("status") == "pass"],
                         "fails": [r["check"] for r in rows if r.get("status") == "fail"],
                         "open": [r["check"] for r in rows if r.get("status") == "open"]}
        log["needs_human"] = [f"{r['check']}: {r.get('title', '')}" for r in rows if r.get("status") == "open"] + \
            [f"{c.get('item')}: {c.get('changes', '')}".strip(": ") for c in (last or {}).get("field_checks") or []]
        if log["status"] == "done" and final is not None:
            try:  # the deliverable pack of the passing design (DWSIM re-solve, no model call)
                from . import decision
                pack = decision.make(w, final)
                log["deliverables"].append({"kind": "moc", "title": "MOC decision pack (draft)", "folder": pack.get("folder")})
            except Exception as e:  # noqa: BLE001 - the loop result stands without its pack
                log["deliverables"].append({"kind": "moc", "title": f"MOC pack not generated: {type(e).__name__}: {e}"[:200]})
        log["deliverables"] += [{"kind": a.get("kind"), "title": a.get("title"), "artifact": a.get("id")}
                                for a in (last or {}).get("artifacts") or []]
    except Exception as e:  # noqa: BLE001 - a crashed run still leaves its log
        log["status"] = "error"
        log["error"] = f"{type(e).__name__}: {e}"[:500]
    log["finished"] = _now()
    log["usd_total"] = round(llm.spent() - usd0, 4)
    log["seconds_total"] = round(time.time() - t0)
    save()
    return log


def runs(w):
    d = work_dir(w)
    out = []
    for f in sorted(d.glob("*/worklog.json"), reverse=True):
        x = json.loads(f.read_text())
        out.append({k: x.get(k) for k in ("id", "goal", "status", "usd_total", "started", "label")} | {"rounds": len(x.get("rounds") or [])})
    return out


def load(w, rid):
    f = work_dir(w) / rid / "worklog.json"
    if not rid.replace("-", "").isdigit() or not f.exists():
        return None
    return json.loads(f.read_text())
