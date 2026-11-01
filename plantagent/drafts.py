"""Drafts of the case-specific discipline files for a plant that has none: electrical one-line, performance curves,
economics, uncertainty inputs and an operating envelope, made deterministically from the built model (its spec, solved
result and the documents it was built from). No model call, except the optional Muse envelope (draft_envelope(muse=True)).

Each draft is stored under runs/ws/<case>/drafts/<name>.json with "draft": true and every value carrying a provenance:
documented (in the plant's documents), datasheet (a documented rating), muse_default (assumed here), engineer_confirmed.
Loaders prefer the engineer's case file (cases/<case>/<name>.json), then a draft (case_file below), so a hand-written or
confirmed file always wins. A check that ran on a draft says "draft (assumed values)" in its title.
"""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = "draft (assumed values)"
NAMES = ("electrical.json", "curves.json", "economics.json", "uncertainty.json", "prefeed.json")
PROVENANCE = ("documented", "datasheet", "muse_default", "engineer_confirmed")

# IEC 60072 / common catalogue motor ratings (kW)
IEC_KW = [0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250,
          315, 355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1120, 1250, 1400, 1600, 1800, 2000, 2240, 2500, 2800, 3150,
          3550, 4000, 4500, 5000, 5600, 6300, 7100, 8000, 9000, 10000, 11200, 12500, 14000, 16000, 18000, 20000]
# IEC 60076 preferred transformer ratings (MVA)
IEC_MVA = [0.1, 0.16, 0.25, 0.315, 0.4, 0.5, 0.63, 0.8, 1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0,
           20.0, 25.0, 31.5, 40.0, 50.0, 63.0]
_CAB = "typical {v} XLPE Cu manufacturer values (in air, 30 C), muse_default"
CABLES_LV = {f"LV-4x{s}Cu": (r, i) for s, r, i in [(2.5, 7.41, 0.024), (4, 4.61, 0.032), (6, 3.08, 0.041), (10, 1.83, 0.057),
                                                     (16, 1.15, 0.076), (25, 0.727, 0.101), (35, 0.524, 0.125), (50, 0.387, 0.151),
                                                     (70, 0.268, 0.192), (95, 0.193, 0.232), (120, 0.153, 0.269),
                                                     (150, 0.124, 0.309), (185, 0.0991, 0.353), (240, 0.0754, 0.415)]}
CABLES_MV = {f"MV-3x{s}Cu": (r, i) for s, r, i in [(35, 0.524, 0.14), (70, 0.268, 0.205), (95, 0.193, 0.245), (150, 0.124, 0.315),
                                                     (240, 0.0754, 0.41)]}
MV_FROM_KW = 250
# Towler & Sinnott, Chemical Engineering Design 2nd ed. (2012), Table 7.2: Ce = a + b S^n, US Gulf Coast, Jan 2010 (CEPCI 532.9)
TS = {"pump": {"a": 8000, "b": 240, "n": 0.9, "S": "flow L/s", "range": [0.2, 126], "item": "single-stage centrifugal pump"},
      "compressor": {"a": 580000, "b": 20000, "n": 0.6, "S": "driver power kW", "range": [75, 30000], "item": "centrifugal compressor"},
      "hx": {"a": 28000, "b": 54, "n": 1.2, "S": "area m2", "range": [10, 1000], "item": "U-tube shell and tube exchanger"},
      "tank": {"a": 5800, "b": 1600, "n": 0.7, "S": "volume m3", "range": [10, 4000], "item": "cone-roof storage tank"}}
CEPCI = {"base": 532.9, "base_date": "Jan 2010", "now": 797.9, "now_date": "2023 annual average",
         "source": "Chemical Engineering Plant Cost Index (Chemical Engineering magazine); muse_default until updated"}
LANG_FLUID = 4.74  # Towler & Sinnott Table 7.1, fluids-processing plant
UTILITY_PRICES = [  # (test on a utility feed, name, price, unit, field)
    (lambda f: (f.get("T_C") or 99) <= 12, "chilled water", 0.40, "USD per m3", "m3_h"),
    (lambda f: (f.get("T_C") or 99) <= 45, "cooling water", 0.05, "USD per m3", "m3_h"),
    (lambda f: (f.get("T_C") or 0) > 100, "steam", 0.025, "USD per kg", "kg_h"),
]


