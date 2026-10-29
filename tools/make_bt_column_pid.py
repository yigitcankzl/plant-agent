"""Draw the benzene–toluene column P&ID as a DEXPI-style Proteus XML subset plus a matching SVG.

The column is the standard equimolar benzene–toluene teaching problem. Shell diameter, tray spacing and the
600 kW utility ratings are illustrative (see cases/bt_column_debottleneck/basis.md). Tags and line numbers are ours.

python tools/make_bt_column_pid.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cases" / "bt_column_debottleneck"

EQ = {
    "E-101": ("Condenser", 70, 210, {"DesignHeatFlowRate": (600, "Kilowatt")}, ["N1", "N2", "N3", "N4"]),
    "V-101": ("Vessel", 130, 180, {"NominalCapacity(Volume)": (2, "MetreCubed")}, ["N1", "N2", "N3"]),
    "P-101": ("CentrifugalPump", 130, 120, {"DesignVolumeFlowRate": (4, "MetreCubedPerHour")}, ["N1", "N2"]),
    "C-101": ("DistillationColumn", 220, 140, {"InsideDiameter": (0.8, "Metre"), "NumberOfTrays": (10, "")},
              ["N1", "N2", "N3", "N4", "N5"]),
    "E-102": ("Reboiler", 300, 70, {"DesignHeatFlowRate": (600, "Kilowatt")}, ["N1", "N2", "N3", "N4"]),
}
NAMES = {"E-101": "Condenser", "V-101": "Reflux drum", "P-101": "Reflux pump",
         "C-101": "Benzene–toluene column", "E-102": "Reboiler"}
LINES = [
    ("1001", "FD", None, ("C-101", "N1"), [("GateValve", "C1", {})]),
    ("2001", "OV", ("C-101", "N2"), ("E-101", "N1"), []),
    ("2002", "RF", ("E-101", "N2"), ("V-101", "N1"), []),
    ("3001", "RF", ("V-101", "N2"), ("P-101", "N1"), []),
    ("3002", "RF", ("P-101", "N2"), ("C-101", "N3"), [("GlobeValve", "FV-101", {})]),
    ("4001", "DS", ("V-101", "N3"), None, [("GlobeValve", "FV-102", {})]),
    ("5001", "BT", ("C-101", "N4"), ("E-102", "N1"), []),
    ("5002", "BT", ("E-102", "N2"), ("C-101", "N5"), []),
    ("6001", "BT", ("E-102", "N3"), None, [("GateValve", "C1", {})]),
    ("7001", "CW", None, ("E-101", "N3"), []),
    ("7002", "CW", ("E-101", "N4"), None, []),
    ("8001", "ST", None, ("E-102", "N4"), []),
]
FLUID = {"FD": ("feed", "#2b6cb3"), "OV": ("overhead vapour", "#c0392b"), "RF": ("reflux", "#1f8a5b"),
         "DS": ("distillate", "#1f8a5b"), "BT": ("bottoms", "#7a4fb3"), "CW": ("cooling water", "#4a90a4"),
         "ST": ("steam", "#c0392b")}


def ga(name, value, units=None):
    if isinstance(value, (int, float)):
        return f'<GenericAttribute Name="{name}" Value="{value}" Format="double"' + (f' Units="{units}"' if units else "") + "/>"
    return f'<GenericAttribute Name="{name}" Value="{escape(str(value))}" Format="string"/>'


def xml():
    out = ['<?xml version="1.0" encoding="utf-8"?>', "<PlantModel>",
           '<PlantInformation SchemaVersion="4.1.1" OriginatingSystem="PlantAgent tools/make_bt_column_pid.py" '
           'Discipline="PID" Units="mm"/>']
    for tag, (cls, x, y, design, nozzles) in EQ.items():
        out.append(f'<Equipment ID="{tag}" ComponentClass="{cls}"><Position><Location X="{x}" Y="{y}" Z="0"/></Position>'
                   f'<GenericAttributes Set="DexpiAttributes">{ga("TagNameAssignmentClass", tag)}'
                   + "".join(ga(k, v, u) for k, (v, u) in design.items()) + "</GenericAttributes>"
                   + "".join(f'<Nozzle ID="{tag}-{n}" ComponentClass="Nozzle"><GenericAttributes>{ga("SubTagNameAssignmentClass", n)}'
                             f'</GenericAttributes></Nozzle>' for n in nozzles) + "</Equipment>")
    for line, fluid, frm, to, inline in LINES:
        comps = "".join(
            f'<PipingComponent ID="{line}-{num}" ComponentClass="{cls}"><GenericAttributes>{ga("PipingComponentNumberAssignmentClass", num)}'
            + "".join(ga(k, v, u) for k, (v, u) in extra.items()) + "</GenericAttributes></PipingComponent>"
            for cls, num, extra in inline)
        conn = "<Connection" + (f' FromID="{frm[0]}-{frm[1]}"' if frm else "") + (f' ToID="{to[0]}-{to[1]}"' if to else "") + "/>"
        out.append(f'<PipingNetworkSystem ID="L{line}" ComponentClass="PipingNetworkSystem"><GenericAttributes>'
                   f'{ga("LineNumberAssignmentClass", line)}{ga("FluidCodeAssignmentClass", fluid)}</GenericAttributes>'
                   f'<PipingNetworkSegment ID="S{line}" ComponentClass="PipingNetworkSegment">{comps}{conn}</PipingNetworkSegment></PipingNetworkSystem>')
    out.append("</PlantModel>")
    return "\n".join(out)


def svg():
    pos = {tag: (e[1], -e[2]) for tag, e in EQ.items()}
    ports = {
        "E-101": [(-12, 0), (12, 0), (0, -8), (0, 8)],
        "V-101": [(0, -8), (-8, 6), (8, 6)],
        "P-101": [(0, -6), (8, 0)],
        "C-101": [(-10, 8), (0, -28), (-10, -8), (8, 24), (8, 12)],
        "E-102": [(-10, 4), (-10, -4), (10, 0), (0, 8)],
    }
    nozzle = {(tag, n): (pos[tag][0] + dx, pos[tag][1] + dy)
              for tag, e in EQ.items() for n, (dx, dy) in zip(e[4], ports[tag])}
    open_end = {"1001": (140, -132), "4001": (180, -150), "6001": (340, -70),
                "7001": (70, -240), "7002": (70, -180), "8001": (300, -40)}
    route = {
        "1001": [], "2001": [(220, -210)], "2002": [(130, -210)],
        "3001": [(122, -126)], "3002": [(180, -120), (180, -148)],
        "4001": [(138, -150)], "5001": [(228, -66)],
        "5002": [(290, -128)], "6001": [],
        "7001": [], "7002": [], "8001": [],
    }
    label = {"1001": (150, -128), "2001": (140, -206), "2002": (100, -206), "3001": (108, -150),
             "3002": (184, -132), "4001": (150, -146), "5001": (232, -90), "5002": (260, -124),
             "6001": (318, -66), "7001": (48, -230), "7002": (48, -176), "8001": (304, -48)}
    valve_at = {"1001": (170, -132), "3002": (180, -136), "4001": (155, -150), "6001": (325, -70)}
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="380" height="280" viewBox="-5 -270 380 280" font-family="Arial,sans-serif">',
         '<rect x="-5" y="-270" width="380" height="280" fill="#fcfbf7"/>',
         '<rect x="1" y="-264" width="368" height="268" fill="none" stroke="#294248" stroke-width="0.7"/>',
         '<text x="8" y="-252" fill="#294248" font-size="4.4" font-weight="700">Benzene–toluene column</text>',
         '<text x="8" y="-246" fill="#647a7b" font-size="2.7">Process and instrumentation drawing · illustrative shell and utility ratings</text>']
    for line, fluid, frm, to, _inline in LINES:
        a = nozzle[frm] if frm else open_end[line]
        b = nozzle[to] if to else open_end[line]
        points = [a, *route[line], b]
        assert all(x1 == x2 or y1 == y2 for (x1, y1), (x2, y2) in zip(points, points[1:])), line
        colour = FLUID[fluid][1]
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        s.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="0.8"/>')
        s.append(f'<text x="{label[line][0]}" y="{label[line][1]}" fill="{colour}" font-size="2.4">{line}</text>')
        if line in valve_at:
            vx, vy = valve_at[line]
            s.append(f'<path d="M{vx-2},{vy-2} L{vx+2},{vy+2} L{vx+2},{vy-2} L{vx-2},{vy+2} Z" fill="none" stroke="#294248" stroke-width="0.5"/>')
    shapes = {
        "E-101": '<rect x="-14" y="-6" width="28" height="12" fill="#fff" stroke="#294248"/>',
        "V-101": '<ellipse cx="0" cy="0" rx="10" ry="8" fill="#fff" stroke="#294248"/>',
        "P-101": '<circle cx="0" cy="0" r="6" fill="#fff" stroke="#294248"/>',
        "C-101": '<rect x="-8" y="-28" width="16" height="56" fill="#fff" stroke="#294248"/>',
        "E-102": '<rect x="-12" y="-6" width="24" height="12" fill="#fff" stroke="#294248"/>',
    }
    for tag, (x, y) in pos.items():
        s.append(f'<g transform="translate({x},{y})">{shapes[tag]}'
                 f'<text x="0" y="-2" text-anchor="middle" font-size="2.6" fill="#294248">{tag}</text></g>')
        s.append(f'<text x="{x}" y="{y + 18}" text-anchor="middle" font-size="2.4" fill="#647a7b">{NAMES[tag]}</text>')
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "bt_column_pid.xml").write_text(xml())
    (OUT / "pid.svg").write_text(svg())
    print(OUT / "bt_column_pid.xml")
    print(OUT / "pid.svg")
