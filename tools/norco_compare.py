"""Shell Norco C2 splitter: did the agent reach what Shell's engineers did? No LLM.

Reads the agent's model and its latest design (runs/ws/shell_norco_c2splitter), re-solves the design in DWSIM at the target,
and sets each finding next to the withheld outcome (cases/shell_norco_c2splitter/outcome.json, from Summers et al.,
CET 69 (2018) 703-708). Writes runs/ws/shell_norco_c2splitter/comparison.json with a scorecard the plant page shows.

  PYTHONPATH=. .venv/bin/python tools/norco_compare.py
"""
import json
import re
from pathlib import Path

from plantagent import process, revb
from plantagent.plant import PlantWorkspace, patch

ROOT = Path(__file__).resolve().parents[1]
CASE = "shell_norco_c2splitter"


def column(spec):
    return next(u for u in spec["units"] if u.get("type") == "distillation")


def tray_from_bottom(stage, n_stages, trays=154):
    """DWSIM stage 1 is the condenser and the last stage the reboiler; map a stage onto the real 154 trays."""
    inner = max(n_stages - 2, 1)
    return round((n_stages - 1 - stage) / inner * trays + 0.5)


def section(tray, feed_tray):
    return "pasteurization" if tray >= 145 else "above feed" if tray > feed_tray else "below feed"


def worst(sol, uid):
    u = sol["units"][uid]
    rows = [r for r in u.get("profile") or [] if r.get("flood_frac") is not None]
    return max(rows, key=lambda r: r["flood_frac"]) if rows else None, u


def product(sol, spec, uid, name_hint="ethylene"):
    """Ethylene product kg/h: the column's liquid side draw (or its distillate if there is none)."""
    u = column(spec)
    outs = list(u.get("out") or []) if isinstance(u.get("out"), list) else ([u["out"]] if u.get("out") else [])
    for s in outs + [u.get("distillate")]:
        st = (sol["streams"] or {}).get(s) or {}
        comp = st.get("components_kg_h") or {}
        if comp and comp.get("Ethylene", 0) / max(sum(comp.values()), 1e-9) > 0.5:  # the ethylene product, whatever its purity
            return s, comp.get("Ethylene", 0), sum(comp.values())
    return None, None, None


def text_of(answers):
    return " ".join(json.dumps({k: a.get(k) for k in ("headline", "summary", "proposals", "field_checks", "assumptions")})
                    for a in answers).lower()