def _dir(case, root=None):
    return (root or ROOT) / "runs" / "ws" / case / "drafts"


def file_text(case, name, root=None):
    """Raw text of the engineer's cases/<case>/<name> if present, else of the stored draft, else None. root: the caller
    module's ROOT (so a test that moves one module's ROOT moves its files too)."""
    for f in ((root or ROOT) / "cases" / case / name, _dir(case, root) / name):
        if f.exists():
            return f.read_text()
    return None


def case_file(case, name, root=None):
    """The engineer's cases/<case>/<name> if present, else the stored draft, else None."""
    t = file_text(case, name, root)
    return json.loads(t) if t is not None else None


def is_draft(cfg):
    return bool(isinstance(cfg, dict) and cfg.get("draft"))


def _next(xs, v):
    return next((x for x in xs if x >= v - 1e-9), xs[-1])


def _num(v):
    return str(int(v)) if float(v).is_integer() else f"{v:g}"


# ---------- provenance -----------------------------------------------------------------------------------------------
CANDIDATES = {"units": ("U_W_m2K", "eff_pct", "area_m2", "volume_m3", "dP_bar", "P_out_bar"), "feeds": ("T_C", "P_bar"),
              "limits": ("max_m3_h", "max_kg_h", "max_kW", "max_head_m", "max_T_C", "min_residence_min", "max_area_m2")}


def provenance(w):
    """{path: {value, provenance, source}} for the model's numeric inputs. A value written in the plant's own documents
    (basis) next to its tag is documented (datasheet when 'datasheet', 'nameplate' or 'rated' is next to it); anything
    else in the spec was assumed while building. Muse's build notes are not a document: they can state assumptions."""
    docs, spec = getattr(w, "basis", "") or "", w.spec
    pid = ROOT / "cases" / w.name / str((getattr(w, "cfg", None) or {}).get("pid") or "")
    if pid.is_file() and pid.suffix.lower() in (".xml", ".md", ".txt"):  # a DEXPI P&ID is a document too
        docs += "\n" + pid.read_text(errors="ignore")
    out = {}
    def tag(path, v):
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            return
        oid = path.split(".")[1]
        names = {oid, oid.lstrip("sS"), re.split(r"[/_]", oid)[0]} - {""}
        hits = [m.start() for m in re.finditer(r"(?<![\d.])" + re.escape(_num(v)) + r"(?:\.0+)?(?![\d])", docs)
                if any(n in docs[max(0, m.start() - 300):m.start() + 120] for n in names)]
        if not hits:
            out[path] = {"value": v, "provenance": "muse_default", "source": "not found next to its tag in the plant documents: assumed while building"}
            return
        near = any(re.search(r"datasheet|data sheet|nameplate|rated", docs[max(0, h - 120):h + 60], re.I) for h in hits)
        out[path] = {"value": v, "provenance": "datasheet" if near else "documented", "source": "plant documents (basis, P&ID)"}
    for u in spec.get("units") or []:
        for k in CANDIDATES["units"]:
            tag(f"units.{u['id']}.{k}", u.get(k))
    for sid, f in (spec.get("feeds") or {}).items():
        for k in CANDIDATES["feeds"]:
            tag(f"feeds.{sid}.{k}", f.get(k))
    for oid, lim in (spec.get("limits") or {}).items():
        for k in CANDIDATES["limits"]:
            tag(f"limits.{oid}.{k}", (lim or {}).get(k))
    confirmed = _dir(w.name) / "confirmed.json"
    for path, v in (json.loads(confirmed.read_text()) if confirmed.exists() else {}).items():
        out[path] = {"value": v, "provenance": "engineer_confirmed", "source": "confirmed by the engineer"}
    return out


def confirm(case, path, value):
    """Record an engineer-confirmed input value (read by provenance())."""
    f = _dir(case) / "confirmed.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    d = json.loads(f.read_text()) if f.exists() else {}
    d[path] = value
    f.write_text(json.dumps(d, indent=1))
    return d


# ---------- drafts ---------------------------------------------------------------------------------------------------
def _driven(w):
    res = ((getattr(w, "built", None) or {}).get("result") or {}).get("units") or {}
    lims = w.spec.get("limits") or {}
    for u in w.spec.get("units") or []:
        if u.get("type") in ("pump", "compressor"):
            yield u, res.get(u["id"]) or {}, lims.get(u["id"]) or {}


