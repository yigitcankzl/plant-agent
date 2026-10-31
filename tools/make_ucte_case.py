"""Write cases/ucte_2006: case.json, basis.md (pre-event data only), pid.svg (one-line diagram) and outcome.json (withheld).
python tools/make_ucte_case.py

Source: UCTE, Final Report - System Disturbance on 4 November 2006 (30 Jan 2007). The reduced network around Landesbergen is
a PlantAgent reconstruction: substation positions from public maps, straight-line distance x 1.1 routing factor, typical
380/220 kV per-km parameters. It is not TSO network data.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cases" / "ucte_2006"
REPORT = "UCTE Final Report, System Disturbance on 4 November 2006 (30 January 2007)"
URL = "https://eepublicdownloads.entsoe.eu/clean-documents/pre2015/publications/ce/otherreports/Final-Report-20070130.pdf"

# approximate substation positions (lat, lon) from public maps
XY = {"LAN": (52.556, 9.123), "WEH": (52.318, 8.300), "OVE": (52.430, 8.880), "DOL": (53.530, 9.580),
      "GRO": (52.035, 9.410), "BEC": (52.000, 8.630), "ELS": (51.730, 8.680), "TWI": (51.330, 8.980), "GUT": (51.900, 8.380)}
NAMES = {"LAN": "Landesbergen", "WEH": "Wehrendorf", "OVE": "Ovenstädt", "DOL": "Dollern", "GRO": "Grohnde",
         "BEC": "Bechterdissen", "ELS": "Elsen", "TWI": "Twistetal", "GUT": "Gütersloh"}


def km(a, b, f=1.1):
    (la1, lo1), (la2, lo2) = XY[a], XY[b]
    dy = (la2 - la1) * 111.2
    dx = (lo2 - lo1) * 111.2 * math.cos(math.radians((la1 + la2) / 2))
    return round(math.hypot(dx, dy) * f, 1)


# (id, from bus, to bus, length km, circuits, kV, owner/route note)
LINES = [
    ("LAN-WEH", "LAN_A", "WEH", km("LAN", "WEH"), 1, 380, "tie line E.ON Netz - RWE TSO"),
    ("LAN-OVE 1", "LAN_A", "OVE", km("LAN", "OVE"), 1, 380, "circuit on busbar A"),
    ("LAN-OVE 2", "LAN_B", "OVE", km("LAN", "OVE"), 1, 380, "circuit on busbar B"),
    ("LAN-DOL 1", "LAN_A", "DOL", km("LAN", "DOL"), 1, 380, "circuit on busbar A"),
    ("LAN-DOL 2", "LAN_B", "DOL", km("LAN", "DOL"), 1, 380, "circuit on busbar B"),
    ("LAN-GRO 1", "LAN_A", "GRO", km("LAN", "GRO"), 1, 380, "circuit on busbar A"),
    ("LAN-GRO 2", "LAN_B", "GRO", km("LAN", "GRO"), 1, 380, "circuit on busbar B"),
    ("OVE-BEC", "OVE", "BEC", km("OVE", "BEC"), 2, 380, "E.ON corridor south"),
    ("BEC-ELS", "BEC", "ELS", km("BEC", "ELS"), 2, 380, "E.ON corridor south"),
    ("ELS-TWI", "ELS", "TWI", km("ELS", "TWI"), 2, 380, "E.ON corridor south"),
    ("TWI-SOUTH_E", "TWI", "SOUTH_E", 100.0, 2, 380, "equivalent of the E.ON grid further south"),
    ("WEH-GUT", "WEH", "GUT", km("WEH", "GUT"), 2, 380, "RWE TSO"),
    ("GUT-SOUTH_W", "GUT", "SOUTH_W", 100.0, 2, 380, "equivalent of the RWE grid further south-west"),
    ("BIO-SPX 220", "BIO220", "SPX220", 20.0, 1, 220, "220 kV Bielefeld/Ost - Spexard, parallel to the tie"),
]
TRAFOS = [("LAN TA", "LAN_A", "LAN220"), ("LAN TB", "LAN_B", "LAN220"), ("BEC T", "BEC", "BIO220"), ("GUT T", "GUT", "SPX220")]
P380 = {"r": 0.03, "x": 0.26, "c": 13.0, "i": 2.0}
P220 = {"r": 0.08, "x": 0.32, "c": 11.0, "i": 1.0}


def basis():
    rows = "\n".join(f"| {lid} | {f} | {t} | {L:g} | {n} | {kv} | {note} |" for lid, f, t, L, n, kv, note in LINES)
    trafos = "\n".join(f"| {tid} | {hv} | {lv} |" for tid, hv, lv in TRAFOS)
    return f"""# 4 November 2006, Landesbergen area (E.ON Netz / RWE TSO), 380/220 kV: data sheet

