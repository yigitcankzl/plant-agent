"""Smart P&ID reader: DEXPI (Proteus XML 4.x / DEXPI 1.3), the vendor-neutral P&ID exchange format, -> process graph.
Standard library only.

Nodes: equipment (with nozzles + chamber design limits), piping components (valves, tees, reducers...),
off-page connectors, open line ends, instruments. Edges: pipe connections (ordered chain inside each
PipingNetworkSegment) and signal edges (sensor -> instrument -> actuator -> valve).
`equipment_paths()` collapses piping into equipment-to-equipment edges with the inline valves on the way.
"""
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

PIPE_ITEMS = {"PipingComponent", "PipeOffPageConnector", "PropertyBreak"}
SKIP_ATTR = ("NominalDiameterStandard", "NominalDiameterType", "SymbolRegistration", "TagNamePrefix",
             "TagNameSequence", "TagNameSuffix")


def attrs(el):
    """Direct GenericAttributes of an element (not of its nested Nodes) -> {name: value[ unit]}."""
    out = {}
    for ga in el.findall("GenericAttributes/GenericAttribute"):
        n = ga.get("Name", "")
        if n.startswith(SKIP_ATTR) or ga.get("Value") is None:
            continue
        n = n.replace("AssignmentClass", "").replace("RepresentationAssignmentClass", "")
        v = ga.get("Value")
        try:
            v = float(v) if ga.get("Format") == "double" else v
        except ValueError:
            pass
        out[n] = f"{v:g} {ga.get('Units')}" if ga.get("Units") and isinstance(v, float) else v
    return out