def _motor_eff_pf(kw):
    eff = 0.82 if kw <= 1.1 else 0.87 if kw <= 7.5 else 0.92 if kw <= 37 else 0.95 if kw <= 160 else 0.96
    return eff, (0.80 if kw <= 7.5 else 0.85 if kw <= 75 else 0.88)


def draft_electrical(w):
    """One-line diagram from the driven machines: IEC motor sizes, one MV grid bus, one LV MCC behind a transformer of
    the next IEC size above 1.25 x the connected LV load, cables from an ampacity table."""
    rated = []
    for u, r, lim in _driven(w):
        shaft = float(r.get("kW") or 0)
        if lim.get("max_kW"):
            rated.append((u, float(lim["max_kW"]), "datasheet", f"model limits.{u['id']}.max_kW (from the plant documents)"))
        elif shaft:
            rated.append((u, _next(IEC_KW, shaft * 1.15), "muse_default", f"next IEC rating above solved shaft {shaft:,.1f} kW x 1.15 service margin"))
    if not rated:
        return None
    vn = 11.0 if max(kw for _, kw, _, _ in rated) > 3000 else 6.6  # big drives go to 11 kV
    cable_types = {}

    def cable_for(i_ka, mv):
        """Smallest cable from the table carrying 1.25 x full-load current; parallel runs of the largest when none does."""
        table = CABLES_MV if mv else CABLES_LV
        name = next((k for k, (_, imax) in table.items() if imax >= 1.25 * i_ka), None)
        n = 1
        if not name:
            name = list(table)[-1]
            n = math.ceil(1.25 * i_ka / table[name][1])
        r, imax = table[name]
        key = name if n == 1 else f"{n}x({name})"
        cable_types[key] = {"r_ohm_per_km": round(r / n, 5), "x_ohm_per_km": round(0.08 / n, 5), "c_nf_per_km": 0, "max_i_ka": round(imax * n, 3),
                            "source": _CAB.format(v="6/10 kV" if mv else "0.6/1 kV") + (f", {n} runs in parallel" if n > 1 else "")}
        return key

    motors, lv_kva = [], 0.0
    for u, kw, prov, src in rated:
        eff, pf = _motor_eff_pf(kw)
        mv = kw >= MV_FROM_KW
        kva = kw / eff / pf
        cable = cable_for(kva / (math.sqrt(3) * (vn if mv else 0.4)) / 1000, mv)
        motors.append({"id": f"M-{u['id']}", "unit": u["id"], "bus": "MV" if mv else "LV", "kw": kw, "eff": eff, "pf": pf,
                       "start": "DOL" if kw < 75 else "SOFT", "lrc": 7.0 if kw < 75 else 6.0,
                       "cable": {"type": cable, "length_km": 0.1}, "provenance": prov,
                       "source": f"{src}; efficiency, PF, start, cable (1.25 x full-load current) and 100 m length muse_default"})
        lv_kva += kva * (not mv)
    tx = _next(IEC_MVA, max(lv_kva * 1.25 / 1000, 0.1))
    for k, (r, i), v in (("MV-3x95Cu", CABLES_MV["MV-3x95Cu"], "6/10 kV"), ("LV-4x95Cu", CABLES_LV["LV-4x95Cu"], "0.6/1 kV")):
        cable_types.setdefault(k, {"r_ohm_per_km": r, "x_ohm_per_km": 0.08, "c_nf_per_km": 0, "max_i_ka": i,
                                   "source": _CAB.format(v=v)})  # the new-motor feeders below
    return {"draft": True, "note": f"{DRAFT}: one-line drafted from the motor list of the built model; only motor ratings "
                                    "marked datasheet come from documents. Replace with the site single-line diagram.",
            "buses": [{"id": "MV", "vn_kv": vn, "name": f"{vn:g} kV site supply", "source": "muse_default"},
                      {"id": "LV", "vn_kv": 0.4, "name": "400 V MCC", "source": "muse_default"}],
            "ext_grid": {"bus": "MV", "s_sc_mva": 250, "rx": 0.1, "vm_pu": 1.0, "source": "muse_default site short-circuit level"},
            "transformers": [{"id": "TX-D1", "hv": "MV", "lv": "LV", "sn_mva": tx, "vk_percent": 4.0 if tx <= 0.63 else 6.0,
                              "vkr_percent": 1.0, "tap_percent": 0, "provenance": "muse_default",
                              "source": f"next IEC 60076 rating above 1.25 x connected LV load ({lv_kva:,.0f} kVA)"}],
            "generators": [], "loads": [], "cable_types": cable_types, "motors": motors, "unmodelled_drives": [],
            "new_motor": {"mv_from_kw": MV_FROM_KW, "eff": 0.95, "pf": 0.87, "start": "DOL", "lrc": 6.5,
                          "cable_mv": {"type": "MV-3x95Cu", "length_km": 0.15}, "cable_lv": {"type": "LV-4x95Cu", "length_km": 0.1},
                          "source": "muse_default new motor feeder"},
            "unsupplied_note": "other site loads unknown: not modelled (muse_default)"}


