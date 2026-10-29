"""Draw the MVR salt-crystallisation P&ID (demonstration) as a DEXPI-style Proteus XML subset plus a matching SVG.

The topology and operating points follow US Patent 5,366,514 (Texas Brine, 1994) FIG. I and Table I; tags, line numbers,
valves and relief set pressures are ours (the patent shows no instrumentation). No public P&ID of such a plant exists.
python tools/make_salt_pid.py   ->   case-data/drawn/salt_mvr_pid.xml and cases/salt_mvr/pid.svg
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/home/kizil/Desktop/hackathon/case-data")

# tag: (DEXPI class, x, y (y up, sheet 0..297), shape, design data {name: (value, units)}, nozzles)
EQ = {
    "P-101": ("CentrifugalPump", 30, 150, "pump", {"DesignVolumeFlowRate": (300, "MetreCubedPerHour")}, ["N1", "N2"]),
    "E-101": ("TubularHeatExchanger", 75, 150, "hx", {"DesignHeatFlowRate": (13000, "Kilowatt")}, ["N1", "N2", "N3", "N4"]),
    "E-102": ("PlateHeatExchanger", 125, 150, "hx", {"DesignHeatFlowRate": (16000, "Kilowatt")}, ["N1", "N2", "N3", "N4"]),
    "V-201": ("Vessel", 190, 175, "vessel", {"DesignPressure": (3.5, "BarGauge"), "NominalCapacity(Volume)": (450, "MetreCubed")},
              ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]),
    "P-201": ("CentrifugalPump", 175, 95, "pump", {"DesignVolumeFlowRate": (12000, "MetreCubedPerHour")}, ["N1", "N2"]),
    "E-201": ("TubularHeatExchanger", 245, 130, "hx", {"DesignHeatTransferArea": (6500, "MetreSquared")}, ["N1", "N2", "N3", "N4"]),
    "K-201": ("CentrifugalCompressor", 265, 235, "comp", {"DesignPressureRatio": (1.8, ""), "DesignShaftPower": (14000, "Kilowatt")}, ["N1", "N2"]),
    "D-201": ("Desuperheater", 315, 200, "drum", {}, ["N1", "N2", "N3"]),
    "V-301": ("Vessel", 345, 120, "vessel", {"DesignPressure": (1.0, "BarGauge"), "NominalCapacity(Volume)": (120, "MetreCubed")},
              ["N1", "N2", "N3", "N4", "N5", "N6", "N7"]),
    "E-301": ("TubularHeatExchanger", 390, 95, "hx", {"DesignHeatTransferArea": (1500, "MetreSquared")}, ["N1", "N2", "N3", "N4"]),
    "T-401": ("Tank", 230, 35, "tank", {"NominalCapacity(Volume)": (300, "MetreCubed")}, ["N1", "N2", "N3", "N4"]),
}
NAMES = {"P-101": "Feed brine pump", "E-101": "Brine-cooled condenser", "E-102": "Brine preheater", "V-201": "VRC evaporator / crystalliser",
         "P-201": "Forced-circulation pump", "E-201": "Circulating heater CH1", "K-201": "Vapour recompressor (MVR)", "D-201": "Desuperheater",
         "V-301": "Purge evaporator", "E-301": "Circulating heater CH2", "T-401": "Condensate tank"}
# (line, fluid, from (tag, nozzle) or None for an open end, to, [inline (class, number, extra attrs)])
LINES = [
    ("1001", "BR", None, ("P-101", "N1"), []),
    ("1002", "BR", ("P-101", "N2"), ("E-101", "N1"), [("GateValve", "C1", {})]),
    ("1003", "BR", ("E-101", "N2"), ("E-102", "N1"), []),
    ("1004", "BR", ("E-102", "N2"), ("V-201", "N1"), [("GlobeValve", "LV-201", {})]),
    ("2001", "SL", ("V-201", "N3"), ("P-201", "N1"), []),
    ("2002", "SL", ("P-201", "N2"), ("E-201", "N1"), []),
    ("2003", "SL", ("E-201", "N2"), ("V-201", "N4"), []),
    ("3001", "ST", ("V-201", "N5"), ("K-201", "N1"), [("ButterflyValve", "C1", {})]),
    ("3002", "ST", ("K-201", "N2"), ("D-201", "N1"), []),
    ("3003", "STa", ("D-201", "N2"), ("E-201", "N3"), [("GateValve", "C1", {})]),
    ("4001", "STb", ("E-201", "N4"), ("E-102", "N3"), []),
    ("4002", "STc", ("E-102", "N4"), ("T-401", "N1"), []),
    ("5001", "PG", ("V-201", "N6"), ("V-301", "N1"), [("GlobeValve", "FV-301", {})]),
    ("3101", "STa", ("V-201", "N7"), ("E-301", "N3"), [("GateValve", "C1", {})]),
    ("4101", "STb", ("E-301", "N4"), ("T-401", "N2"), []),
    ("2101", "SL", ("V-301", "N3"), ("E-301", "N1"), []),
    ("2102", "SL", ("E-301", "N2"), ("V-301", "N4"), []),
    ("3201", "STa", ("V-301", "N5"), ("E-101", "N3"), []),
    ("4201", "STb", ("E-101", "N4"), ("T-401", "N3"), []),
    ("6001", "SL", ("V-201", "N2"), None, [("GateValve", "C1", {})]),
    ("5101", "PG", ("V-301", "N6"), None, [("GateValve", "C1", {})]),
    ("4301", "CD", ("T-401", "N4"), None, []),
    ("7001", "ST", ("V-201", "N8"), None, [("SpringLoadedGlobeSafetyValve", "PSV-201", {"SetPressureHigh": (3.5, "Bar")})]),
    ("7002", "ST", ("D-201", "N3"), None, [("SpringLoadedGlobeSafetyValve", "PSV-202", {"SetPressureHigh": (4.5, "Bar")})]),
    ("7003", "ST", ("V-301", "N7"), None, [("SpringLoadedGlobeSafetyValve", "PSV-301", {"SetPressureHigh": (1.0, "Bar")})]),
]
# lower-case suffixes (STa steam in, STb/STc its condensate) keep one exchanger side in one fluid family for the relief scan
FLUID = {"BR": ("brine", "#2b6cb3"), "SL": ("slurry", "#7a4fb3"), "ST": ("steam", "#c0392b"), "CD": ("condensate", "#1f8a5b"), "PG": ("purge liquor", "#b07a12")}


def ga(name, value, units=None):
    if isinstance(value, (int, float)):
        return f'<GenericAttribute Name="{name}" Value="{value}" Format="double"' + (f' Units="{units}"' if units else "") + "/>"
    return f'<GenericAttribute Name="{name}" Value="{escape(str(value))}" Format="string"/>'


def xml():
    out = ['<?xml version="1.0" encoding="utf-8"?>', '<PlantModel>',
           '<PlantInformation SchemaVersion="4.1.1" OriginatingSystem="PlantAgent tools/make_salt_pid.py" '
           'Discipline="PID" Units="mm"/>']
    for tag, (cls, x, y, _, design, nozzles) in EQ.items():
        out.append(f'<Equipment ID="{tag}" ComponentClass="{cls}"><Position><Location X="{x}" Y="{y}" Z="0"/></Position>'
                   f'<GenericAttributes Set="DexpiAttributes">{ga("TagNameAssignmentClass", tag)}'
                   + "".join(ga(k, v, u) for k, (v, u) in design.items()) + "</GenericAttributes>"
                   + "".join(f'<Nozzle ID="{tag}-{n}" ComponentClass="Nozzle"><GenericAttributes>{ga("SubTagNameAssignmentClass", n)}'
                             f'</GenericAttributes></Nozzle>' for n in nozzles) + "</Equipment>")
    for line, fluid, frm, to, inline in LINES:
        comps = "".join(f'<PipingComponent ID="{line}-{num}" ComponentClass="{cls}"><GenericAttributes>{ga("PipingComponentNumberAssignmentClass", num)}'
                        + "".join(ga(k, v, u) for k, (v, u) in extra.items()) + "</GenericAttributes></PipingComponent>"
                        for cls, num, extra in inline)
        conn = "<Connection" + (f' FromID="{frm[0]}-{frm[1]}"' if frm else "") + (f' ToID="{to[0]}-{to[1]}"' if to else "") + "/>"
        out.append(f'<PipingNetworkSystem ID="L{line}" ComponentClass="PipingNetworkSystem"><GenericAttributes>'
                   f'{ga("LineNumberAssignmentClass", line)}{ga("FluidCodeAssignmentClass", fluid)}</GenericAttributes>'
                   f'<PipingNetworkSegment ID="S{line}" ComponentClass="PipingNetworkSegment">{comps}{conn}</PipingNetworkSegment></PipingNetworkSystem>')
    out.append("</PlantModel>")
    return "\n".join(out)


def svg():
    """Only the drawing changes: XML equipment centres, topology and nozzle IDs stay fixed."""
    pos = {tag: (e[1], -e[2]) for tag, e in EQ.items()}
    # Realistic entry/exit sides, keyed by the unchanged DEXPI nozzle IDs.
    ports = {
        "P-101": [(-6, 0), (6, 0)], "P-201": [(-6, 0), (6, 0)],
        "E-101": [(-10, 0), (10, 0), (0, -6), (0, 6)],
        "E-102": [(-10, 0), (10, 0), (0, -6), (0, 6)],
        "E-201": [(-10, 0), (10, 0), (0, -6), (0, 6)],
        "E-301": [(-10, 0), (10, 0), (0, -6), (0, 6)],
        "V-201": [(-9, -7), (-9, 8), (-2, 16), (9, 10), (0, -16), (9, 0), (9, -9), (6, -16)],
        "V-301": [(-9, -7), (-9, 8), (-3, 16), (9, 1), (0, -16), (5, 16), (7, -16)],
        "K-201": [(-8, 0), (8, 0)], "D-201": [(0, -6), (6, 0), (3, -6)],
        "T-401": [(-12, -2), (0, -8), (-12, 2), (0, 8)],
    }
    nozzle = {(tag, n): (pos[tag][0] + dx, pos[tag][1] + dy)
              for tag, e in EQ.items() for n, (dx, dy) in zip(e[5], ports[tag])}
    open_end = {"1001": (10, -150), "6001": (145, -75), "5101": (333, -63), "4301": (230, -8),
                "7001": (215, -275), "7002": (318, -270), "7003": (377, -245)}
    route = {
        "1001": [], "1002": [], "1003": [], "1004": [(158, -150), (158, -182)],
        "2001": [(188, -95)], "2002": [(220, -95), (220, -130)], "2003": [(272, -130), (272, -165)],
        "3001": [(190, -215), (257, -215)], "3002": [(315, -235)],
        "3003": [(330, -200), (330, -143), (245, -143)],
        "4001": [(245, -115), (105, -115), (105, -156)],
        "4002": [(150, -144), (150, -48), (218, -48)],
        "5001": [(304, -175), (304, -127)],
        "3101": [(366, -184), (366, -110), (390, -110)],
        "4101": [(405, -89), (405, -57), (230, -57)],
        "2101": [(342, -95)], "2102": [(413, -95), (413, -119)],
        "3201": [(345, -220), (55, -220), (55, -156)],
        "4201": [(50, -144), (50, -20), (218, -20)],
        "6001": [(145, -167)], "5101": [(333, -104)], "4301": [],
        "7001": [(215, -191)], "7002": [], "7003": [(377, -136)],
    }
    label = {"1001": (10, -155), "1002": (43, -154), "1003": (95, -154), "1004": (137, -154),
             "2001": (192, -109), "2002": (194, -99), "2003": (249, -169),
             "3001": (220, -219), "3002": (283, -239), "3003": (299, -147),
             "4001": (162, -119), "4002": (153, -79), "5001": (240, -179),
             "3101": (269, -188), "4101": (307, -61), "2101": (357, -99),
             "2102": (391, -123), "3201": (178, -224), "4201": (104, -24),
             "6001": (147, -67), "5101": (335, -68), "4301": (232, -10),
             "7001": (217, -258), "7002": (320, -255), "7003": (379, -230)}
    valve_at = {"1002": (51, -150), "1004": (158, -167), "3001": (235, -215),
                "3003": (282, -143), "5001": (272, -175), "3101": (315, -184),
                "6001": (145, -151), "5101": (333, -86),
                "7001": (215, -245), "7002": (318, -246), "7003": (377, -215)}
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="429" height="306" viewBox="-5 -301 429 306" font-family="Arial,sans-serif">',
         '<rect x="-5" y="-301" width="429" height="306" fill="#fcfbf7"/>',
         '<rect x="1" y="-296" width="418" height="295" fill="none" stroke="#294248" stroke-width="0.7"/>',
         '<defs>' + ''.join(f'<marker id="arr-{k}" markerWidth="5" markerHeight="5" refX="4.5" refY="2.5" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L5,2.5 0,5 Z" fill="{v[1]}"/></marker>' for k, v in FLUID.items()) + '</defs>',
         '<text x="8" y="-286" fill="#294248" font-size="4.4" font-weight="700">MVR salt crystallisation</text>',
         '<text x="8" y="-281" fill="#647a7b" font-size="2.7">Process and instrumentation drawing · illustrative equipment ratings</text>']
    for line, fluid, frm, to, inline in LINES:
        a = nozzle[frm] if frm else open_end[line]
        b = nozzle[to] if to else open_end[line]
        points = [a, *route[line], b]
        assert all(x1 == x2 or y1 == y2 for (x1, y1), (x2, y2) in zip(points, points[1:])), line
        family = "ST" if fluid.startswith("ST") else fluid
        colour = FLUID[family][1]
        xy = " ".join(f"{x},{y}" for x, y in points)
        from_tag, to_tag = frm[0] if frm else "", to[0] if to else ""
        s.append(f'<g data-line="{line}" data-from="{from_tag}" data-to="{to_tag}">'
                 f'<polyline points="{xy}" fill="none" stroke="{colour}" stroke-width="0.9" stroke-linejoin="round" marker-end="url(#arr-{family})"/>')
        x, y = label[line]
        title = f"{line}-{fluid}"
        s.append(f'<rect x="{x - 1}" y="{y - 2.8}" width="{len(title) * 1.55 + 2}" height="3.7" fill="#fcfbf7"/>'
                 f'<text x="{x}" y="{y}" font-size="2.5" font-weight="700" fill="{colour}">{title}</text>')
        for cls, num, extra in inline:
            vx, vy = valve_at[line]
            vertical = any(x1 == x2 == vx and min(y1, y2) <= vy <= max(y1, y2) for (x1, y1), (x2, y2) in zip(points, points[1:]))
            if "Safety" in cls:
                s.append(f'<g transform="translate({vx},{vy})"><path d="M-2,2 L2,2 L0,-1 Z M0,-1 V-4 M-2,-4 L2,-4 M-2,-6 L2,-6 M-2,-8 L2,-8" fill="#fff" stroke="#a92525" stroke-width="0.6"/>'
                         f'<text x="3" y="-4" font-size="2.6" font-weight="700" fill="#a92525">{num}</text>'
                         f'<text x="3" y="-1" font-size="2.2" fill="#a92525">{extra["SetPressureHigh"][0]} barg</text></g>')
            else:
                rotate = 90 if vertical else 0
                s.append(f'<g transform="translate({vx},{vy})"><g transform="rotate({rotate})">'
                         '<path d="M-3,-2 L0,0 L-3,2 Z M3,-2 L0,0 L3,2 Z" fill="#fff" stroke="#294248" stroke-width="0.6"/>'
                         + ('<path d="M0,-2 V-5" stroke="#294248" stroke-width="0.5"/><circle cx="0" cy="-7" r="2" fill="#fff" stroke="#294248" stroke-width="0.5"/>' if num.startswith(("LV", "FV")) else '')
                         + f'</g>{f"<text x=\"4\" y=\"-4\" font-size=\"2.6\" font-weight=\"700\" fill=\"#294248\">{num}</text>" if num.startswith(("LV", "FV")) else ""}</g>')
        s.append('</g>')
    for tag, (_, x, y_up, shape, _, _) in EQ.items():
        x, y = pos[tag]
        g = [f'<g data-tag="{tag}" data-pid="{tag}" data-name="{escape(NAMES[tag])}" fill="#fff" stroke="#294248" stroke-width="0.7">']
        if shape == "vessel":
            g.append(f'<rect x="{x - 9}" y="{y - 16}" width="18" height="32" rx="7"/>'
                     f'<path d="M{x-7},{y+5} H{x+7} M{x-4},{y+16} L{x-2},{y+23} H{x+2} L{x+4},{y+16}" fill="none" stroke-width="0.5"/>')
            if tag == "V-201":
                g.append(f'<path d="M{x-4},{y+23} V{y+29} M{x+4},{y+23} V{y+29} M{x-4},{y+29} H{x+4}" fill="none" stroke-width="0.5"/>')
        elif shape == "tank":
            g.append(f'<path d="M{x-12},{y-8} V{y+8} H{x+12} V{y-8} M{x-12},{y-8} H{x+12} M{x-10},{y+2} H{x+10}" fill="none"/>')
        elif shape == "hx" and tag == "E-102":
            g.append(f'<rect x="{x-10}" y="{y-6}" width="20" height="12" rx="1"/>')
            g.extend(f'<path d="M{x+i},{y-5} L{x+i+4},{y+5}" fill="none" stroke-width="0.45"/>' for i in (-7, -2, 3))
        elif shape == "hx":
            g.append(f'<rect x="{x-10}" y="{y-6}" width="20" height="12" rx="5"/>'
                     f'<path d="M{x-9},{y-2} H{x+9} M{x-9},{y+2} H{x+9} M{x-3},{y-5} V{y+5} M{x+4},{y-5} V{y+5}" fill="none" stroke-width="0.4"/>')
        elif shape == "pump":
            g.append(f'<circle cx="{x}" cy="{y}" r="6"/><path d="M{x-3},{y-3} L{x+4},{y} L{x-3},{y+3} Z" fill="#dbe9e7"/>'
                     f'<path d="M{x-2},{y+6} V{y+9} H{x+8}" fill="none" stroke-width="0.5"/>')
        elif shape == "comp":
            g.append(f'<path d="M{x-8},{y-7} L{x+8},{y-4} V{y+4} L{x-8},{y+7} Z"/>'
                     f'<circle cx="{x-1}" cy="{y}" r="2" fill="none" stroke-width="0.45"/>'
                     f'<path d="M{x-1},{y-2} L{x+4},{y-4} M{x-1},{y+2} L{x+4},{y+4}" fill="none" stroke-width="0.45"/>')
        else:
            g.append(f'<rect x="{x-6}" y="{y-6}" width="12" height="12" rx="2"/>'
                     f'<path d="M{x-4},{y+3} L{x+4},{y-3}" fill="none" stroke-width="0.5"/>')
        label_y = y - (20 if shape == "vessel" else 12)
        g.append(f'<text x="{x-10}" y="{label_y}" font-size="3.2" font-weight="700" stroke="none" fill="#17383d">{tag}</text>'
                 f'<text x="{x-10}" y="{label_y+3.5}" font-size="2.4" stroke="none" fill="#526b6c">{escape(NAMES[tag])}</text></g>')
        s.append(''.join(g))
    s.append('<g fill="#17383d"><rect x="250" y="-31" width="166" height="27" fill="#fff" stroke="#294248" stroke-width="0.6"/>'
             '<path d="M250,-23 H416 M250,-13 H416 M310,-13 V-4" fill="none" stroke="#294248" stroke-width="0.4"/>'
             '<text x="254" y="-26" font-size="3.5" font-weight="700">MVR salt evaporation and crystallisation</text>'
             '<text x="254" y="-19" font-size="2.4">Based on US Patent 5,366,514, FIG. I / Table I (Texas Brine, 1994)</text>'
             '<text x="254" y="-15" font-size="2.4">PlantAgent demonstration drawing · not a real plant P&amp;ID</text>'
             '<text x="254" y="-9" font-size="2.4">BR brine · SL slurry · ST steam · CD condensate · PG purge</text>'
             '<text x="350" y="-9" font-size="2.4">PA-SALT-01 · Rev A</text></g>')
    s.append('</svg>')
    return '\n'.join(s)


if __name__ == "__main__":
    out = DATA / "drawn"
    out.mkdir(parents=True, exist_ok=True)
    (out / "salt_mvr_pid.xml").write_text(xml())
    (ROOT / "cases" / "salt_mvr").mkdir(parents=True, exist_ok=True)
    (ROOT / "cases" / "salt_mvr" / "pid.svg").write_text(svg())
    import sys
    sys.path.insert(0, str(ROOT))
    from plantagent import pid
    ov = pid.overview(out / "salt_mvr_pid.xml")
    print(len(ov["equipment"]), "equipment,", len(ov["connections"]), "connections,", len(ov["valves"]), "valves")
    assert len(ov["equipment"]) == len(EQ) and len(ov["connections"]) >= 15
    for r in pid.relief_scan(out / "salt_mvr_pid.xml"):
        print(f"  {r['tag']:6s} {','.join(r['side_fluids']):6s} {r['status']:24s} {r['detail'][:90]}")
    print("ok")