def parse(path):
    root = ET.parse(path).getroot()
    nodes, pipe_edges, sig_edges, owner = {}, [], [], {}

    def add(el, kind, **extra):
        a = attrs(el)
        tag = a.get("TagName") or a.get("SubTagName") or a.get("PipingComponentNumber") or \
            a.get("ProcessInstrumentationFunctionNumber") or a.get("ProcessSignalGeneratingFunctionNumber")
        nodes[el.get("ID")] = dict(id=el.get("ID"), kind=kind, cls=el.get("ComponentClass"), tag=tag,
                                   attrs={k: v for k, v in a.items() if not k.endswith("Number") or k == "LineNumber"},
                                   **extra)

    # Equipment (top-level and nested sub-equipment like Chamber/Impeller/TubeBundle)
    def walk_eq(el, parent=None):
        add(el, "equipment" if parent is None else "sub_equipment", parent=parent)
        top = parent or el.get("ID")
        for nz in el.findall("Nozzle"):
            add(nz, "nozzle", parent=top); owner[nz.get("ID")] = top
        for sub in el.findall("Equipment"):
            owner[sub.get("ID")] = top
            walk_eq(sub, top)
    for eq in root.findall("Equipment"):
        walk_eq(eq)
    # Roll design limits from chambers / sub-equipment up to the parent
    for n in list(nodes.values()):
        if n["kind"] == "sub_equipment" and n["attrs"]:
            nodes[n["parent"]].setdefault("parts", {})[f'{n["cls"]}:{n["id"]}'] = n["attrs"]

    # Piping: each segment is an ordered chain From -> items... -> To
    for sysel in root.findall("PipingNetworkSystem"):
        line = attrs(sysel)
        for seg in sysel.findall("PipingNetworkSegment"):
            items = [c for c in seg if c.tag in PIPE_ITEMS]
            for it in items:
                add(it, "offpage" if it.tag == "PipeOffPageConnector" else "piping_component",
                    segment=seg.get("ID"))
                owner[it.get("ID")] = it.get("ID")
                n = nodes[it.get("ID")]          # component numbers (C1, C2) restart per line -> prefix line no.
                n["tag"] = f'{line.get("LineNumber", "?")}/{n["tag"] or n["cls"]}'
            conn = seg.find("Connection")
            frm = conn.get("FromID") if conn is not None else None
            to = conn.get("ToID") if conn is not None else None
            if frm is None:
                frm = f"open-in:{seg.get('ID')}"; nodes[frm] = dict(id=frm, kind="line_end", cls="OpenEnd", tag=None, attrs={})
            if to is None:
                to = f"open-out:{seg.get('ID')}"; nodes[to] = dict(id=to, kind="line_end", cls="OpenEnd", tag=None, attrs={})
            chain = [frm] + [i.get("ID") for i in items] + [to]
            chain = [c for k, c in enumerate(chain) if k == 0 or c != chain[k - 1]]
            seg_attrs = {**line, **attrs(seg)}
            for a, b in zip(chain, chain[1:]):
                pipe_edges.append(dict(src=a, dst=b, segment=seg.get("ID"), system=sysel.get("ID"),
                                       line=seg_attrs.get("LineNumber"), dn=seg_attrs.get("NominalDiameter"),
                                       fluid=seg_attrs.get("FluidCode"), piping_class=seg_attrs.get("PipingClassCode")))

    # Instrumentation: functions, actuators, signal lines, operated-valve references
    for pif in root.findall("ProcessInstrumentationFunction"):
        a = attrs(pif)
        add(pif, "instrument")
        nodes[pif.get("ID")]["tag"] = (a.get("ProcessInstrumentationFunctionCategory", "") +
                                       a.get("ProcessInstrumentationFunctions", "") + " " +
                                       a.get("ProcessInstrumentationFunctionNumber", "")).strip()
        for psg in pif.findall("ProcessSignalGeneratingFunction"):
            add(psg, "sensor")
            loc = psg.find("Association[@Type='is located in']")
            if loc is not None:
                sig_edges.append(dict(src=loc.get("ItemID"), dst=psg.get("ID"), type="measured_at"))
        for flow in pif.findall("InformationFlow"):
            c = flow.find("Connection")
            if c is not None and c.get("FromID") and c.get("ToID"):
                sig_edges.append(dict(src=c.get("FromID"), dst=c.get("ToID"), type=flow.get("ComponentClass")))
    for asys in root.findall("ActuatingSystem"):
        for comp in asys.findall("ActuatingSystemComponent"):
            add(comp, "actuator")
        act = [c.get("ID") for c in asys.findall("ActuatingSystemComponent") if c.get("ComponentClass") != "OperatedValveReference"]
        for ref in asys.iterfind(".//Association[@Type='refers to']"):
            for a_id in act:
                sig_edges.append(dict(src=a_id, dst=ref.get("ItemID"), type="actuates"))
    # vendor exports reference connection targets this reader does not model (e.g. off-page items): keep them as boundaries
    for e in pipe_edges + sig_edges:
        for k in ("src", "dst"):
            if e[k] and e[k] not in nodes:
                nodes[e[k]] = dict(id=e[k], kind="line_end", cls="Boundary", tag=None, attrs={})
    return dict(nodes=nodes, pipe_edges=pipe_edges, signal_edges=sig_edges, owner=owner)


def equipment_paths(g):
    """Collapse nozzles into their equipment and walk through piping items: equipment/boundary -> equipment/boundary."""
    own = lambda i: g["owner"].get(i, i)
    adj = defaultdict(list)
    for e in g["pipe_edges"]:
        adj[own(e["src"])].append((own(e["dst"]), e))
    terminal = lambda i: g["nodes"].get(i, {"kind": "line_end"})["kind"] in ("equipment", "offpage", "line_end")
    paths = []
    for start in [n for n in adj if terminal(n)]:
        stack = [(start, [], [])]
        while stack:
            cur, via, lines = stack.pop()
            for nxt, e in adj[cur]:
                if nxt in via:
                    continue
                ln = lines + ([e["line"]] if e["line"] and e["line"] not in lines else [])
                if terminal(nxt):
                    paths.append(dict(src=start, dst=nxt, via=via, lines=ln))
                else:
                    stack.append((nxt, via + [nxt], ln))
    return paths