PUMP_SHAPE = [[0.2, 1.18, 0.45], [0.4, 1.15, 0.70], [0.6, 1.10, 0.87], [0.8, 1.05, 0.97], [1.0, 1.00, 1.00],
              [1.1, 0.95, 0.98], [1.2, 0.88, 0.93], [1.3, 0.78, 0.85]]
COMP_SHAPE = [[0.60, 1.10, 0.86], [0.70, 1.10, 0.92], [0.80, 1.08, 0.97], [0.90, 1.05, 0.995], [1.00, 1.00, 1.00],
              [1.10, 0.92, 0.97], [1.18, 0.80, 0.88]]


def draft_curves(w):
    """Normalised generic curves anchored at each machine's rated point (datasheet limits when present, else the
    solved point at 85 % of best-efficiency flow). Positive-displacement pumps have no head-flow curve: skipped."""
    streams = ((getattr(w, "built", None) or {}).get("result") or {}).get("streams") or {}
    units, skipped = {}, []
    for u, r, lim in _driven(w):
        if u["type"] == "pump":
            if "positive" in str(u.get("kind") or r.get("kind") or ""):
                skipped.append(f"{u['id']}: positive displacement, no head-flow curve")
                continue
            q, h = r.get("m3_h"), r.get("head_m")
            if not q or not h:
                skipped.append(f"{u['id']}: no solved flow/head")
                continue
            doc = bool(lim.get("max_m3_h") and lim.get("max_head_m"))
            qd = float(lim["max_m3_h"]) if doc else q / 0.85
            hd = float(lim["max_head_m"]) if doc else h / 1.03  # the solved point sits on the curve at 85 % BEP flow
            units[u["id"]] = {"kind": "pump", "design": {"q_m3_h": round(qd, 2), "head_m": round(hd, 2),
                                                         "eff_pct": float(u.get("eff_pct") or r.get("eff_pct") or 75)},
                              "points": PUMP_SHAPE, "min_flow_q": 0.3, "speed_pct": 100, "variable_speed": False,
                              "provenance": "datasheet" if doc else "muse_default",
                              "basis": (f"generic centrifugal shape anchored at the documented rating {qd:g} m3/h at {hd:g} m" if doc else
                                        f"generic centrifugal shape: solved {q:g} m3/h at {h:g} m taken as 85 % of best-efficiency flow")
                                       + "; minimum continuous flow 30 % of BEP (muse_default)"}
        else:
            s_in, s_out = streams.get(u.get("in")) or {}, streams.get(u.get("out")) or {}
            if not (s_in.get("m3_h") and s_in.get("P_bar") and (s_out.get("P_bar") or u.get("P_out_bar"))):
                skipped.append(f"{u['id']}: suction state not in the solve")
                continue
            pr = float(s_out.get("P_bar") or u["P_out_bar"]) / float(s_in["P_bar"])
            q = float(s_in["m3_h"])
            qd = q * float(lim["max_kg_h"]) / float(s_in["kg_h"]) if lim.get("max_kg_h") and s_in.get("kg_h") else q / 0.95
            units[u["id"]] = {"kind": "compressor", "design": {"q_m3_h": round(qd, 1), "pr": round(pr, 4), "T_in_C": s_in.get("T_C"),
                                                               "eff_pct": float(u.get("eff_pct") or 75)},
                              "points": COMP_SHAPE, "surge_q": 0.62, "stonewall_q": 1.18, "speed_pct": 100,
                              "variable_speed": False, "provenance": "datasheet" if lim.get("max_kg_h") else "muse_default",
                              "basis": "generic single-stage centrifugal map anchored at "
                                       + ("the documented rated mass flow" if lim.get("max_kg_h") else "the solved suction flow taken as 95 % of design")
                                       + "; surge at 62 % of design flow (muse_default)"}
            if lim.get("max_kg_h"):
                units[u["id"]]["anchor_kg_h"] = float(lim["max_kg_h"])
    if not units:
        return None
    return {"draft": True, "basis": f"{DRAFT}: generic curve templates scaled from each machine's rated point; replace with "
                                    "vendor curves before any decision.", "units": units, "skipped": skipped}