def main(session=None):
    """session: a loop's session folder (runs/ws/<case>/work/<id>/session) to score instead of the latest session."""
    oc = json.loads((ROOT / "cases" / CASE / "outcome.json").read_text())
    m = oc["measured_after"]
    w = PlantWorkspace(CASE, "baseten:meta-models/muse-spark-open-1026")
    logs = sorted((ROOT / "runs" / "ws" / CASE).glob("2*/log.jsonl"))
    if session:
        w.answers = json.loads((Path(session) / "answers.json").read_text())
        logs.append(Path(session) / "log.jsonl")
    spec = w.built["spec"]
    uid = column(spec)["id"]
    n = int(column(spec)["stages"])
    fs = column(spec)["feed_stage"]
    fs = fs[0] if isinstance(fs, list) else fs
    feed_tray = tray_from_bottom(int(fs), n)
    design = revb.design_answer(w.answers)
    changes = [c for p in (design or {}).get("proposals") or [] if p.get("verified") for c in p.get("changes") or []]
    if session:  # a loop's last answer, verified or not: the server's verdict is reported next to the scorecard
        design = w.answers[-1]
        changes = [c for p in design.get("proposals") or [] for c in p.get("changes") or []]
    # The agent's prediction is the run its design answer cites last (its own feed slate and operating specs), re-solved here
    # in DWSIM. Its specs do not converge on Shell's exact Feb 2017 feed, so that run is the comparison point; the feed it
    # assumed is reported next to Shell's.
    target = float(json.loads((ROOT / "cases" / CASE / "case.json").read_text()).get("target_scale") or 1.0)
    design_run, design_spec, design_scale = None, None, 1.0
    for label in reversed((design or {}).get("runs") or []):
        for f in logs:
            for line in f.read_text().splitlines():
                d = json.loads(line)
                if d.get("tool") == "run_process" and (d.get("args") or {}).get("label") == label and not (d.get("result") or {}).get("errors") \
                        and abs(float(d["args"].get("scale") or 1.0) - target) <= 0.02:  # the design at the target, not an envelope case
                    design_run, design_spec, design_scale = label, d["args"]["spec"], float(d["args"].get("scale") or 1.0)
        if design_spec:
            break
    before = process.run(spec, 1.0)
    after = process.run(design_spec, design_scale) if design_spec else None
    b_worst, b_u = worst(before, uid)
    rows = []

    # 1. the bottleneck
    if b_worst:
        t = tray_from_bottom(b_worst["stage"], n)
        sec = section(t, feed_tray)
        rows.append({"item": "Bottleneck section today", "agent": f"{sec} (flood {b_worst['flood_frac'] * 100:.0f} % at tray ~{t})",
                     "recorded": "above feed, jet flood 87 % (Table 3; given to the agent as before-data)",
                     "verdict": "match" if sec == "above feed" else "partial" if sec == "pasteurization" else "miss"})

    # 2. the change itself
    old_cf = float((spec.get("limits") or {}).get(uid, {}).get("tray_capacity_factor") or 1.0)
    tray_swap = [c for c in changes if c.get("replace_unit") == uid and (c.get("new_rating") or {}).get("tray_capacity_factor", 0) > old_cf]
    shell_swap = [c for c in changes if c.get("replace_unit") == uid and "diameter_m" in (c.get("new_rating") or {})]
    eff_up = [c for c in changes if (c.get("new_rating") or {}).get("efficiency") or str(c.get("path", "")).endswith(".efficiency")]
    kind = ("higher-capacity trays (capacity factor " + ", ".join(f"{c['new_rating']['tray_capacity_factor']:g}" for c in tray_swap) + ")") if tray_swap \
        else ("a larger shell" if shell_swap else "no tray or shell change")
    rows.append({"item": "Change to the tower internals", "agent": kind + ("; higher tray efficiency" if eff_up else ""),
                 "recorded": "all 154 trays replaced tray-for-tray with high-capacity HiFi Plus trays",
                 "verdict": "match" if tray_swap else "partial" if shell_swap else "miss"})

    new_fs = next((c.get("value") for c in changes if str(c.get("path", "")).endswith(".feed_stage")), None)
    new_fs = new_fs or next(((c.get("new_rating") or {}).get("feed_stage") for c in changes if (c.get("new_rating") or {}).get("feed_stage")), None)
    if new_fs is not None:
        nt = tray_from_bottom(int(new_fs[0] if isinstance(new_fs, list) else new_fs), n)
        rows.append({"item": "Feed tray", "agent": f"moved from ~{feed_tray} to ~{nt} (from the bottom)", "recorded": "moved up, 37 to above 45",
                     "verdict": "match" if nt > feed_tray else "miss"})
    else:
        rows.append({"item": "Feed tray", "agent": "not moved", "recorded": "moved up, 37 to above 45", "verdict": "miss"})

    # 3. predicted against measured, on the feed Shell ran in Feb 2017 (Table 4: 69.3 wt % ethylene, 1,129 normalised kg/h)
    if after and uid in after.get("units", {}):
        a_worst, a_u = worst(after, uid)
        fd = next(iter(design_spec["feeds"].values()))
        ff = after["streams"].get(next(iter(design_spec["feeds"])), {})
        c2 = (ff.get("components_kg_h") or {}).get("Ethylene", 0) / max(ff.get("kg_h") or 1, 1e-9) * 100
        rows.append({"item": "Feed the design was solved for", "agent": f"{fd.get('kg_h', 0) * design_scale:,.0f} kg/h at {c2:.1f} wt % ethylene (run {design_run})",
                     "recorded": f"{m['feed_norm_kg_h'] * m['scale_assumed']:,.0f} kg/h at {m['feed_ethylene_wt_pct']} wt % (Feb 2017, at the assumed scale)",
                     "verdict": "partial" if abs(fd.get("kg_h", 0) * design_scale / (m["feed_norm_kg_h"] * m["scale_assumed"]) - 1) > 0.05 else "match"})
        s0, e0, t0 = product(before, spec, uid)
        s1, e1, t1 = product(after, spec, uid)
        if e1 and t1:
            # judged on the documented spec (cases/<case>/purity.json): ethane in the product at most 0.1 wt %. The model's
            # remaining impurity is methane and nitrogen from the vent split, which the spec leaves to the pasteurisation trays.
            pur = e1 / t1 * 100
            eth = ((after["streams"].get(s1) or {}).get("components_kg_h") or {}).get("Ethane", 0) / t1 * 1e6
            rows.append({"item": "Ethylene product purity after the change", "agent": f"{pur:.2f} wt % ethylene, ethane {eth:,.0f} ppm",
                         "recorded": "99.944 wt % (polymer grade held); spec: ethane at most 1,000 ppm",
                         "verdict": "match" if eth <= 1000 else "partial" if eth <= 5000 else "miss"})
        if a_worst:
            got = a_worst["flood_frac"] * 100
            rows.append({"item": "Jet flood above feed after the change", "agent": f"{got:.0f} % (Fair screen with the new tray rating)",
                         "recorded": f"{m['jet_flood_above_feed_pct']} % (Shell hydraulics, Feb 2017)",
                         "verdict": "match" if abs(got - m["jet_flood_above_feed_pct"]) <= 10 else
                         "partial" if abs(got - m["jet_flood_above_feed_pct"]) <= 20 else "miss"})
        if e0 and e1:
            got, rec = (e1 / e0 - 1) * 100, (m["ethylene_draw_norm_kg_h"] / m["ethylene_draw_before_norm_kg_h"] - 1) * 100
            rows.append({"item": "Ethylene product rate", "agent": f"{got:+.0f} %", "recorded": f"{rec:+.0f} % (576 to 722 normalised kg/h)",
                         "verdict": "match" if abs(got - rec) <= 5 else "partial" if abs(got - rec) <= 10 else "miss"})
        r0 = (b_u.get("reflux") or 0) * (t0 or 0)
        r1 = (a_u.get("reflux") or 0) * (t1 or 0)
        if r0 and r1:
            got, rec = (r1 / r0 - 1) * 100, (m["reflux_norm_kg_h"] / m["reflux_before_norm_kg_h"] - 1) * 100
            rows.append({"item": "Reflux (mass)", "agent": f"{got:+.0f} %", "recorded": f"{rec:+.0f} % (3,503 to 4,003 normalised kg/h)",
                         "verdict": "match" if abs(got - rec) <= 10 else "partial" if abs(got - rec) <= 25 else "miss"})
        eff = next(((c.get("new_rating") or {}).get("efficiency") for c in changes if (c.get("new_rating") or {}).get("efficiency")), None)
        if eff:
            rows.append({"item": "Tray efficiency of the new trays", "agent": f"{eff * 100:.0f} % (assumed)",
                         "recorded": f"{m['tray_efficiency_pct']} % (fitted to the Feb 2017 data)",
                         "verdict": "match" if abs(eff * 100 - m["tray_efficiency_pct"]) <= 3 else "partial"})
        q0, q1 = b_u.get("reboiler_kW"), a_u.get("reboiler_kW")
        if q0 and q1 and e0 and e1:
            per = (q1 / e1) / (q0 / e0) * 100 - 100
            rows.append({"item": "Reboiler duty per kg ethylene", "agent": f"{per:+.0f} %",
                         "recorded": "-6 % (plant, per kg product) to -15 % (paper's balances)",
                         "verdict": "match" if -20 <= per <= 0 else "partial" if per <= 10 else "miss"})
        c0, c1 = b_u.get("condenser_kW"), a_u.get("condenser_kW")
        if c0 and c1:
            rows.append({"item": "Condenser duty (refrigeration load)", "agent": f"{(c1 / c0 - 1) * 100:+.0f} %",
                         "recorded": "not addressed by the project; condenser and refrigeration now limit",
                         "verdict": "match" if c1 > c0 else "partial"})
    rows.append({"item": "Column pressure drop", "agent": "not predicted: DWSIM takes column dP as an input",
                 "recorded": f"{m['column_dP_before_kPa']} to {m['column_dP_kPa']} kPa", "verdict": "not predicted"})

    txt = text_of(w.answers)
    flagged = bool(re.search(r"condens|refrigerat", txt))
    rows.append({"item": "Flags the condenser / refrigeration limit", "agent": "yes, mentioned" if flagged else "not mentioned",
                 "recorded": "Shell left it unaddressed; it now limits the extra capacity", "verdict": "match" if flagged else "miss"})

    verdicts = [{"title": p.get("title"), "verified": p.get("verified"), "reason": p.get("unverified_reason")}
                for p in (design or {}).get("proposals") or []]
    out = {"case": CASE, "design_answer": (design or {}).get("headline"), "design_run": design_run, "changes": changes,
           "session": str(Path(session).relative_to(ROOT)) if session else None, "server_verification": verdicts,
           "source": oc["source"], "scale_assumed": m["scale_assumed"], "scorecard": rows,
           "summary": {k: sum(r["verdict"] == k for r in rows) for k in ("match", "partial", "miss", "not predicted")}}
    (ROOT / "runs" / "ws" / CASE / "comparison.json").write_text(json.dumps(out, indent=1))
    for r in rows:
        print(f"{r['verdict']:>13}  {r['item']}: {r['agent']}  |  {r['recorded']}")
    print(out["summary"])


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