def label(g, i):
    n = g["nodes"].get(i, {"cls": "?", "tag": None})
    return f'{n.get("tag") or i}({n["cls"]})'



def overview(path):
    """What an engineer reads off the P&ID: equipment with design data, how it is connected, valves, control loops."""
    g = parse(path)
    n = g["nodes"]
    eq = [{"tag": x["tag"], "id": x["id"], "class": x["cls"], "design": {k: v for k, v in x["attrs"].items() if k != "TagName"},
           "design_limits": list(x.get("parts", {}).values())} for x in n.values() if x["kind"] == "equipment"]
    paths = [{"from": label(g, p["src"]), "to": label(g, p["dst"]), "lines": p["lines"],
              "inline": [label(g, v) for v in p["via"] if "Tee" not in n[v]["cls"]]} for p in equipment_paths(g)]
    lines = {}
    for e in g["pipe_edges"]:
        lines.setdefault(e["line"], {"line": e["line"], "fluid_code": e["fluid"], "piping_class": e["piping_class"], "dn": e["dn"]})
    valves = [{"tag": x["tag"], "class": x["cls"], **({"set_pressure": x["attrs"]["SetPressureHigh"]} if "SetPressureHigh" in x["attrs"] else {})}
              for x in n.values() if x["kind"] == "piping_component" and "Valve" in x["cls"]]
    control = [f'{label(g, e["src"])} --{e["type"]}--> {label(g, e["dst"])}' for e in g["signal_edges"]]
    return {"equipment": eq, "connections": paths, "lines": list(lines.values()), "valves": valves, "control": control,
            "data_quality": lint(eq)}


RELIEF = ("SafetyValve", "ReliefValve", "RuptureDisc", "BurstingDisc", "BreatherValve")
BLOCKING = ("Valve",)  # any valve that can be closed: block, check and control valves alike


def relief_scan(path):
    """For every side of every equipment item: can it reach a relief device without passing a valve that could be closed?
    That is the Williams Geismar question: an exchanger side that heat can reach, isolatable from its relief, ruptures.
    Sides are told apart by the fluid code of the lines on their nozzles. Deterministic graph search, no LLM."""
    g = parse(path)
    n = g["nodes"]
    adj, fwd = defaultdict(set), set()
    for e in g["pipe_edges"]:
        adj[e["src"]].add(e["dst"]); adj[e["dst"]].add(e["src"])
        fwd.add((e["src"], e["dst"]))  # segments run from the relief device's inlet to its outlet
    fluid_of = defaultdict(set)
    for e in g["pipe_edges"]:
        for k in ("src", "dst"):
            if n.get(e[k], {}).get("kind") == "nozzle" and e["fluid"]:
                fluid_of[e[k]].add(e["fluid"].rstrip("abcdefghijklmnopqrstuvwxyz") or e["fluid"])  # WKa/WKb: supply and return of one side
    is_relief = lambda i: any(r in (n.get(i, {}).get("cls") or "") for r in RELIEF)  # noqa: E731
    is_valve = lambda i: "Valve" in (n.get(i, {}).get("cls") or "") and not is_relief(i)  # noqa: E731
    out = []
    for eq in [x for x in n.values() if x["kind"] == "equipment" and x.get("tag")]:
        nozzles = [x["id"] for x in n.values() if x["kind"] == "nozzle" and x.get("parent") == eq["id"]]
        sides = defaultdict(list)
        for z in nozzles:
            sides[tuple(sorted(fluid_of[z])) or ("?",)].append(z)
        heated = "HeatExchanger" in eq["cls"] or "Heater" in eq["cls"] or "Reboiler" in eq["cls"]
        for fluids, starts in sides.items():
            # breadth-first over the piping; remember the closable valves crossed on the way
            best, seen, todo = None, set(starts), [(z, ()) for z in starts]
            boundary = False
            while todo:
                cur, via = todo.pop(0)
                for nx in adj[cur]:
                    if nx in seen or n.get(nx, {}).get("kind") in ("nozzle",) and n[nx].get("parent") == eq["id"]:
                        continue
                    if n.get(nx, {}).get("kind") == "equipment" or n.get(nx, {}).get("kind") == "nozzle":
                        continue  # stop at other equipment: its relief is its own
                    seen.add(nx)
                    v = via + ((n[nx].get("tag") or n[nx]["cls"]),) if is_valve(nx) else via
                    if is_relief(nx):
                        if (cur, nx) not in fwd:  # reached from its outlet: this relief valve discharges here, it does not protect it
                            continue
                        if best is None or len(v) < len(best[1]):
                            best = ((n[nx].get("tag") or n[nx]["cls"]), v)
                        continue
                    if n.get(nx, {}).get("kind") in ("line_end", "offpage"):
                        boundary = True
                        continue
                    todo.append((nx, v))
            if best and not best[1]:
                status, text = "protected", f"relief {best[0]} with no closable valve in between"
            elif best:
                status, text = "isolatable", f"relief {best[0]} only through {', '.join(best[1])}: if one is closed the side has no relief"
            else:
                status, text = "no relief on this P&ID", "no relief device reachable" + (" (lines leave the drawing: check the connecting P&ID)" if boundary else "")
            risk = heated and status != "protected"
            out.append({"tag": eq["tag"], "class": eq["cls"], "side_fluids": list(fluids), "status": status, "detail": text,
                        "thermal_expansion_risk": risk,
                        "why": ("a heat-exchanger side that can be blocked in while the other side is hot: liquid thermal expansion can "
                                "exceed the design pressure (API 521 hydraulic expansion; Williams Geismar 2013)") if risk else ""})
    return out