def draft_economics(w):
    """Prices and factored-capex basis: Towler & Sinnott correlations escalated by CEPCI, Lang factor for fluids.
    The product price is not knowable from a P&ID: it stays null (the engineer supplies it); margin is then not computed."""
    spec = w.spec
    proc = {k: f for k, f in (spec.get("feeds") or {}).items() if not f.get("utility")}
    if all(f.get("m3_h") for f in proc.values()) and proc:
        base, unit = sum(float(f["m3_h"]) for f in proc.values()) * 24, "m3/d"
    else:
        base, unit = sum(float(f.get("kg_h") or 0) for f in proc.values()) * 24 / 1000, "t/d"
    driven = [u["id"] for u, _, _ in _driven(w)]
    utils = []
    for sid, f in (spec.get("feeds") or {}).items():
        if not f.get("utility"):
            continue
        m = next((m for m in UTILITY_PRICES if m[0](f)), None)
        if m and f.get(m[4]) is not None:
            utils.append({"name": f"{m[1].capitalize()} ({sid})", "stream": sid, "field": m[4],
                          "price": {"value": m[2], "unit": m[3], "source": f"muse_default typical {m[1]} cost"}})
    return {"draft": True, "note": f"{DRAFT}: prices are typical values, not the site's. Product price must come from the engineer.",
            "currency": "USD",
            "throughput": {"name": "Process feed", "base": round(base, 2), "unit": unit,
                           "source": "sum of the non-utility feeds of the built model", "provenance": "documented"},
            "product": {"price": {"value": None, "unit": f"USD per {unit[:-2]}", "source": "engineer to supply", "provenance": "open"},
                        "variable_cost": {"value": 0, "unit": f"USD per {unit[:-2]}", "source": "muse_default"}},
            "drivers": [{"name": "Electric drives", "units": driven,
                         "price": {"value": 0.08, "unit": "USD per kWh", "source": "muse_default industrial power price"}}] if driven else [],
            "utilities": utils,
            "operating_days": {"value": 330, "source": "muse_default"},
            "outage": {"days": 2, "source": "muse_default shutdown for a tie-in or exchanger clean"},
            "discount_rate": {"value": 0.10, "source": "muse_default"}, "years": {"value": 10, "source": "muse_default"},
            "capex_correlations": {"source": "Towler & Sinnott, Chemical Engineering Design 2nd ed. (2012), Table 7.2; "
                                             "Lang factor Table 7.1 (fluids processing)", "items": TS, "cepci": CEPCI,
                                   "lang_factor": LANG_FLUID}}


def draft_uncertainty(w, prov=None):
    """Every assumed (muse_default) input becomes an uncertain input of kind 'assumed'; at most 8, operating inputs first."""
    prov = prov or provenance(w)
    order = {"units": 0, "feeds": 1, "limits": 2}
    picks = sorted((p for p, v in prov.items() if v["provenance"] == "muse_default" and v["value"]),
                   key=lambda p: (order[p.split(".")[0]], p))[:8]
    if not picks:
        return None
    return {"draft": True, "note": f"{DRAFT}: the inputs assumed while building (not found in the plant documents), each "
                                   "varied ±10 % (kind 'assumed').", "n": 32,
            "inputs": [{"path": p, "kind": "assumed", "provenance": "muse_default", "source": prov[p]["source"]} for p in picks]}


