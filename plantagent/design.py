"""Design deliverables built from simulator results (no LLM): a new hydraulic profile sheet (DXF/DWG) and pump data sheets."""
import math

import ezdxf

from . import profile, sim

NEMA_HP = [1, 1.5, 2, 3, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500,
           600, 700, 800, 900, 1000, 1250, 1500, 1750, 2000]
IEC_KW = [0.75, 1.1, 1.5, 2.2, 3, 4, 5.5, 7.5, 11, 15, 18.5, 22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250, 315,
          355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1120, 1250]
LAYERS = {"STRUCT": 7, "WS": 5, "LIMIT": 1, "TEXT": 7, "GRID": 8, "TITLE": 7}


# --- hydraulic profile sheet -------------------------------------------------------------------
def profile_sheet(spec, flows, out, title, subtitle, prepared="PlantAgent (AI) - for review by a licensed engineer"):
    """A new to-scale hydraulic profile sheet: one column per structure, water surface at each flow, limits dashed.
    Sheet units: inches on a 36x24 (ARCH D) sheet; vertical scale chosen to fit the elevation range."""
    results = [profile.run(spec, q) for q in flows]
    nodes = results[0]["nodes"]
    limits = {}
    for c in results[0]["checks"]:
        if "limit_ft" in c:
            limits.setdefault(c["id"], []).append(c)
    elev = [n["ws_ft"] for r in results for n in r["nodes"]] + [c["limit_ft"] for cs in limits.values() for c in cs]
    lo, hi = math.floor(min(elev)) - 2, math.ceil(max(elev)) + 2
    W, H, x0, y0, plot_w, plot_h = 36.0, 24.0, 3.0, 6.0, 30.0, 15.0
    Y = lambda e: y0 + (e - lo) / (hi - lo) * plot_h  # noqa: E731
    X = lambda i: x0 + plot_w * (i + 0.5) / len(nodes)  # noqa: E731

    doc = ezdxf.new("R2018", setup=True)
    for name, color in LAYERS.items():
        doc.layers.add("PA-" + name, color=color)
    doc.linetypes.add("DASHED2", pattern=[0.25, 0.15, -0.1]) if "DASHED2" not in doc.linetypes else None
    msp = doc.modelspace()
    L = lambda k: {"layer": "PA-" + k}  # noqa: E731
    msp.add_lwpolyline([(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)], close=True, dxfattribs=L("TITLE"))

    step = max(1, round((hi - lo) / 12))
    for e in range(lo, hi + 1, step):  # elevation grid with labels both sides
        msp.add_line((x0, Y(e)), (x0 + plot_w, Y(e)), dxfattribs=L("GRID"))
        for xx, align in ((x0 - 0.15, "RIGHT"), (x0 + plot_w + 0.15, "LEFT")):
            msp.add_text(f"{e}", height=0.14, dxfattribs=L("TEXT")).set_placement((xx, Y(e)), align=getattr(ezdxf.enums.TextEntityAlignment, "MIDDLE_" + align))

    colw = plot_w / len(nodes) * 0.6
    for i, n in enumerate(nodes):
        cx = X(i)
        ws_all = [r["nodes"][i]["ws_ft"] for r in results]
        top = max([c["limit_ft"] for c in limits.get(n["id"], [])] + [max(ws_all) + 1.5])
        bottom = min(ws_all) - 3
        msp.add_lwpolyline([(cx - colw / 2, Y(top)), (cx - colw / 2, Y(bottom)), (cx + colw / 2, Y(bottom)), (cx + colw / 2, Y(top))],
                           dxfattribs=L("STRUCT"))
        msp.add_text(n["id"].upper()[:24], height=0.16, dxfattribs=L("TEXT")).set_placement(
            (cx, y0 - 0.5), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        for c in limits.get(n["id"], []):
            msp.add_line((cx - colw / 2 - 0.2, Y(c["limit_ft"])), (cx + colw / 2 + 0.2, Y(c["limit_ft"])),
                         dxfattribs={**L("LIMIT"), "linetype": "DASHED2"})
            msp.add_text(f"{c['check'][:26].upper()} {c['limit_ft']:.2f}", height=0.1, dxfattribs=L("LIMIT")).set_placement(
                (cx - colw / 2, Y(c["limit_ft"]) + 0.08))
        for k, r in enumerate(results):
            w = r["nodes"][i]["ws_ft"]
            fail = any(c["id"] == n["id"] and c["margin_ft"] < 0 for c in r["checks"])
            msp.add_line((cx - colw / 2, Y(w)), (cx + colw / 2, Y(w)), dxfattribs={**L("WS"), "color": 1 if fail else 5})
            msp.add_text(f"WS {w:.2f} @ {r['flow_mgd']:g} MGD", height=0.11,
                         dxfattribs={**L("WS"), "color": 1 if fail else 5}).set_placement((cx + colw / 2 + 0.05, Y(w) - 0.05 - 0.17 * k))
    for i in range(len(nodes) - 1):  # hydraulic grade line between structures at the highest flow
        a, b = results[-1]["nodes"][i]["ws_ft"], results[-1]["nodes"][i + 1]["ws_ft"]
        msp.add_line((X(i) + colw / 2, Y(a)), (X(i + 1) - colw / 2, Y(b)), dxfattribs={**L("WS"), "linetype": "DASHED2"})

    # title block
    tb = [(W - 12.5, 0.5), (W - 0.5, 0.5), (W - 0.5, 4.5), (W - 12.5, 4.5)]
    msp.add_lwpolyline(tb, close=True, dxfattribs=L("TITLE"))
    for k, (txt, h) in enumerate([(title.upper(), 0.28), (subtitle.upper(), 0.18),
                                  (f"FLOWS: {', '.join(f'{q:g}' for q in flows)} MGD   ELEV. IN FEET", 0.14),
                                  ("PREPARED BY: " + prepared.upper(), 0.12),
                                  ("NOT FOR CONSTRUCTION - DRAFT FOR ENGINEER REVIEW", 0.14)]):
        msp.add_text(txt, height=h, dxfattribs=L("TITLE")).set_placement((W - 12.2, 4.0 - 0.7 * k))
    doc.saveas(out)
    return {"file": str(out), "flows": flows, "structures": len(nodes), "elev_range_ft": [lo, hi]}


# --- pump data sheet ---------------------------------------------------------------------------
def _next(sizes, x):
    return next((s for s in sizes if s >= x), sizes[-1])


def pump_datasheet(spec, pump_id, run_result=None, centerline=None, suction_loss=0.0, temp_c=20.0):
    p0 = next(x for x in spec["pumps"] if x["id"] == pump_id)
    centerline = centerline if centerline is not None else p0.get("centerline_ft", p0.get("centerline_m"))
    """Duty point, power, motor size and NPSH available for one pump in a simulated network (document units)."""
    u = sim._u(spec)
    r = run_result or sim.run(spec)
    p = next(x for x in spec["pumps"] if x["id"] == pump_id)
    row = next(x for x in r["pumps"] if x["id"] == pump_id)
    F, L, P = u["flow_u"], u["len_u"], u["power_u"]
    shaft = row[f"shaft_{P}"]
    motor = _next(NEMA_HP if u["power_u"] == "hp" else IEC_KW, shaft * 1.15)  # 15% margin over the duty-point shaft power
    sheet = {"pump": pump_id, f"duty_flow_{F}": row[f"flow_{F}"], f"duty_head_{L}": row[f"tdh_{L}"], "speed": row["speed"],
             "efficiency_at_duty": row["efficiency"], f"shaft_power_{P}": shaft, f"motor_selected_{P}": motor,
             "motor_basis": "next standard size >= 1.15 x duty shaft power", "electric_kw": row["electric_kw"]}
    if "curve" in p:
        sheet[f"shutoff_head_{L}"] = p["curve"][0][1]
    if "eff_curve" in p:
        bep_q = max(p["eff_curve"], key=lambda e: e[1])[0]
        ratio = row[f"flow_{F}"] / (bep_q * row["speed"])
        sheet["bep_flow"] = bep_q
        sheet["pct_of_bep"] = round(100 * ratio)
        sheet["in_preferred_operating_region_70_120"] = 0.7 <= ratio <= 1.2
    src = next((x for x in spec.get("reservoirs", []) + spec.get("tanks", []) if x["id"] == p["from"]), None)
    if src is not None and centerline is not None:
        level = sim._f(src, "head", u) if "head_ft" in src or "head_m" in src else None
        if level is not None:
            m = u["len"]
            patm = 10.33  # m of water at sea level
            pv = {10: 0.125, 20: 0.239, 30: 0.433, 40: 0.752}[min((10, 20, 30, 40), key=lambda t: abs(t - temp_c))]
            npsha = patm + (level - centerline) * m - suction_loss * m - pv
            sheet[f"npsh_available_{L}"] = round(npsha / m, 1)
            sheet["npsh_basis"] = f"sea-level atmosphere, water {temp_c:g} C, suction level {level} {L}, centerline {centerline} {L}"
    return sheet


if __name__ == "__main__":
    import tempfile
    from pathlib import Path
    spec = {"start": {"id": "clearwell", "ws_ft": 449.0}, "elements": [
        {"type": "control", "id": "filters", "ws_ft": 464.0, "required_drop_ft": 11.0},
        {"type": "pipe", "id": "settled pipe", "diameter_in": 42, "calibrate": {"flow_mgd": 13.1, "headloss_ft": 0.233}},
        {"type": "drop", "id": "channel", "loss_ft": 0, "at_flow_mgd": 1, "max_ws_ft": 465.0, "limit_name": "overflow weir"}]}
    with tempfile.TemporaryDirectory() as t:
        info = profile_sheet(spec, [12, 18, 24], Path(t) / "p.dxf", "Proposed hydraulic profile", "Test plant")
        doc = ezdxf.readfile(Path(t) / "p.dxf")
        assert "PA-WS" in doc.layers and len(doc.modelspace().query("TEXT")) > 10, info
    net = {"reservoirs": [{"id": "wet", "head_ft": 10}, {"id": "top", "head_ft": 60}], "junctions": [{"id": "j"}],
           "pipes": [{"id": "fm", "from": "j", "to": "top", "length_ft": 2000, "diameter_in": 12}],
           "pumps": [{"id": "P1", "from": "wet", "to": "j", "curve": [[0, 90], [1200, 70], [2000, 40]],
                      "eff_curve": [[400, 0.55], [1200, 0.78], [1800, 0.7]]}]}
    ds = pump_datasheet(net, "P1", centerline=5.0)
    assert ds["motor_selected_hp"] >= ds["shaft_power_hp"] * 1.15 and 20 < ds["npsh_available_ft"] < 40, ds
    print("ok", ds)