def _num(v):
    try:
        return float(str(v).split()[0])
    except (ValueError, IndexError):
        return None


def lint(eq):
    """Design data that does not hang together: flag it before anyone builds a model on it."""
    out = []
    for e in eq:
        d = e["design"]
        q, h, p = _num(d.get("DesignVolumeFlowRate")), _num(d.get("DesignPressureHead")), _num(d.get("DesignShaftPower"))
        if q and h and p:
            eff = 1000 * 9.81 * q / 3600 * h / 1000 / p
            if not 0.3 <= eff <= 0.9:
                out.append(f"{e['tag']}: rated {q:g} m3/h at {h:g} m needs {1000 * 9.81 * q / 3600 * h / 1000:.1f} kW hydraulic, "
                           f"but the shaft power is {p:g} kW (implied efficiency {eff:.0%}): check the datasheet")
        vol = _num(d.get("NominalCapacity(Volume)"))
        for part in e["design_limits"]:
            dn, length = _num(part.get("NominalDiameter")), _num(d.get("CylinderLength"))
            if vol and dn and length:
                geo = 3.14159 / 4 * (dn / 1000) ** 2 * length
                if abs(geo / vol - 1) > 0.3:
                    out.append(f"{e['tag']}: nominal volume {vol:g} m3 but diameter {dn:g} mm x length {length:g} m gives {geo:,.0f} m3: check the datasheet")
                break
    return out


if __name__ == "__main__":
    import sys as _s
    o = overview(_s.argv[1] if len(_s.argv) > 1 else str(__import__("pathlib").Path(__file__).resolve().parents[2] /
                 "case-data/realcad/dexpi/C01V04-VER.EX01.xml"))
    print(json.dumps(o, indent=1)[:3000])
    assert {e["tag"] for e in o["equipment"]} >= {"P4711", "H1007", "T4750"} and o["connections"]
    print("ok", len(o["equipment"]), "equipment,", len(o["connections"]), "connections")
    for r in relief_scan(_s.argv[1] if len(_s.argv) > 1 else str(__import__("pathlib").Path(__file__).resolve().parents[2] /
                         "case-data/realcad/dexpi/C01V04-VER.EX01.xml")):
        print(f"  {r['tag']:6s} {','.join(r['side_fluids']):10s} {r['status']:24s} {'THERMAL ' if r['thermal_expansion_risk'] else ''}{r['detail']}")