def draft_envelope(w, muse=False, model="muse-spark-1.3-contributor"):
    """Operating envelope around the target (prefeed.json 'scenarios'). Deterministic default: feed ±10 % around the
    target, a hot-day utility case (+5 C on cooling/chilled water) and fouled exchangers (U at 85 %). With muse=True one
    cheap Muse call proposes the scenarios instead (validated the same way)."""
    target = float(w.cfg.get("target_scale") or 1.0)
    feeds, units = w.spec.get("feeds") or {}, w.spec.get("units") or []
    hot = [{"path": f"feeds.{k}.T_C", "value": round(float(f["T_C"]) + 5, 2)} for k, f in feeds.items()
           if f.get("utility") and f.get("T_C") is not None and float(f["T_C"]) <= 45]
    foul = [{"path": f"units.{u['id']}.U_W_m2K", "value": round(float(u["U_W_m2K"]) * 0.85, 1)} for u in units if u.get("U_W_m2K")]
    sc = [{"name": "Target, feed +10 %", "scale": round(target * 1.1, 4), "basis": f"{DRAFT}: feed swing above the target"},
          {"name": "Target, feed -10 %", "scale": round(target * 0.9, 4), "basis": f"{DRAFT}: turndown below the target (minimum flows)"}]
    if hot:
        sc.append({"name": "Target, hot day (utility water +5 C)", "scale": target, "changes": hot, "basis": f"{DRAFT}: summer cooling water"})
    if foul:
        sc.append({"name": "Target, exchangers fouled (U at 85 %)", "scale": target, "changes": foul, "basis": f"{DRAFT}: fouling allowance"})
    src = "deterministic"
    if muse:
        from . import llm
        prompt = ("Propose 3 to 6 worst credible operating scenarios for checking a plant change. Reply only JSON: "
                  '{"scenarios":[{"name":str,"scale":number (throughput multiple),"changes":[{"path":str,"value":number}],"basis":str}]}. '
                  "Paths may only be feeds.<id>.T_C|P_bar or units.<id>.<numeric field> from this spec; never limits or new units. "
                  f"Target throughput multiple: {target}. Spec: " + json.dumps({"feeds": feeds, "units": units})[:6000])
        try:
            text = llm.chat(model, [{"role": "user", "content": prompt}], temperature=0)
            got = json.loads(re.search(r"\{.*\}", text, re.S).group(0))["scenarios"]
            ok = {f"feeds.{k}.{f_}" for k, f in feeds.items() for f_ in ("T_C", "P_bar")} | \
                 {f"units.{u['id']}.{k}" for u in units for k, v in u.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            got = [{"name": str(s["name"])[:80], "scale": float(s.get("scale") or target),
                    "changes": [c for c in s.get("changes") or [] if c.get("path") in ok and isinstance(c.get("value"), (int, float))],
                    "basis": f"{DRAFT}, proposed by Muse: {str(s.get('basis') or '')[:200]}"} for s in got[:6]]
            if got and len({s["name"] for s in got}) == len(got) and all(0 < s["scale"] < 3 for s in got):
                sc, src = got, f"Muse ({model})"
        except Exception as ex:  # noqa: BLE001 - the deterministic envelope stands
            src = f"deterministic (Muse proposal rejected: {type(ex).__name__})"
    return {"draft": True, "note": f"{DRAFT}: operating envelope, {src}; the engineer confirms or replaces it.",
            "provenance": "muse_default", "scenarios": sc}


BUILDERS = {"electrical.json": draft_electrical, "curves.json": draft_curves, "economics.json": draft_economics,
            "uncertainty.json": draft_uncertainty, "prefeed.json": draft_envelope}


def ensure(w, refresh=False):
    """Write a draft for every discipline file the case lacks (no model call). Returns {name: 'case'|'draft'|'none'}."""
    if not getattr(w, "built", None) or not w.spec:
        return {}
    d, out = _dir(w.name), {}
    for name, build in BUILDERS.items():
        if (ROOT / "cases" / w.name / name).exists():
            out[name] = "case"
            continue
        f = d / name
        if f.exists() and not refresh:
            out[name] = "draft"
            continue
        data = build(w)
        if data is None:
            out[name] = "none"
            continue
        d.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, indent=1))
        out[name] = "draft"
    prov = provenance(w)
    d.mkdir(parents=True, exist_ok=True)
    (d / "provenance.json").write_text(json.dumps(prov, indent=1))
    return out


if __name__ == "__main__":
    import sys
    from .plant import PlantWorkspace
    ws = PlantWorkspace(sys.argv[1])
    for n, b in BUILDERS.items():
        print(f"--- {n}", "(case file present)" if (ROOT / "cases" / ws.name / n).exists() else "")
        print(json.dumps(b(ws), indent=1)[:1800])
