"""DEXPI-style P&IDs for the Monterey and Brownsville seawater RO cases.

Monterey follows the 2013 CalAm design-build RFP process description (Appendix 2), not a traced
copy of the sealed Exhibit 1 sheets. Brownsville follows Section 4 of the 2004 feasibility study.
Title blocks say the drawing was produced by PlantAgent on that flowsheet.

python tools/make_swro_pid.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/home/kizil/Desktop/hackathon/case-data")


def ga(name, value, units=None):
    if isinstance(value, (int, float)):
        return f'<GenericAttribute Name="{name}" Value="{value}" Format="double"' + (f' Units="{units}"' if units else "") + "/>"
    return f'<GenericAttribute Name="{name}" Value="{escape(str(value))}" Format="string"/>'


def xml_for(eq, lines, origin):
    out = ['<?xml version="1.0" encoding="utf-8"?>', "<PlantModel>",
           f'<PlantInformation SchemaVersion="4.1.1" OriginatingSystem="{escape(origin)}" Discipline="PID" Units="mm"/>']
    for tag, (cls, x, y, design, nozzles) in eq.items():
        out.append(f'<Equipment ID="{tag}" ComponentClass="{cls}"><Position><Location X="{x}" Y="{y}" Z="0"/></Position>'
                   f'<GenericAttributes Set="DexpiAttributes">{ga("TagNameAssignmentClass", tag)}'
                   + "".join(ga(k, v, u) for k, (v, u) in design.items()) + "</GenericAttributes>"
                   + "".join(f'<Nozzle ID="{tag}-{n}" ComponentClass="Nozzle"><GenericAttributes>{ga("SubTagNameAssignmentClass", n)}'
                             f'</GenericAttributes></Nozzle>' for n in nozzles) + "</Equipment>")
    for line, fluid, frm, to, inline in lines:
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


def orthogonal(points):
    """Insert a corner so every segment is horizontal or vertical."""
    out = [points[0]]
    for x, y in points[1:]:
        px, py = out[-1]
        if px != x and py != y:
            out.append((x, py))
        if out[-1] != (x, y):
            out.append((x, y))
    return out


def svg_for(eq, lines, names, fluids, ports, routes, labels, valves, title, subtitle, size):
    pos = {tag: (e[1], -e[2]) for tag, e in eq.items()}
    nozzle = {}
    for tag, e in eq.items():
        for n, (dx, dy) in zip(e[4], ports[tag]):
            nozzle[(tag, n)] = (pos[tag][0] + dx, pos[tag][1] + dy)
    w, h, vx, vy = size
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vx} {vy} {w} {h}" font-family="Arial,sans-serif">',
         f'<rect x="{vx}" y="{vy}" width="{w}" height="{h}" fill="#fcfbf7"/>',
         f'<rect x="{vx+4}" y="{vy+4}" width="{w-8}" height="{h-8}" fill="none" stroke="#294248" stroke-width="0.7"/>',
         '<text x="' + str(vx + 10) + '" y="' + str(vy + 16) + '" fill="#294248" font-size="5" font-weight="700">' + escape(title) + "</text>",
         '<text x="' + str(vx + 10) + '" y="' + str(vy + 23) + '" fill="#647a7b" font-size="2.8">' + escape(subtitle) + "</text>"]
    for line, fluid, frm, to, inline in lines:
        a = nozzle[frm] if frm else routes[line][0]
        b = nozzle[to] if to else routes[line][-1]
        mid = routes.get(line, [])
        if not frm:
            mid = mid[1:]
        if not to:
            mid = mid[:-1]
        points = orthogonal([a, *mid, b])
        colour = fluids[fluid][1]
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        frm_tag = frm[0] if frm else ""
        to_tag = to[0] if to else ""
        s.append(f'<g data-line="{line}" data-from="{frm_tag}" data-to="{to_tag}">'
                 f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="0.9" stroke-linejoin="round"/></g>')
        lx, ly = labels[line]
        s.append(f'<text x="{lx}" y="{ly}" fill="{colour}" font-size="2.3">{line} {fluid}</text>')
        for cls, num, extra in inline:
            vx_, vy_ = valves[line]
            if "Safety" in cls:
                s.append(f'<g transform="translate({vx_},{vy_})"><path d="M-2,2 L2,2 L0,-1 Z M0,-1 V-3" fill="#fff" stroke="#a92525" stroke-width="0.5"/>'
                         f'<text x="3" y="1" font-size="2.2" fill="#a92525">{num}</text></g>')
            else:
                s.append(f'<g transform="translate({vx_},{vy_})"><path d="M-2.5,-1.6 L0,0 L-2.5,1.6 Z M2.5,-1.6 L0,0 L2.5,1.6 Z" fill="#fff" stroke="#294248" stroke-width="0.5"/></g>')
    for tag, (x, y) in pos.items():
        s.append(f'<g data-tag="{tag}" data-pid="{tag}" data-name="{escape(names[tag])}">'
                 f'<rect x="{x-12}" y="{y-7}" width="24" height="14" fill="#fff" stroke="#294248" stroke-width="0.7"/>'
                 f'<text x="{x}" y="{y+1}" text-anchor="middle" font-size="2.6" fill="#294248">{tag}</text></g>')
        s.append(f'<text x="{x}" y="{y+12}" text-anchor="middle" font-size="2.2" fill="#647a7b">{escape(names[tag])}</text>')
    s.append("</svg>")
    return "\n".join(s)


# --- Monterey: one representative first-pass train plus the common systems in the RFP ---

MONTEREY_EQ = {
    "WF-101": ("WellField", 30, 160, {"SourceWaterHydraulicGradeLine": (155, "FootMSL"), "Scope": ("by others", None)}, ["N1", "N2"]),
    "MX-101": ("StaticMixer", 80, 160, {"Chemical": ("sodium hypochlorite", None)}, ["N1", "N2"]),
    "F-101": ("PressureFilter", 130, 160, {"MaximumFiltrationRate": (4, "GallonPerMinutePerSquareFoot"),
              "Media": ("sand 12 in + anthracite 18 in", None)}, ["N1", "N2", "N3", "N4"]),
    "T-101": ("Tank", 185, 160, {"NominalCapacity(Volume)": (300000, "Gallon"), "NumberOfTanks": (2, "")}, ["N1", "N2"]),
    "P-101": ("CentrifugalPump", 235, 160, {"Arrangement": ("two at 50 percent, two at 25 percent; VFD on the smaller pair", None)}, ["N1", "N2"]),
    "CF-101": ("CartridgeFilter", 285, 160, {"DesignPressure": (150, "PoundForcePerSquareInch"), "PoreSize": (5, "Micrometre")}, ["N1", "N2", "N3"]),
    "P-201": ("CentrifugalPump", 340, 160, {"MinimumEfficiency": (80, "Percent"), "Drive": ("VFD, one per first-pass train", None)}, ["N1", "N2"]),
    "RO-201": ("ReverseOsmosisUnit", 400, 160, {"RecoveryMinimum": (42, "Percent"), "RecoveryMaximum": (45, "Percent"),
               "MaximumFlux": (8.75, "GallonPerSquareFootPerDay"), "MaximumFeedPressure": (1000, "PoundForcePerSquareInch"),
               "ElementsPerVesselMaximum": (7, ""), "ElementArea": (400, "SquareFoot")}, ["N1", "N2", "N3", "N4", "N5"]),
    "ER-201": ("EnergyRecoveryDevice", 400, 100, {"MinimumEfficiency": (95, "Percent"), "MaximumMixing": (3, "Percent"),
               "Type": ("positive displacement, one per train", None)}, ["N1", "N2", "N3"]),
    "P-202": ("CentrifugalPump", 455, 100, {"Type": ("ERD booster, horizontal multistage", None)}, ["N1", "N2"]),
    "P-301": ("CentrifugalPump", 455, 210, {"MinimumEfficiency": (70, "Percent"), "Drive": ("VFD, one per second-pass train", None)}, ["N1", "N2"]),
    "RO-301": ("ReverseOsmosisUnit", 515, 210, {"MaximumRecovery": (90, "Percent"), "MaximumFlux": (18, "GallonPerSquareFootPerDay"),
               "PartialSecondPassMinimum": (40, "Percent")}, ["N1", "N2", "N3"]),
    "UV-401": ("UVReactor", 470, 160, {"MinimumLogInactivationCryptosporidium": (2, ""), "MinimumUVT": (95, "Percent"),
               "MaximumFlowAt9.6mgdDesign": (11.2, "MillionGallonPerDay")}, ["N1", "N2"]),
    "CC-401": ("CalciteContactor", 530, 160, {"MinimumEmptyBedContactTime": (20, "Minute"), "StandbyContactorsMinimum": (1, "")}, ["N1", "N2"]),
    "T-501": ("Tank", 590, 160, {"NominalCapacity(Volume)": (750000, "Gallon"), "NumberOfTanks": (2, ""),
              "CtVolumeAt9.6mgd": (615000, "Gallon")}, ["N1", "N2", "N3"]),
    "P-501": ("CentrifugalPump", 650, 160, {"FirmCapacity": (9.6, "MillionGallonPerDay"),
              "Arrangement": ("two at 50 percent constant speed, two at 25 percent with VFD", None)}, ["N1", "N2"]),
    "B-601": ("ConcentrateBasin", 340, 50, {"NominalCapacity(Volume)": (3000000, "Gallon"), "MinimumFreeboard": (3, "Foot")}, ["N1", "N2"]),
    "P-601": ("CentrifugalPump", 410, 50, {"Duty": ("empty the basin in 12 hours; one or two duty plus a reserve", None)}, ["N1", "N2"]),
    "W-201": ("WashwaterBasin", 130, 90, {"MinimumNumberOfBasins": (2, ""), "UnitFilterWasteVolume": (200, "GallonPerSquareFootPerWash")}, ["N1", "N2"]),
}
MONTEREY_NAMES = {
    "WF-101": "Slant wells (by others)", "MX-101": "Hypochlorite mixer", "F-101": "Media filters",
    "T-101": "Filtered-water tanks", "P-101": "Filtered-water pumps", "CF-101": "Cartridge filters",
    "P-201": "HP feed pump", "RO-201": "First-pass SWRO", "ER-201": "Energy recovery",
    "P-202": "ERD booster", "P-301": "Second-pass pump", "RO-301": "Partial second pass",
    "UV-401": "UV reactors", "CC-401": "Calcite contactors", "T-501": "Finished-water tanks",
    "P-501": "Finished-water pumps", "B-601": "Brine basin 3 MG", "P-601": "Brine pumps",
    "W-201": "Backwash basins",
}
MONTEREY_LINES = [
    ("1001", "SW", None, ("WF-101", "N1"), []),
    ("1002", "SW", ("WF-101", "N2"), ("MX-101", "N1"), [("GateValve", "C1", {})]),
    ("1003", "SW", ("MX-101", "N2"), ("F-101", "N1"), []),
    ("1004", "FW", ("F-101", "N2"), ("T-101", "N1"), []),
    ("1005", "FW", ("T-101", "N2"), ("P-101", "N1"), []),
    ("1006", "FW", ("P-101", "N2"), ("CF-101", "N1"), [("GateValve", "C1", {})]),
    ("1007", "FW", ("CF-101", "N2"), ("P-201", "N1"), []),
    ("1008", "HP", ("P-201", "N2"), ("RO-201", "N1"), []),
    ("2001", "HP", ("RO-201", "N3"), ("ER-201", "N1"), []),
    ("2002", "HP", ("ER-201", "N2"), ("P-202", "N1"), []),
    ("2003", "HP", ("P-202", "N2"), ("RO-201", "N4"), []),
    ("2004", "BR", ("ER-201", "N3"), ("B-601", "N1"), []),
    ("3001", "PW", ("RO-201", "N2"), ("P-301", "N1"), []),
    ("3002", "PW", ("P-301", "N2"), ("RO-301", "N1"), []),
    ("3003", "PW", ("RO-301", "N2"), ("UV-401", "N1"), []),
    ("3004", "BR", ("RO-301", "N3"), ("B-601", "N1"), []),
    ("4001", "PW", ("UV-401", "N2"), ("CC-401", "N1"), []),
    ("4002", "FW", ("CC-401", "N2"), ("T-501", "N1"), []),
    ("4003", "FW", ("T-501", "N2"), ("P-501", "N1"), []),
    ("4004", "FW", ("P-501", "N2"), None, [("GateValve", "C1", {})]),
    ("5001", "BR", ("B-601", "N2"), ("P-601", "N1"), []),
    ("5002", "BR", ("P-601", "N2"), None, []),
    ("6001", "WW", ("F-101", "N3"), ("W-201", "N1"), []),
    ("6002", "WW", ("W-201", "N2"), ("MX-101", "N1"), []),
    ("7001", "SW", ("F-101", "N4"), None, [("SpringLoadedGlobeSafetyValve", "PSV-101", {"SetPressureHigh": (150, "PoundForcePerSquareInch")})]),
    ("7002", "HP", ("CF-101", "N3"), None, [("SpringLoadedGlobeSafetyValve", "PSV-102", {"SetPressureHigh": (150, "PoundForcePerSquareInch")})]),
    ("7003", "HP", ("RO-201", "N5"), None, [("SpringLoadedGlobeSafetyValve", "PSV-201", {"SetPressureHigh": (1200, "PoundForcePerSquareInch")})]),
    ("7004", "FW", ("T-501", "N3"), None, [("SpringLoadedGlobeSafetyValve", "PSV-501", {})]),
]
MONTEREY_FLUID = {"SW": ("seawater", "#2b6cb3"), "FW": ("filtered / finished", "#1f8a5b"), "HP": ("high pressure", "#7a4fb3"),
                  "PW": ("permeate", "#0e7c86"), "BR": ("brine", "#a15c07"), "WW": ("washwater", "#647a7b")}
# nozzle offsets in the drawing (y down)
MONTEREY_PORTS = {tag: [(-12, 0), (12, 0)] + ([(0, 8), (0, -8)] if len(e[4]) > 2 else [])[:len(e[4]) - 2]
                  for tag, e in MONTEREY_EQ.items()}
# fix ports that need a third/fourth explicitly where the slice is wrong for 3-nozzle items
MONTEREY_PORTS.update({
    "F-101": [(-12, 0), (12, 0), (0, 8), (6, -8)],
    "CF-101": [(-12, 0), (12, 0), (0, -8)],
    "RO-201": [(-12, 0), (0, -8), (0, 8), (12, 4), (8, -8)],
    "ER-201": [(-12, 0), (12, 0), (0, 8)],
    "RO-301": [(-12, 0), (12, 0), (0, 8)],
    "T-501": [(-12, 0), (12, 0), (0, -8)],
    "B-601": [(-12, 0), (12, 0)],
    "W-201": [(-12, 0), (0, -8)],
})


def _monterey_routes():
    """Waypoints in drawing coordinates (y down). Open ends included as the full polyline."""
    return {
        "1001": [(8, -160)],
        "4004": [(690, -160)],
        "5002": [(450, -50)],
        "7001": [(136, -200)],
        "7002": [(285, -200)],
        "7003": [(430, -200)],
        "7004": [(590, -200)],
        "6002": [(130, -120), (80, -120)],
        "3004": [(515, -250), (340, -250)],
        "2004": [(400, -70), (328, -70)],
    }


MONTEREY_LABELS = {
    "1001": (10, -154), "1002": (48, -154), "1003": (98, -154), "1004": (150, -154), "1005": (200, -154),
    "1006": (250, -154), "1007": (305, -154), "1008": (362, -154), "2001": (388, -128), "2002": (420, -94),
    "2003": (430, -124), "2004": (360, -74), "3001": (420, -176), "3002": (478, -204), "3003": (500, -176),
    "3004": (420, -244), "4001": (492, -154), "4002": (552, -154), "4003": (612, -154), "4004": (668, -154),
    "5001": (368, -44), "5002": (428, -44), "6001": (118, -120), "6002": (100, -114),
    "7001": (140, -190), "7002": (290, -190), "7003": (418, -190), "7004": (596, -190),
}
MONTEREY_VALVES = {
    "1002": (55, -160), "1006": (260, -160), "4004": (672, -160),
    "7001": (136, -184), "7002": (285, -184), "7003": (412, -184), "7004": (590, -184),
}


BROWNSVILLE_EQ = {
    "IN-101": ("IntakeScreen", 40, 150, {"Source": ("Brownsville Ship Channel", None), "CapacityPhase": (25, "MillionGallonPerDay")}, ["N1", "N2"]),
    "F-101": ("BallastedFlocculation", 110, 150, {"TrainFeed": (21, "MillionGallonPerDay"), "DutyTrains": (2, ""), "InstalledTrains": (3, "")}, ["N1", "N2", "N3"]),
    "E-101": ("HeatExchanger", 180, 150, {"HeatSource": ("co-located power-plant steam", None),
              "ChannelTemperatureRange": ("60 to 95 F, average 75 F", None)}, ["N1", "N2", "N3", "N4", "N5"]),
    "CF-101": ("CartridgeFilter", 250, 150, {"Rating": (5, "Micrometre")}, ["N1", "N2"]),
    "P-201": ("CentrifugalPump", 310, 150, {"Service": ("SWRO high-pressure feed", None)}, ["N1", "N2"]),
    "RO-201": ("ReverseOsmosisUnit", 370, 150, {"PermeatePerTrain": (5, "MillionGallonPerDay"), "InstalledTrains": (6, ""),
               "DutyTrains": (5, ""), "OverallRecovery": (60, "Percent"), "ElementsPerVessel": (6, "")}, ["N1", "N2", "N3"]),
    "T-201": ("PeltonTurbine", 370, 90, {"Arrangement": ("one energy-recovery turbine per SWRO train", None)}, ["N1", "N2"]),
    "RO-301": ("ReverseOsmosisUnit", 440, 200, {"FeedPerTrain": (11.1, "MillionGallonPerDay"), "Recovery": (90, "Percent"),
               "InstalledTrains": (2, ""), "DutyTrains": (1, "")}, ["N1", "N2", "N3"]),
    "T-501": ("Tank", 510, 150, {"Service": ("finished water / clearwell", None)}, ["N1", "N2"]),
    "P-501": ("CentrifugalPump", 570, 150, {"Service": ("finished-water transfer", None)}, ["N1", "N2"]),
    "D-601": ("BrineDiffuser", 440, 70, {"InitialBrineFlow": (16.67, "MillionGallonPerDay")}, ["N1"]),
}
BROWNSVILLE_NAMES = {
    "IN-101": "Ship-channel intake", "F-101": "Ballasted flocculation", "E-101": "Feed heater",
    "CF-101": "Cartridge filters", "P-201": "SWRO feed pumps", "RO-201": "SWRO trains",
    "T-201": "Pelton turbine", "RO-301": "Partial second pass", "T-501": "Clearwell",
    "P-501": "Finished-water pumps", "D-601": "Brine diffuser",
}
BROWNSVILLE_LINES = [
    ("1001", "SW", None, ("IN-101", "N1"), []),
    ("1002", "SW", ("IN-101", "N2"), ("F-101", "N1"), [("GateValve", "C1", {})]),
    ("1003", "SW", ("F-101", "N2"), ("E-101", "N1"), []),
    ("1004", "SW", ("E-101", "N2"), ("CF-101", "N1"), []),
    ("1005", "SW", ("CF-101", "N2"), ("P-201", "N1"), []),
    ("1006", "HP", ("P-201", "N2"), ("RO-201", "N1"), []),
    ("2001", "BR", ("RO-201", "N3"), ("T-201", "N1"), []),
    ("2002", "BR", ("T-201", "N2"), ("D-601", "N1"), []),
    ("3001", "PW", ("RO-201", "N2"), ("RO-301", "N1"), []),
    ("3002", "PW", ("RO-301", "N2"), ("T-501", "N1"), []),
    ("3003", "BR", ("RO-301", "N3"), ("F-101", "N1"), []),
    ("4001", "FW", ("T-501", "N2"), ("P-501", "N1"), []),
    ("4002", "FW", ("P-501", "N2"), None, []),
    ("5001", "ST", None, ("E-101", "N3"), []),
    ("5002", "ST", ("E-101", "N4"), None, [("SpringLoadedGlobeSafetyValve", "PSV-101", {})]),
    ("7001", "SW", ("F-101", "N3"), None, [("SpringLoadedGlobeSafetyValve", "PSV-102", {})]),
    ("7002", "SW", ("E-101", "N5"), None, [("SpringLoadedGlobeSafetyValve", "PSV-103", {})]),
]
BROWNSVILLE_FLUID = {"SW": ("seawater", "#2b6cb3"), "HP": ("high pressure", "#7a4fb3"), "PW": ("permeate", "#0e7c86"),
                     "BR": ("brine", "#a15c07"), "FW": ("finished", "#1f8a5b"), "ST": ("steam", "#c0392b")}
BROWNSVILLE_PORTS = {
    "IN-101": [(-12, 0), (12, 0)], "F-101": [(-12, 0), (12, 0), (0, -8)],
    "E-101": [(-12, 0), (12, 0), (0, 8), (8, 8), (0, -8)], "CF-101": [(-12, 0), (12, 0)],
    "P-201": [(-12, 0), (12, 0)], "RO-201": [(-12, 0), (0, -8), (0, 8)],
    "T-201": [(-12, 0), (12, 0)], "RO-301": [(-12, 0), (12, 0), (0, 8)],
    "T-501": [(-12, 0), (12, 0)], "P-501": [(-12, 0), (12, 0)], "D-601": [(-12, 0)],
}


def write_pair(name, eq, lines, names, fluids, ports, routes, labels, valves, title, subtitle, origin, xml_name):
    drawn = DATA / "drawn"
    drawn.mkdir(parents=True, exist_ok=True)
    case = ROOT / "cases" / name
    case.mkdir(parents=True, exist_ok=True)
    (drawn / xml_name).write_text(xml_for(eq, lines, origin))
    (case / "pid.svg").write_text(svg_for(eq, lines, names, fluids, ports, routes, labels, valves, title, subtitle,
                                          (720, 280, -5, -260)))
    return drawn / xml_name


def main():
    import sys
    sys.path.insert(0, str(ROOT))
    from plantagent import pid
    mon = write_pair(
        "swro_monterey", MONTEREY_EQ, MONTEREY_LINES, MONTEREY_NAMES, MONTEREY_FLUID, MONTEREY_PORTS,
        _monterey_routes(), MONTEREY_LABELS, MONTEREY_VALVES,
        "Monterey Peninsula desalination plant",
        "drawn by PlantAgent on the Monterey RFP flowsheet",
        "PlantAgent tools/make_swro_pid.py", "swro_monterey_pid.xml")
    bro_routes = {"1001": [(8, -150)], "4002": [(620, -150)], "5001": [(180, -110)], "5002": [(210, -110)],
                  "7001": [(110, -190)], "7002": [(180, -190)]}
    bro_labels = {ln: (40 + 28 * i, -140) for i, (ln, *_) in enumerate(BROWNSVILLE_LINES)}
    bro_valves = {"1002": (75, -150), "5002": (196, -128), "7001": (110, -176), "7002": (180, -176)}
    bro = write_pair(
        "swro_brownsville", BROWNSVILLE_EQ, BROWNSVILLE_LINES, BROWNSVILLE_NAMES, BROWNSVILLE_FLUID, BROWNSVILLE_PORTS,
        bro_routes, bro_labels, bro_valves,
        "Brownsville seawater desalination, 25 MGD concept",
        "drawn by PlantAgent on the 2004 feasibility-study flowsheet",
        "PlantAgent tools/make_swro_pid.py", "swro_brownsville_pid.xml")
    for path, eq in ((mon, MONTEREY_EQ), (bro, BROWNSVILLE_EQ)):
        ov = pid.overview(path)
        print(path.name, len(ov["equipment"]), "equipment,", len(ov["connections"]), "connections,", len(ov["valves"]), "valves")
        assert len(ov["equipment"]) == len(eq)
        assert ov["connections"]
        for r in pid.relief_scan(path):
            if r["thermal_expansion_risk"]:
                print("  THERMAL", r["tag"], r["status"], r["detail"][:80])
    print("ok")


if __name__ == "__main__":
    main()
