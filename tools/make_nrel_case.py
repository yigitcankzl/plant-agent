"""NREL 2011 corn-stover ethanol plant (Humbird et al., NREL/TP-5100-47764) as PlantAgent area cases.

python tools/make_nrel_case.py <stream_tables.json>   (from tools/nrel_tables.py)

Writes, per modelled area, cases/nrel_ethanol_<area>/ (case.json, basis.md, pid.svg) and a DEXPI-style P&ID subset in
case-data/drawn/, and the plant case cases/nrel_ethanol/ (case.json, outcome.json with the report's stream tables).
The basis gives the design basis and the area's INPUT streams only; every output stream of the report's tables is
withheld in outcome.json, which the agent never reads.

DWSIM's databank has no biomass polymers or lumped solids, so the report's components map onto stand-in compounds mass
for mass (MAP); a reaction on a stand-in scales its coefficients by molar mass to stay mass-balanced."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/home/kizil/Desktop/hackathon/case-data")
REPORT = "Humbird et al., NREL/TP-5100-47764 (May 2011)"
MW = {"Water": 18.015, "Ethanol": 46.069, "Carbon dioxide": 44.01, "Oxygen": 31.999, "Nitrogen": 28.014, "Ammonia": 17.031,
      "Glycerol": 92.09, "Methane": 16.043, "Furfural": 96.08, "Acetic acid": 60.05, "Sulfur dioxide": 64.07,
      "Triethylene glycol": 150.17, "Tetraethylene glycol": 194.23, "PentaEthylene Glycol": 238.28, "TetraPropylene Glycol": 250.33,
      "HexaEthylene Glycol": 282.33, "HexaPropylene Glycol": 366.5}
# report component -> DWSIM compound, mass for mass. DWSIM's sugars (user databank) stall the rigorous column solver, so
# well-characterised ChemSep glycols stand in for the sugars, polymers and solids lumps: non-volatile and water-miscible.
GLUCOSE, XYLOSE, CELLULOSE, XYLAN = "Tetraethylene glycol", "Triethylene glycol", "PentaEthylene Glycol", "TetraPropylene Glycol"
SOLUBLE, INSOLUBLE = "HexaEthylene Glycol", "HexaPropylene Glycol"
MAP = {"Ethanol": "Ethanol", "Water": "Water", "Glucose (SS)": GLUCOSE, "Xylose (SS)": XYLOSE,
       "Other sugars (SS)": SOLUBLE, "Sugar Oligomers (SS)": SOLUBLE, "Organic Soluble Solids (SS)": SOLUBLE,
       "Inorganic Soluble Solids (SS)": SOLUBLE, "Ammonia": "Ammonia", "Acetic Acid": "Acetic acid",
       "Sulfuric Acid": SOLUBLE, "Furfurals": "Acetic acid", "Other Organics": "Glycerol",
       "Carbon Dioxide": "Carbon dioxide", "Methane": "Methane", "O2": "Oxygen", "N2": "Nitrogen", "CO/SOX/NOX/H2S": "Sulfur dioxide",
       "Cellulose (IS)": CELLULOSE, "Xylan (IS)": XYLAN,
       "Other Struct. Carbohydr. (IS)": INSOLUBLE, "Acetate (IS)": INSOLUBLE, "Lignin (IS)": INSOLUBLE,
       "Protein (IS)": INSOLUBLE, "Cell Mass (IS)": INSOLUBLE, "Other Insoluble Solids (IS)": INSOLUBLE}
STANDIN_NOTE = [("Ethanol, Water, CO2, O2, N2, Ammonia, Methane, Acetic acid", "themselves"),
                ("Furfurals (furfural + HMF)", "Acetic acid (furfural-water is partly immiscible; its liquid-liquid split stalls the column solver)"), ("Other Organics (glycerol, succinic acid, ...)", "Glycerol"),
                ("Glucose", GLUCOSE), ("Xylose", XYLOSE), ("Cellulose", CELLULOSE), ("Xylan", XYLAN),
                ("Soluble solids lumps: other sugars, sugar oligomers, organic and inorganic soluble solids, sulfuric acid", SOLUBLE),
                ("Insoluble solids lumps: lignin, protein, cell mass, acetate, other structural carbohydrates, other insolubles", INSOLUBLE)]
STANDIN_RULE = ("Every stand-in carries the report component's MASS (1 kg of glucose is 1 kg of " + GLUCOSE + "). The glycols are "
                "non-volatile and water-miscible, like the sugars and solids they replace (DWSIM's own sugar compounds stall its rigorous "
                "column solver). A reaction on a stand-in keeps its mass balance by scaling the coefficients with molar mass, e.g. "
                "glucose -> 2 ethanol + 2 CO2 becomes 1 " + GLUCOSE + " -> 2.1562 Ethanol + 2.1562 Carbon dioxide. Missing NRTL pairs are "
                "treated as ideal.")
PROPS = ("Total Flow", "Temperature", "Pressure", "Vapor Fraction")


def standin(row):
    """Report stream row -> {stand-in compound: kg/h}."""
    out = {}
    for comp, kg in row.items():
        if comp in MAP and kg:
            out[MAP[comp]] = out.get(MAP[comp], 0) + kg
    return {k: round(v, 1) for k, v in out.items() if abs(v) > 0.05}


def feed_spec(row):
    kg = standin(row)
    mol = {c: v / MW[c] for c, v in kg.items()}
    tot = sum(mol.values())
    return {"T_C": row["Temperature"], "P_bar": round(row["Pressure"] * 1.01325, 3), "kg_h": round(sum(kg.values()), 1),
            "x": {c: round(v / tot, 6) for c, v in mol.items()}, "components_kg_h": kg}


# ------------------------------------------------------------------ areas
# equipment: tag -> (DEXPI class, name, shape, design data text)
# lines: (stream number, fluid, from tag or None, to tag or None)
AREAS = {
    "a500": {
        "area": "A500", "title": "NREL 2011 cellulosic ethanol plant, Area 500: product, solids and water recovery (distillation, dehydration, separation)",
        "pfd": "PFD-P120-A501 to A505", "pages": "report pp. 44-46 (section 3.5) and Appendix A/E",
        "inputs": {"501": "Beer from the beer well (fermentation, Area 300; includes the vent-scrubber effluent)",
                   "305": "Seed-fermentor vent (Area 300)", "317": "Production-fermentor vent (Area 300)",
                   "524": "Fresh scrubber water", "559": "Pressure-filter drying air (from compressor M-507)"},
        "outputs": {"508": "Beer column bottoms after the economizer", "509": "Beer column overhead vent to the scrubber",
                    "510": "Beer column vapour side draw to D-502", "511": "D-502 overhead vapour", "514": "Dehydrated ethanol vapour",
                    "512": "Molecular sieve regeneration vapour", "515": "Ethanol product to storage (Area 700)",
                    "516": "D-502 bottoms, recycled to pretreatment (Area 200)", "521": "Regeneration condensate recycled to D-502",
                    "535": "Pressed stillage water to wastewater treatment (Area 600)", "571": "Lignin wet cake to the combustor (Area 800)",
                    "550": "Scrubber vent to atmosphere", "551": "Scrubber effluent returned to the beer well (Area 300)",
                    "560": "Spent drying air to the combustor (Area 800)", "506": "Preheated beer to D-501", "507": "Beer column bottoms",
                    "519": "Ethanol product vapour after H-506", "517": "Regeneration condensate", "511A": "Superheated sieve feed",
                    "523": "Combined vents to the scrubber"},
        "energy": {"QRD501": "D-501 reboiler H-501", "QCD501": "D-501 condenser H-504", "QRD502": "D-502 reboiler H-502",
                   "QCD502": "D-502 condenser H-505", "QH512": "Beer column feed interchanger H-512", "QH503": "Sieve feed superheater H-503",
                   "QH509": "Product condenser H-509"},
        "equipment": {
            "H-512": ("PlateHeatExchanger", "Beer column feed interchanger", "hx", "plate & frame; beer (cold) against beer column bottoms (hot)"),
            "D-501": ("Column", "Beer column", "column", "32 fixed-valve trays, 24 in spacing, 14 ft diameter (4.27 m), 76 ft tall; reboiler H-501 (LP steam 9.5 atm), condenser H-504"),
            "T-512": ("Column", "Vent scrubber", "column", "water scrubber for the beer column and fermentation vents; inlet gas 9,681 acfm at 91 F"),
            "D-502": ("Column", "Rectification column", "column", "45 valve trays; top section 13 ft (3.96 m) diameter, bottom 4.5 ft (1.37 m) below tray 15; thermosiphon reboiler H-502; air-cooled condenser H-505 (92.2 MMBtu/h, 3 cells)"),
            "H-503": ("TubularHeatExchanger", "Sieve feed superheater", "hx", "superheats the D-502 overhead vapour before the sieve"),
            "M-503": ("Vessel", "Molecular sieve adsorption package", "vessel", "two adsorption columns, vapour phase; removes 95 % of the water"),
            "H-506": ("TubularHeatExchanger", "Product / regeneration condensate interchanger", "hx", "cools the dry ethanol vapour against the regeneration condensate"),
            "H-509": ("TubularHeatExchanger", "Product condenser", "hx", "condenses and cools the ethanol product with cooling water"),
            "H-507": ("TubularHeatExchanger", "Regeneration condenser", "hx", "condenses the regeneration vapour under vacuum"),
            "S-505": ("Filter", "Pressure filter (lignin separator)", "filter", "2 Larox FFP 2512 units, 384 m2 filtration area each; no wash; cake air-dried to 35 % moisture"),
        },
        "lines": [("501", "BE", None, "H-512"), ("506", "BE", "H-512", "D-501"), ("507", "SG", "D-501", "H-512"), ("508", "SG", "H-512", "S-505"),
                  ("509", "VT", "D-501", "T-512"), ("305", "VT", None, "T-512"), ("317", "VT", None, "T-512"), ("524", "WA", None, "T-512"),
                  ("550", "VT", "T-512", None), ("551", "BE", "T-512", None), ("510", "EV", "D-501", "D-502"),
                  ("511", "EV", "D-502", "H-503"), ("511A", "EV", "H-503", "M-503"), ("514", "ET", "M-503", "H-506"), ("519", "ET", "H-506", "H-509"),
                  ("515", "ET", "H-509", None), ("512", "EV", "M-503", "H-507"), ("517", "EV", "H-507", "H-506"), ("521", "EV", "H-506", "D-502"),
                  ("516", "WA", "D-502", None), ("559", "AI", None, "S-505"), ("560", "AI", "S-505", None), ("535", "SG", "S-505", None),
                  ("571", "LG", "S-505", None)],
        "design": """### Design basis (report section 3.5.2, design basis text)