Source of the event data: {REPORT}, {URL}. Page numbers are the report's PDF pages. The reduced network below is a
PlantAgent reconstruction (RECONSTRUCTED): substation positions from public maps, line length = straight-line distance x 1.1,
typical per-km parameters. The report gives no impedances. Anything not from the report is marked RECONSTRUCTED.

## Situation at 22:00

- At 21:38 and 21:39 E.ON Netz switched off both circuits of the 380 kV line Conneforde - Diele (at the request of the Meyer Werft shipyard,
  for the ship "Norwegian Pearl" to pass down the river Ems; report p.18). The flow on the 380 kV tie line Landesbergen - Wehrendorf rose by over 600 MW to about
  1,200 MW (report p.19-20, Fig. 3).
- The 380 kV Landesbergen substation is operated with two separated busbars (A and B), its normal configuration, to keep
  the short-circuit current within the switchgear rating (report p.15). The bus coupler is open.
- The 380 kV Borken substation is split in two parts for construction work (report p.15). Not in the reduced model.
- Flows at the Landesbergen substation at 22:00, busbar by busbar (report p.50, Fig. 30), MW, sign = into the busbar:

| Busbar | Element | Flow at 22:00 (MW) |
|---|---|---|
| A | LAN-DOL 1 (from Dollern) | +843 |
| A | LAN TA (from the 220 kV side) | +219 |
| A | LAN-GRO 1 (from Grohnde) | +394 |
| A | LAN-WEH (to Wehrendorf) | -1,225 |
| A | LAN-OVE 1 (to Ovenstädt) | -233 |
| B | LAN-DOL 2 (from Dollern) | +721 |
| B | LAN TB (from the 220 kV side) | +196 |
| B | LAN-GRO 2 (from Grohnde) | +113 |
| B | LAN-OVE 2 (to Ovenstädt) | -1,032 |

- Between 22:02 and 22:09 the flow on Landesbergen - Wehrendorf rose gradually by about 130 MW, to about 1,375 MW just
  before 22:10 (report p.20 Fig. 3 and p.49: German-Dutch exchange variation and three units in the E.ON Netz grid).
  Between 22:05 and 22:07 the current exceeded RWE TSO's 1,795 A warning value (report p.19).

## Protection settings on Landesbergen - Wehrendorf (report p.19, Table 1)

| | E.ON Netz end (Landesbergen) | RWE TSO end (Wehrendorf) |
|---|---|---|
| Thermal capacity | 2,000 A | 2,000 A |
| Warning (alarm) | 1,000 A and 2,000 A | 1,795 A |
| Maximum accepted | 2,550 A for at most 1 h | 1,995 A |
| Tripping current | 3,000 A | 2,100 A |

The line trips at the lower of the two ends' tripping currents. The 220 kV line Bielefeld/Ost - Spexard is electrically
interdependent with it: if the 380 kV tie trips, the 220 kV line cannot carry the load (report p.49 footnote 16).

## Reduced network (RECONSTRUCTED)

Buses: LAN_A and LAN_B (Landesbergen 380 kV busbars A and B), bus coupler `LAN coupler` between them (open at 22:00);
WEH, OVE, DOL, GRO, BEC, ELS, TWI, GUT (380 kV, {', '.join(f'{k} = {v}' for k, v in NAMES.items() if k != 'LAN')});
LAN220, BIO220 (Bielefeld/Ost), SPX220 (Spexard) at 220 kV; SOUTH_E (E.ON grid further south) and SOUTH_W (RWE grid
further south-west) are grid equivalents.

Lines (380 kV per circuit: r {P380['r']} ohm/km, x {P380['x']} ohm/km, c {P380['c']:g} nF/km, thermal {P380['i'] * 1000:g} A;
220 kV: r {P220['r']}, x {P220['x']}, c {P220['c']:g}, thermal {P220['i'] * 1000:g} A; typical quad/twin-bundle values, RECONSTRUCTED):