- Beer from fermentation (5.4 wt % ethanol) is fed to the beer column D-501 after an economizing exchanger H-512 against the beer column bottoms. The bottoms are cooled to 47 C in that economizer (a suitable temperature for liquid-solid separation).
- D-501 removes the CO2 and as little ethanol as possible to the overhead while removing about 90 % of the water to the bottoms. The ethanol leaves as a vapour side draw and is fed directly to the rectification column D-502. Both columns are modelled in the report with rigorous VLE (Aspen RADFRAC).
- D-501: 32 stages at 48 % efficiency; feed on the fourth tray from the top; molar reflux ratio 3:1; overhead vented to the scrubber (about 85 % CO2, 11 % ethanol and close to 4 % water); all of the CO2 and only 0.3 % of the feed ethanol go overhead; about 0.8 % of the feed ethanol is lost in the bottoms; more than 99 % of the feed ethanol leaves as the vapour side draw at tray 8, at 40 wt % ethanol. Overhead pressure 2 atm (15 psig). Reboiler H-501 uses low-pressure steam at 9.5 atm (125 psig).
- D-502: 45 stages at 76 % efficiency; the D-501 vapour enters on tray 33 counting from the top; the molecular-sieve recycle (72 wt % ethanol) enters on tray 14; molar reflux ratio 3.5:1 to obtain an overhead vapour of 92.5 % w/w ethanol and bottoms of 0.05 % w/w ethanol. The overhead leaves as saturated vapour at about 1.6 atm (PFD-P120-A502/A503 operating pressure). The bottoms are recycled to pretreatment as dilution water.
- Vent scrubber T-512: the beer column overhead and the seed and production fermentor vents are scrubbed with water; it recovers 99 % of the vented ethanol; the effluent (about 1.8 wt % ethanol) returns to the beer well.
- Molecular sieve M-503: the saturated D-502 overhead vapour is superheated and fed to one of two adsorption columns, which removes 95 % of the water and a small amount of ethanol; the 99.5 % ethanol vapour is cooled against the regeneration condensate and finally condensed with cooling water and pumped to storage. Regeneration: a slipstream of pure ethanol vapour strips the water off under vacuum; the mixture (about 70-72 wt % ethanol) is condensed and returned to D-502.
- Pressure filter S-505: operated without a wash; the cake is dried with air to 35 % moisture; the drying air goes to the combustor and the pressed stillage water to wastewater treatment.
""",
    },
}

FLUIDS = {"BE": ("beer", "#7a4fb3"), "SG": ("stillage", "#8a6d3b"), "VT": ("vent gas", "#6b7a8f"), "WA": ("water", "#2b6cb3"),
          "EV": ("ethanol vapour", "#c0392b"), "ET": ("ethanol", "#b03a2e"), "AI": ("air", "#4a8f8f"), "LG": ("lignin cake", "#5d4037")}


def ga(name, value):
    return f'<GenericAttribute Name="{name}" Value="{escape(str(value))}" Format="string"/>'


def dexpi(a):
    """DEXPI-style Proteus subset: one nozzle per connected line end, so pid.overview sees every connection."""
    nozzles = {tag: [] for tag in a["equipment"]}
    for num, _, frm, to in a["lines"]:
        for tag, end in ((frm, "out"), (to, "in")):
            if tag:
                nozzles[tag].append(f"N{len(nozzles[tag]) + 1}")
    out = ['<?xml version="1.0" encoding="utf-8"?>', "<PlantModel>",
           '<PlantInformation SchemaVersion="4.1.1" OriginatingSystem="PlantAgent tools/make_nrel_case.py" Discipline="PID" Units="mm"/>']
    for tag, (cls, name, _, design) in a["equipment"].items():
        out.append(f'<Equipment ID="{tag}" ComponentClass="{cls}"><GenericAttributes Set="DexpiAttributes">{ga("TagNameAssignmentClass", tag)}'
                   f'{ga("EquipmentDescription", name + "; " + design)}</GenericAttributes>'
                   + "".join(f'<Nozzle ID="{tag}-{n}" ComponentClass="Nozzle"><GenericAttributes>{ga("SubTagNameAssignmentClass", n)}</GenericAttributes></Nozzle>'
                             for n in nozzles[tag]) + "</Equipment>")
    used = {tag: 0 for tag in a["equipment"]}
    for num, fluid, frm, to in a["lines"]:
        ends = []
        for tag in (frm, to):
            if tag:
                used[tag] += 1
                ends.append(f"{tag}-N{used[tag]}")
            else:
                ends.append(None)
        conn = "<Connection" + (f' FromID="{ends[0]}"' if ends[0] else "") + (f' ToID="{ends[1]}"' if ends[1] else "") + "/>"
        out.append(f'<PipingNetworkSystem ID="L{num}" ComponentClass="PipingNetworkSystem"><GenericAttributes>{ga("LineNumberAssignmentClass", num)}'
                   f'{ga("FluidCodeAssignmentClass", fluid)}</GenericAttributes><PipingNetworkSegment ID="S{num}" ComponentClass="PipingNetworkSegment">'
                   f"{conn}</PipingNetworkSegment></PipingNetworkSystem>")
    out.append("</PlantModel>")
    return "\n".join(out)


LAYOUT = {"a500": {"H-512": (60, 150), "D-501": (120, 120), "T-512": (120, 40), "D-502": (200, 120), "H-503": (250, 60),
                   "M-503": (300, 60), "H-506": (350, 90), "H-509": (395, 60), "H-507": (300, 150), "S-505": (60, 225)}}


def svg(key, a, title):
    """Generated PFD sheet: equipment at fixed positions, streams as orthogonal polylines with their report numbers."""
    pos = LAYOUT[key]
    w, h = 440, 280
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="Arial,sans-serif">',
         f'<rect width="{w}" height="{h}" fill="#fcfbf7"/><rect x="3" y="3" width="{w - 6}" height="{h - 6}" fill="none" stroke="#294248" stroke-width="0.7"/>',
         f'<text x="10" y="14" fill="#294248" font-size="5" font-weight="700">{escape(title)}</text>',
         f'<text x="10" y="20" fill="#647a7b" font-size="2.8">Drawn by PlantAgent from the report\'s process flow diagrams ({escape(a["pfd"])}) and stream tables; stream numbers as in the report</text>']
    opens = {}
    for i, (num, fluid, frm, to) in enumerate(a["lines"]):
        colour = FLUIDS[fluid][1]
        if frm and to:
            (x1, y1), (x2, y2) = pos[frm], pos[to]
        elif to:
            x2, y2 = pos[to]
            k = opens.setdefault(to, 0)
            opens[to] += 1
            x1, y1 = x2 - 30, y2 - 12 + 9 * k
        else:
            x1, y1 = pos[frm]
            k = opens.setdefault(frm + "o", 0)
            opens[frm + "o"] += 1
            x2, y2 = x1 + 30, y1 + 12 + 9 * k
        mx = (x1 + x2) / 2 + (i % 3 - 1) * 3
        pts = f"{x1},{y1} {mx},{y1} {mx},{y2} {x2},{y2}"
        s.append(f'<g data-line="{num}" data-from="{frm or ""}" data-to="{to or ""}"><polyline points="{pts}" fill="none" stroke="{colour}" '
                 f'stroke-width="0.8" stroke-linejoin="round"/><rect x="{mx - 5}" y="{(y1 + y2) / 2 - 2.6}" width="10" height="3.6" fill="#fcfbf7"/>'
                 f'<text x="{mx - 4.5}" y="{(y1 + y2) / 2}" font-size="2.6" font-weight="700" fill="{colour}">{num}</text></g>')
    for tag, (cls, name, shape, _) in a["equipment"].items():
        x, y = pos[tag]
        g = [f'<g data-tag="{tag}" data-pid="{tag}" data-name="{escape(name)}" fill="#fff" stroke="#294248" stroke-width="0.7">']
        if shape == "column":
            g.append(f'<rect x="{x - 6}" y="{y - 25}" width="12" height="50" rx="6"/>'
                     + "".join(f'<path d="M{x - 5},{y - 18 + 7 * i} H{x + 5}" stroke-width="0.35" fill="none"/>' for i in range(6)))
            ly = y - 29
        elif shape == "vessel":
            g.append(f'<rect x="{x - 8}" y="{y - 14}" width="16" height="28" rx="6"/>')
            ly = y - 18
        elif shape == "filter":
            g.append(f'<rect x="{x - 12}" y="{y - 8}" width="24" height="16"/>'
                     + "".join(f'<path d="M{x - 9 + 4 * i},{y - 8} V{y + 8}" stroke-width="0.35" fill="none"/>' for i in range(6)))
            ly = y - 12
        else:
            g.append(f'<circle cx="{x}" cy="{y}" r="7"/><path d="M{x - 6},{y + 3} L{x - 2},{y - 3} L{x + 2},{y + 3} L{x + 6},{y - 3}" fill="none" stroke-width="0.5"/>')
            ly = y - 11
        g.append(f'<text x="{x - 10}" y="{ly}" font-size="3.2" font-weight="700" stroke="none" fill="#17383d">{tag}</text>'
                 f'<text x="{x - 10}" y="{ly + 3.4}" font-size="2.3" stroke="none" fill="#526b6c">{escape(name)}</text></g>')
        s.append("".join(g))
    s.append("</svg>")
    return "\n".join(s)


def basis_md(key, a, t):
    lines = [f"# {a['title']}", "",
             f"Source: {REPORT}, {a['pages']}. The plant processes 2,205 dry US tons/day (2,000 dry tonnes/day) of corn stover. "
             "This area is one part of the plant; its inputs come from other areas at the flows below, and its outputs go to other areas.", "",
             "## Compounds (DWSIM stand-ins)", "",
             "DWSIM's databank has no biomass polymers or lumped solids, so the report's components are represented by these compounds (by mass):", ""]
    lines += [f"- {k}: {v}" for k, v in STANDIN_NOTE]
    lines += ["", STANDIN_RULE, "", "Use these DWSIM compound names (only those present in the area's streams are needed): "
              + ", ".join(sorted({MAP[c] for c in MAP} - {"Methane", "Sulfur dioxide"})) + ". "
              "Use the NRTL property package (ethanol-water). Stream ids are the report's stream numbers prefixed with S (e.g. S501).", "",
              a["design"], "", "## Equipment (Appendix A)", ""]
    lines += [f"- {tag} {name}: {design}" for tag, (_, name, _, design) in a["equipment"].items()]
    lines += ["", "## Input streams (report stream tables; kg/h by stand-in compound)", ""]
    for num, what in a["inputs"].items():
        f = feed_spec(t[num])
        comps = ", ".join(f"{c} {v:,.1f}" for c, v in sorted(f["components_kg_h"].items(), key=lambda kv: -kv[1]))
        lines.append(f"- S{num} {what}: {f['kg_h']:,.1f} kg/h at {f['T_C']} C and {t[num]['Pressure']} atm ({f['P_bar']} bar); {comps}. "
                     f"Mole fractions: {json.dumps(f['x'])}")
    lines += ["", "## Streams to report", "",
              "Name the model streams with these report numbers so they can be compared with the report: "
              + ", ".join(f"S{n} ({w})" for n, w in a["outputs"].items()) + ".", "",
              "Utilities: low-pressure steam 9.5 atm for the reboilers; cooling water at 28 C (Area 900). The report's heat duties are not given here.", ""]
    return "\n".join(lines)


def main(tables):
    t = json.load(open(tables))
    plant = {"areas": [], "stream_tables": {}, "energy": {}}
    for key, a in AREAS.items():
        name = f"nrel_ethanol_{key}"
        d = ROOT / "cases" / name
        d.mkdir(parents=True, exist_ok=True)
        (DATA / "drawn").mkdir(parents=True, exist_ok=True)
        (DATA / "drawn" / f"{name}_pid.xml").write_text(dexpi(a))
        (d / "pid.svg").write_text(svg(key, a, a["title"]))
        (d / "basis.md").write_text(basis_md(key, a, t))
        cfg = {"kind": "process", "title": a["title"], "source": f"{REPORT}; {a['pfd']}; P&ID drawn by PlantAgent from the report's PFDs",
               "url": "https://docs.nlr.gov/docs/fy11osti/47764.pdf", "pid": f"drawn/{name}_pid.xml", "svg": "pid.svg", "basis": "basis.md",
               "task_type": "model reconstruction", "area": a["area"], "plant": "nrel_ethanol",
               "question": f"Rebuild {a['area']} from the design basis and check it against the report's stream tables: does the model reproduce the flows, temperatures and duties?",
               "target_scale": 1.0, "throughput": {"name": "Beer feed (S501)" if key == "a500" else "Area feed", "base": round(t["501"]["Total Flow"] / 1000, 1), "unit": "t/h"},
               "data_note": "Design basis and input streams from the NREL 2011 design report; outputs are withheld from the agent and compared afterwards. "
                            "Biomass components are represented by DWSIM stand-in compounds (see the basis). The P&ID is drawn by PlantAgent from the report's PFDs.",
               "benchmark": False}
        (d / "case.json").write_text(json.dumps(cfg, indent=2) + "\n")
        plant["areas"].append(name)
        nums = list(a["inputs"]) + list(a["outputs"])
        for n in nums:
            plant["stream_tables"][n] = {"area": a["area"], "role": "input" if n in a["inputs"] else "output",
                                         "what": a["inputs"].get(n) or a["outputs"].get(n), **t[n], "standin_kg_h": standin(t[n])}
        plant["energy"].update({k: {**t["_energy"][k], "what": v} for k, v in a["energy"].items()})
    out = ROOT / "cases" / "nrel_ethanol"
    out.mkdir(parents=True, exist_ok=True)
    oc = {"engineers": "NREL's Aspen Plus design model (Humbird et al. 2011, Appendix E stream tables). The agent rebuilds each area in DWSIM "
                       "from the design basis and input streams only; these output streams and duties are withheld and used to score the rebuild.",
          "source": f"{REPORT}, Appendix E (PFD-P120 stream tables, pp. 114-146)", "file": "outcome.json",
          "note": "Withheld from the agent: the area bases give inputs and design specifications only.", **plant}
    (out / "outcome.json").write_text(json.dumps(oc, indent=1) + "\n")
    print("areas:", plant["areas"], "streams kept:", len(plant["stream_tables"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "runs" / "nrel" / "streams.json"))