| id | from | to | length km | circuits | kV | note |
|---|---|---|---|---|---|---|
{rows}

Transformers 380/220 kV, 600 MVA, uk 12 %, ukr 0.3 % (RECONSTRUCTED):

| id | 380 kV bus | 220 kV bus |
|---|---|---|
{trafos}

Injections at 22:00 (report Fig. 30 totals): north through Dollern 1,564 MW (gen at DOL), Grohnde 507 MW (gen at GRO),
Landesbergen 220 kV side 415 MW (gen at LAN220); generator voltage set points 1.05 pu (about 400 kV, RECONSTRUCTED).
Grid equivalents SOUTH_E (reference, 1.05 pu, 0 degrees) and SOUTH_W (1.05 pu). UNKNOWN: the voltage angle of SOUTH_W
relative to SOUTH_E, which stands for the north-east to south-west transit through both control areas. It is the one
quantity to calibrate: the Landesbergen - Wehrendorf flow at 22:00 is 1,225 MW. The flow just before 22:10 (about
1,375 MW) is reached with a larger transit (scale or angle).

## Operating request at 22:08

RWE TSO asked E.ON Netz for urgent intervention to bring the Landesbergen - Wehrendorf current back to a safe value
(report p.19). E.ON Netz dispatchers propose to couple the two busbars in Landesbergen (close `LAN coupler`). They expect
the current on Landesbergen - Wehrendorf to fall by about 80 A (report p.19). No load-flow calculation has been made.
"""


def case_json():
    return {
        "kind": "process", "engine": "pandapower",
        "title": "European grid, 4 November 2006: Landesbergen busbar coupling (UCTE incident)",
        "source": f"{REPORT}; reduced 380/220 kV network reconstructed by PlantAgent from public maps (not TSO data)",
        "url": URL, "svg": "pid.svg", "basis": "basis.md", "task_type": "incident reconstruction",
        "question": "Dispatchers plan to couple the busbars at Landesbergen to relieve the Landesbergen-Wehrendorf line. "
                    "Will it relieve the line, and is the grid N-1 secure afterwards?",
        "target_scale": 1.0,
        "throughput": {"name": "Transit (Landesbergen-Wehrendorf at 22:00 = 1,225 MW)", "base": 1225, "unit": "MW"},
        "data_note": "Event data from the UCTE Final Report (2007). The 380/220 kV network around Landesbergen is a PlantAgent "
                     "reconstruction from public maps with typical line parameters, not TSO data. The investigators' "
                     "conclusion is withheld from the agent.",
        "benchmark": False,
    }


def outcome():
    return {
        "engineers": "The UCTE investigation found that coupling the Landesbergen busbars had the opposite effect to what the "
                     "dispatchers expected: instead of falling by about 80 A, the current on Landesbergen-Wehrendorf rose by "
                     "about 67 A (about 50 MW) and the line was tripped by the distance protection at Wehrendorf, starting a "
                     "cascade that split the UCTE grid into three areas and cut supply to more than 15 million households. "
                     "The grid had not been N-1 secure since Conneforde-Diele was switched off: an outage of Bechterdissen-"
                     "Elsen or Elsen-Twistetal would have pushed the tie above the 2,100 A trip setting.",
        "source": f"{REPORT}, p.19 (coupling effect, +67 A), p.48 (N-1 violation), p.50-51 (Fig. 30/31), p.5 (impact)",
        "file": "outcome.json",
        "note": "Withheld from the agent: basis.md stops at the 22:08 request; the investigators' simulation and conclusion "
                "are only in this file.",
    }


def svg():
    W, H = 430, 300

    def xy(lat, lon):
        return 30 + (lon - 7.9) / (9.9 - 7.9) * (W - 70), -270 + (53.75 - lat) / (53.75 - 51.15) * (H - 60)
    P = {k: xy(*v) for k, v in XY.items()}
    P["SOUTH_E"] = xy(51.2, 9.35)
    P["SOUTH_W"] = xy(51.35, 8.05)
    P["LAN220"] = (P["LAN"][0] + 26, P["LAN"][1] - 4)
    P["BIO220"] = (P["BEC"][0] - 22, P["BEC"][1] + 6)
    P["SPX220"] = (P["GUT"][0] + 4, P["GUT"][1] + 12)
    lan_a, lan_b = (P["LAN"][0] - 7, P["LAN"][1]), (P["LAN"][0] + 7, P["LAN"][1])
    end = {"LAN_A": lan_a, "LAN_B": lan_b, **P}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="-5 -{H - 5} {W} {H}" font-family="Arial,sans-serif">',
           f'<rect x="-5" y="-{H - 5}" width="{W}" height="{H}" fill="#fcfbf7"/>',
           f'<rect x="1" y="-{H - 9}" width="{W - 12}" height="{H - 14}" fill="none" stroke="#294248" stroke-width="0.7"/>',
           '<text x="8" y="-281" fill="#294248" font-size="4.4" font-weight="700">European grid, 4 Nov 2006: Landesbergen area 380/220 kV</text>',
           '<text x="8" y="-276" fill="#647a7b" font-size="2.7">One-line diagram · reduced network reconstructed by PlantAgent from public maps · positions approximate</text>']
    # Conneforde - Diele: context only, switched off at 21:38/21:39, not in the model
    con, die = xy(53.33, 8.03), xy(53.12, 7.32 + 0.6)
    out.append(f'<g><polyline points="{con[0]:.1f},{con[1]:.1f} {die[0]:.1f},{die[1]:.1f}" fill="none" stroke="#9aa5a6" stroke-width="0.9" stroke-dasharray="2,1.5"/>'
               f'<text x="{die[0]:.1f}" y="{die[1] - 3:.1f}" fill="#9aa5a6" font-size="2.6">Conneforde-Diele 380 kV, switched off 21:38/21:39</text></g>')
    for lid, f, t, L, n, kv, note in LINES:
        (x1, y1), (x2, y2) = end[f], end[t]
        col = "#c0392b" if lid == "LAN-WEH" else ("#2b6cb3" if kv == 380 else "#1f8a5b")
        sw = 1.4 if n == 2 else 0.9
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        off = {"LAN-OVE 1": -3, "LAN-OVE 2": 3, "LAN-DOL 1": -3, "LAN-DOL 2": 3, "LAN-GRO 1": -3, "LAN-GRO 2": 3}.get(lid, 0)
        out.append(f'<g data-tag="{lid}" data-name="{lid} {kv} kV, {L:g} km{" x2 circuits" if n == 2 else ""} ({note})">'
                   f'<polyline points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{col}" stroke-width="{sw}"/>'
                   f'<text x="{mx + 1.5:.1f}" y="{my + off:.1f}" fill="{col}" font-size="2.4" font-weight="700">{lid}</text></g>')
    for tid, hv, lv in TRAFOS:
        (x1, y1), (x2, y2) = end[hv], end[lv]
        out.append(f'<g data-tag="{tid}" data-name="{tid} 380/220 kV transformer"><polyline points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f}" '
                   f'fill="none" stroke="#1f8a5b" stroke-width="0.7"/><circle cx="{(x1 + x2) / 2 - 1:.1f}" cy="{(y1 + y2) / 2:.1f}" r="1.6" '
                   f'fill="#fff" stroke="#1f8a5b" stroke-width="0.5"/><circle cx="{(x1 + x2) / 2 + 1:.1f}" cy="{(y1 + y2) / 2:.1f}" r="1.6" '
                   f'fill="none" stroke="#1f8a5b" stroke-width="0.5"/></g>')
    for k, (x, y) in P.items():
        if k == "LAN":
            continue
        name = NAMES.get(k) or {"SOUTH_E": "E.ON grid south (equivalent)", "SOUTH_W": "RWE grid south-west (equivalent)",
                                "LAN220": "Landesbergen 220 kV", "BIO220": "Bielefeld/Ost 220 kV", "SPX220": "Spexard 220 kV"}[k]
        out.append(f'<g data-tag="{k}" data-name="{name}" fill="#fff" stroke="#294248" stroke-width="0.7">'
                   f'<rect x="{x - 4:.1f}" y="{y - 1.6:.1f}" width="8" height="3.2"/>'
                   f'<text x="{x + 5:.1f}" y="{y + 1:.1f}" fill="#294248" stroke="none" font-size="2.8" font-weight="700">{name}</text></g>')
    x, y = P["LAN"]
    out.append(f'<rect x="{x - 13:.1f}" y="{y - 6:.1f}" width="26" height="12" fill="none" stroke="#294248" stroke-width="0.5" stroke-dasharray="1.5,1"/>'
               f'<text x="{x - 13:.1f}" y="{y - 7.5:.1f}" fill="#294248" font-size="3.2" font-weight="700">Landesbergen 380 kV</text>')
    for bid, (bx, by) in (("LAN_A", lan_a), ("LAN_B", lan_b)):
        out.append(f'<g data-tag="{bid}" data-name="Landesbergen busbar {bid[-1]}" stroke="#294248">'
                   f'<line x1="{bx - 5:.1f}" y1="{by:.1f}" x2="{bx + 5:.1f}" y2="{by:.1f}" stroke-width="1.6"/>'
                   f'<text x="{bx - 5:.1f}" y="{by + 4:.1f}" fill="#294248" stroke="none" font-size="2.4">busbar {bid[-1]}</text></g>')
    out.append(f'<g data-tag="LAN coupler" data-name="Landesbergen bus coupler (open at 22:00)">'
               f'<rect x="{x - 1.6:.1f}" y="{y - 1.6:.1f}" width="3.2" height="3.2" fill="#fff" stroke="#c0392b" stroke-width="0.6"/>'
               f'<line x1="{x - 1.2:.1f}" y1="{y + 1.2:.1f}" x2="{x + 1.2:.1f}" y2="{y - 1.2:.1f}" stroke="#c0392b" stroke-width="0.5"/></g>')
    out.append(f'<text x="{W - 150}" y="-14" fill="#647a7b" font-size="2.4">thick line: two circuits · red: tie line LAN-WEH (protection 2,100 A at Wehrendorf)</text>')
    out.append("</svg>")
    return "\n".join(out)


def reference_spec(angle_deg=-3.5, coupler=False):
    """The data sheet as a grid spec (what a correct build reproduces); the SOUTH_W angle is the calibrated unknown."""
    buses = [{"id": b, "vn_kv": 380} for b in ("LAN_A", "LAN_B", "WEH", "OVE", "DOL", "GRO", "BEC", "ELS", "TWI", "GUT", "SOUTH_E", "SOUTH_W")]
    buses += [{"id": b, "vn_kv": 220} for b in ("LAN220", "BIO220", "SPX220")]
    keys = (("r_ohm_per_km", "r"), ("x_ohm_per_km", "x"), ("c_nf_per_km", "c"), ("max_i_ka", "i"))
    lines = [{"id": lid, "from": f, "to": t, "length_km": L, "parallel": n, **{k: (P380 if kv == 380 else P220)[s] for k, s in keys}}
             for lid, f, t, L, n, kv, _ in LINES]
    trafos = [{"id": tid, "hv": hv, "lv": lv, "sn_mva": 600, "vn_hv_kv": 380, "vn_lv_kv": 220, "vk_percent": 12, "vkr_percent": 0.3}
              for tid, hv, lv in TRAFOS]
    return {"grid": True, "buses": buses, "lines": lines, "trafos": trafos,
            "switches": [{"id": "LAN coupler", "bus_a": "LAN_A", "bus_b": "LAN_B", "closed": coupler}],
            "gens": [{"id": "North via Dollern", "bus": "DOL", "p_mw": 1564, "vm_pu": 1.05},
                     {"id": "Grohnde", "bus": "GRO", "p_mw": 507, "vm_pu": 1.05},
                     {"id": "Landesbergen 220 kV", "bus": "LAN220", "p_mw": 415, "vm_pu": 1.05}],
            "ext_grids": [{"id": "E.ON south", "bus": "SOUTH_E", "vm_pu": 1.05, "va_degree": 0},
                          {"id": "RWE grid", "bus": "SOUTH_W", "vm_pu": 1.05, "va_degree": angle_deg}],
            "limits": {"LAN-WEH": {"max_A": 2100, "where": "distance protection trip at Wehrendorf (RWE TSO)",
                                   "source": "UCTE report p.19 Table 1"}}}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "case.json").write_text(json.dumps(case_json(), indent=2) + "\n")
    (OUT / "basis.md").write_text(basis())
    (OUT / "pid.svg").write_text(svg())
    (OUT / "outcome.json").write_text(json.dumps(outcome(), indent=2) + "\n")
    leak = [w for w in ("67 A", "+67", "1,274", "1274", "opposite effect", "Fig. 31", "tripped by") if w in basis()]
    assert not leak, f"basis.md leaks the outcome: {leak}"
    print("written", OUT)
