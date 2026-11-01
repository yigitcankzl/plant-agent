"""Electrical discipline: does the plant's power system carry a proposal's new or bigger motors?

cases/<case>/electrical.json is the one-line diagram (utility infeed, transformers, buses, generators, lumped loads,
motor feeders mapped to process unit ids). Motor electrical load = shaft kW from the process solve at the checked
throughput / motor efficiency; a motor whose unit is not in the solve runs at its rated kW. A proposal's added pump or
compressor with a max_kW rating becomes a new motor feeder; an upsized motor takes its new rating (limits/units max_kW or
"N kW" in its physical_change).

pandapower (load flow) runs in its own venv (.venv-electrical), one subprocess per check, so the DWSIM venv is untouched.
Motor start: the largest new or changed motor is replaced by its locked-rotor impedance (constant impedance: DOL
lrc x rated kVA at PF 0.3; soft starter 3.5 x at PF 0.3; VFD 1.1 x at PF 0.95) and the load flow re-run; the dip is the
voltage drop at each bus. The utility source impedance (from its short-circuit level) is in the network; on-site
generators are not credited and other loads are constant impedance during the start, so the screen is conservative.

Usage (worker): .venv-electrical/bin/python -m plantagent.electrical --solve < net.json
"""
import copy
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv-electrical" / "bin" / "python"
START = {"DOL": (None, 0.3), "SOFT": (3.5, 0.3), "SOFT_STARTER": (3.5, 0.3), "VFD": (1.1, 0.95)}  # (x rated, PF); DOL uses lrc
LIMITS = {
    "transformer": (100.0, "IEC 60076-1: continuous loading within the nameplate rated power"),
    "cable": (100.0, "cable ampacity (manufacturer rating, IEC 60287 basis)"),
    "voltage": (5.0, "typical plant practice: steady-state bus voltage within ±5 % of nominal (IEC 60038 allows ±10 % at supply)"),
    "dip_motor": (15.0, "typical practice: motor terminal voltage at least 85 % during start (IEC 60034-1 sets no start-dip limit)"),
    "dip_other": (10.0, "typical practice: other buses dip at most 10 % during a motor start (contactor drop-out, lighting flicker)"),
}
DRIVEN = ("pump", "compressor")


def available():
    return PY.exists()


def config(case):
    """cases/<case>/electrical.json, else the drafted one-line (plantagent/drafts.py), else None."""
    from . import drafts
    return drafts.case_file(case, "electrical.json", ROOT)


def _q(p_mw, pf):
    return p_mw * math.tan(math.acos(pf))


def _kw_in_text(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*kW\b", str(text or ""))
    return float(m.group(1)) if m else None


def motor_changes(cfg, changes, overrides=None):
    """New motors and re-rated motors a proposal implies: {unit: {kw, new, start?, bus?}}."""
    known = {m["unit"]: m for m in cfg["motors"]}
    out = {}
    for c in changes or []:
        u = c.get("add_unit") if isinstance(c, dict) else None
        if isinstance(u, dict) and u.get("type") in DRIVEN and (c.get("limits") or {}).get("max_kW"):
            out[u["id"]] = {"kw": float(c["limits"]["max_kW"]), "new": True, "bus": c.get("bus"),
                            "source": c.get("rating_source") or "proposal limits.max_kW"}
            continue
        path = str(c.get("path") or "")
        parts = path.split(".")
        if len(parts) == 3 and parts[0] in ("units", "limits") and parts[1] in known:
            kw = float(c["value"]) if parts[2] == "max_kW" else _kw_in_text(c.get("physical_change"))
            if kw:
                out[parts[1]] = {"kw": kw, "new": False, "source": c.get("rating_source") or c.get("physical_change") or path}
    for o in overrides or []:
        out[o["unit"]] = {**out.get(o["unit"], {}), **{k: v for k, v in o.items() if k != "unit"},
                          "new": o["unit"] not in known, "source": o.get("source") or "engineer override"}
    return out


def affected(cfg, changes):
    """True when the changes add or re-rate a motor, or carry an electrical.* overlay (plantagent/overlays.py)."""
    from . import overlays
    return bool(motor_changes(cfg, changes)) or any(str(c.get("path") or "").startswith("electrical.")
                                                     for c in changes or [] if overlays.is_overlay(c))


def _supply(cfg, bus):
    """Rated MVA of the transformer feeding a bus (0 when fed directly by the grid)."""
    return sum(t["sn_mva"] for t in cfg["transformers"] if t["lv"] == bus)


def network(cfg, solved, changes=None, overrides=None):
    """The load-flow input: buses, source impedance, transformers, generators, loads, one cable + terminal per motor."""
    units = (solved or {}).get("units") or {}
    nm = cfg.get("new_motor") or {}
    motors = []
    for m in cfg["motors"]:
        motors.append({**copy.deepcopy(m), "new": False, "changed": False})
    for unit, ch in motor_changes(cfg, changes, overrides).items():
        old = next((m for m in motors if m["unit"] == unit), None)
        if old:
            old.update({"kw": ch["kw"], "changed": True, "rating_source": ch["source"]},
                       **{k: ch[k] for k in ("start", "bus") if ch.get(k)})
            if ch.get("cable"):
                old["cable"] = {**old["cable"], "type": ch["cable"]}
            continue
        mv = ch["kw"] >= nm.get("mv_from_kw", 250)
        boards = [b["id"] for b in cfg["buses"] if (b["vn_kv"] >= 1.0) == mv and _supply(cfg, b["id"])] or \
                 [b["id"] for b in cfg["buses"] if (b["vn_kv"] >= 1.0) == mv]
        bus = ch.get("bus") or max(boards, key=lambda b: _supply(cfg, b))
        motors.append({"id": f"M-{unit}", "unit": unit, "bus": bus, "kw": ch["kw"], "eff": nm.get("eff", 0.95),
                       "pf": nm.get("pf", 0.88), "start": ch.get("start") or nm.get("start", "DOL"), "lrc": nm.get("lrc", 6.0),
                       "cable": copy.deepcopy(nm.get("cable_mv" if mv else "cable_lv")), "new": True, "changed": False,
                       "rating_source": ch["source"], "source": nm.get("source")})
        if ch.get("cable"):
            motors[-1]["cable"]["type"] = ch["cable"]
    for m in motors:
        shaft = (units.get(m["unit"]) or {}).get("kW")
        m["shaft_kW"] = float(shaft) if shaft is not None else float(m["kw"])
        m["shaft_source"] = "process solve" if shaft is not None else "rated kW (unit not in the process model)"
        m["p_mw"] = m["shaft_kW"] / m["eff"] / 1000.0
        m["q_mvar"] = _q(m["p_mw"], m["pf"])
        m["s_rated_mva"] = m["kw"] / m["eff"] / m["pf"] / 1000.0
    return {"buses": cfg["buses"], "ext_grid": cfg["ext_grid"], "transformers": cfg["transformers"],
            "generators": cfg.get("generators") or [], "cable_types": cfg["cable_types"],
            "loads": [{**l, "q_mvar": _q(l["p_mw"], l["pf"])} for l in cfg.get("loads") or []], "motors": motors}


def _run(net, start=None):
    if not available():
        raise RuntimeError(f"pandapower venv missing ({PY}); see docs/electrical.md")
    r = subprocess.run([str(PY), "-m", "plantagent.electrical", "--solve"], input=json.dumps({"net": net, "start": start}),
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    if r.returncode:
        raise RuntimeError(f"pandapower failed: {r.stderr[-800:]}")
    return json.loads(r.stdout)


def check(cfg, solved, changes=None, overrides=None, scale=1.0):
    """Load flow + motor-start screen. Returns {checks, buses, transformers, cables, start, net} (checks like process checks).
    electrical.* changes (plantagent/overlays.py) are applied to a copy of the one-line diagram first."""
    from . import overlays
    cfg, ov, upgrades = overlays.electrical(cfg, changes)
    drives = {m["unit"] for m in cfg["motors"]} | set(motor_changes(cfg, changes))
    overrides = list(overrides or []) + [o for o in ov if o["unit"] in drives]
    net = network(cfg, solved, changes, overrides)
    base = _run(net)
    checks = []

    names = {b["id"]: b.get("name") or b["id"] for b in cfg.get("buses") or []}
    where = lambda bid: f"{bid[:-5]} motor terminal" if bid.endswith("-term") else names.get(bid, bid)  # noqa: E731

    def add(uid, what, value, key):
        limit, src = LIMITS[key]
        checks.append({"id": uid, "check": what, "value": round(value, 2), "limit": limit, "unit": "%",
                       "utilisation": round(value / limit, 3), "basis": src, "source": src})
    for t in base["transformers"]:
        add(t["id"], "transformer loading vs nameplate", t["loading_percent"], "transformer")
    for c in base["cables"]:
        add(c["id"], "cable loading vs ampacity", c["loading_percent"], "cable")
    for b in base["buses"]:
        add(b["id"], f"{where(b['id'])}: {'under' if b['vm_pu'] < 1 else 'over'}-voltage {b['vm_pu']:.3f} p.u. vs ±5 %",
            abs(1 - b["vm_pu"]) * 100, "voltage")
    movers = [m for m in net["motors"] if m["new"] or m["changed"]]
    start = None
    if movers:
        m = max(movers, key=lambda x: x["s_rated_mva"])
        mult, pf = START.get(str(m["start"]).upper(), START["DOL"])
        s = m["s_rated_mva"] * (mult or float(m["lrc"]))
        # conservative screen: on-site generators are not credited during the start (a constant-power generator model
        # finds non-physical low-voltage solutions), and every load is constant impedance, so the network is linear
        quiet = {**net, "generators": []}
        v0 = {b["id"]: b["vm_pu"] for b in _run(quiet, {"motor": None})["buses"]}
        term = f"{m['id']}-term"
        try:
            dip_run = _run(quiet, {"motor": m["id"], "p_mw": s * pf, "q_mvar": s * math.sin(math.acos(pf))})
            dips = {b["id"]: (v0[b["id"]] - b["vm_pu"]) / v0[b["id"]] * 100 for b in dip_run["buses"]}
            collapse = False
        except RuntimeError as e:
            if "did not converge" not in str(e):
                raise
            # no load-flow solution with the locked rotor connected: the supply cannot start it (voltage collapse)
            dips, collapse = {b: 100.0 for b in v0}, True
        start = {"motor": m["id"], "unit": m["unit"], "method": m["start"], "start_kva": round(s * 1000),
                 "dip_percent": {k: round(v, 2) for k, v in dips.items()}, "terminal_dip_percent": round(dips[term], 2),
                 "collapse": collapse}
        add(term, f"start dip at {m['id']} terminal ({m['start']})", max(0.0, dips[term]), "dip_motor")
        for bid, d in dips.items():
            if not bid.endswith("-term"):
                add(bid, f"{where(bid)}: dip during {m['id']} start ({m['start']})", max(0.0, d), "dip_other")
    checks.sort(key=lambda c: -c["utilisation"])
    return {"scale": scale, "checks": checks, **base, "start": start, "net": net, "upgrades": upgrades}


def one_line_svg(title, res):
    """A small one-line diagram: utility, transformers, buses as bars, motor feeders below; loadings coloured."""
    net = res["net"]
    util = {(c["id"], c["check"].split(" ")[0]): c["utilisation"] for c in res["checks"]}
    colour = lambda u: "#15803d" if u is None or u < 0.8 else "#d97706" if u <= 1.0 else "#b91c1c"  # noqa: E731
    order = sorted(net["buses"], key=lambda b: -b["vn_kv"])
    W, row = 760, 120
    bus_y = {b["id"]: 90 + i * row for i, b in enumerate(order)}
    motors_by_bus = {}
    for m in net["motors"]:
        motors_by_bus.setdefault(m["bus"], []).append(m)
    H = 90 + len(order) * row + 40
    trafo = {t["id"]: t for t in res["transformers"]}
    vm = {b["id"]: b["vm_pu"] for b in res["buses"]}
    cable = {c["id"]: c for c in res["cables"]}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="11">',
           f'<rect width="{W}" height="{H}" fill="#fff"/><text x="16" y="22" font-size="14" font-weight="600">{title}</text>',
           f'<text x="16" y="40" fill="#555">utility {net["ext_grid"]["s_sc_mva"]} MVA short-circuit → {order[0]["id"]}</text>']
    for b in order:
        y = bus_y[b["id"]]
        dev = abs(1 - vm.get(b["id"], 1)) * 100
        out.append(f'<line x1="40" y1="{y}" x2="{W - 40}" y2="{y}" stroke="{colour(dev / 5)}" stroke-width="5"/>'
                   f'<text x="44" y="{y - 8}">{b["id"]} {b["vn_kv"]} kV · {vm.get(b["id"], 1):.3f} p.u.</text>')
        for g in [g for g in net["generators"] if g["bus"] == b["id"]]:
            out.append(f'<circle cx="{W - 90}" cy="{y - 26}" r="13" fill="none" stroke="#333"/><text x="{W - 97}" y="{y - 22}">G</text>'
                       f'<line x1="{W - 90}" y1="{y - 13}" x2="{W - 90}" y2="{y}" stroke="#333"/><text x="{W - 70}" y="{y - 26}">{g["id"]} {g["p_mw"]} MW</text>')
        for i, m in enumerate(motors_by_bus.get(b["id"], [])):
            x = 120 + i * 150
            c = cable.get(f"{m['id']}-cable") or {}
            col = "#7c3aed" if m["new"] or m["changed"] else "#333"
            out.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 40}" stroke="{colour((c.get("loading_percent") or 0) / 100)}" stroke-width="2"/>'
                       f'<circle cx="{x}" cy="{y + 54}" r="13" fill="none" stroke="{col}" stroke-width="{2 if col != "#333" else 1}"/>'
                       f'<text x="{x - 5}" y="{y + 58}" fill="{col}">M</text>'
                       f'<text x="{x + 18}" y="{y + 50}" fill="{col}">{m["id"]} {m["kw"]:g} kW {m["start"]}{" NEW" if m["new"] else " UPSIZED" if m["changed"] else ""}</text>'
                       f'<text x="{x + 18}" y="{y + 64}" fill="#555">cable {c.get("loading_percent", 0):.0f} %</text>')
    for t in net["transformers"]:
        y1, y2 = bus_y[t["hv"]], bus_y[t["lv"]]
        x, u = W // 2 + 120, (trafo.get(t["id"]) or {}).get("loading_percent", 0) / 100
        ym = (y1 + y2) / 2
        out.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{ym - 14}" stroke="#333"/><line x1="{x}" y1="{ym + 14}" x2="{x}" y2="{y2}" stroke="#333"/>'
                   f'<circle cx="{x}" cy="{ym - 6}" r="9" fill="none" stroke="{colour(u)}" stroke-width="2"/>'
                   f'<circle cx="{x}" cy="{ym + 6}" r="9" fill="none" stroke="{colour(u)}" stroke-width="2"/>'
                   f'<text x="{x + 16}" y="{ym + 4}" fill="{colour(u)}">{t["id"]} {t["sn_mva"]} MVA · {u * 100:.0f} %</text>')
    if res.get("start"):
        s = res["start"]
        out.append(f'<text x="16" y="{H - 14}" fill="#333">Start of {s["motor"]} ({s["method"]}, {s["start_kva"]} kVA): '
                   f'terminal dip {s["terminal_dip_percent"]:.1f} % · '
                   + " · ".join(f"{k} {v:.1f} %" for k, v in s["dip_percent"].items() if not k.endswith("-term")) + "</text>")
    out.append("</svg>")
    return "\n".join(out)


def summary(res, before=None):
    """One line for the UI and documents: transformer loading (before → after) and the start dip."""
    tr = max(res["transformers"], key=lambda t: t["loading_percent"])
    b = next((t for t in (before or {}).get("transformers") or [] if t["id"] == tr["id"]), None)
    s = res.get("start")
    over = [c for c in res["checks"] if c["utilisation"] > 1]
    return (f"{tr['id']} {'%.0f → ' % b['loading_percent'] if b else ''}{tr['loading_percent']:.0f} % loaded"
            + (f"; {s['motor']} {s['method']} start dip {s['terminal_dip_percent']:.1f} % at its terminal" if s else "")
            + (f"; OVER: {', '.join(c['id'] + ' ' + c['check'] for c in over[:3])}" + (f" (+{len(over) - 3} more)" if len(over) > 3 else "")
               if over else "; all electrical checks within limits")
            + (f"; {'; '.join(res['upgrades'])}" if res.get("upgrades") else ""))


def for_workspace(w, changes=None, scale=None, overrides=None, title=None, save=True, spec=None):
    """Electrical check of a workspace's model with a proposal's changes at a throughput scale; saves an SVG artifact.
    `spec`: the model the changes apply to (default the current one; the MOC pack passes the as-built model)."""
    from .plant import patch
    cfg = config(w.name)
    if not cfg:
        return {"note": "no electrical one-line diagram (cases/<case>/electrical.json) for this plant"}
    scale = float(scale or w.cfg.get("target_scale", 1.0))
    changes = changes or []
    base = w._solve(spec, scale) if spec is not None else w.state(scale)
    before = check(cfg, base, scale=scale) if changes or overrides else None
    res = check(cfg, w._solve(patch(spec if spec is not None else w.spec, changes), scale) if changes else base,
                changes, overrides, scale)
    line = summary(res, before)
    out = {"scale": scale, "summary": line, "checks": res["checks"], "start": res["start"], "transformers": res["transformers"],
           "transformers_before": (before or {}).get("transformers"), "grid_import_mw": res["grid_import_mw"],
           "motors": [{k: m[k] for k in ("id", "unit", "bus", "kw", "shaft_kW", "shaft_source", "start", "new", "changed")}
                      for m in res["net"]["motors"]], "note": cfg.get("note")}
    if save:
        from . import artifacts
        title = title or f"Electrical check at {scale * 100:.0f} %"
        meta = artifacts.save(w.name, "calculation", title, {"one-line.svg": one_line_svg(title, res),
                                                              "electrical.json": json.dumps(out, indent=1)},
                              by="PlantAgent (pandapower)", sources=[f"cases/{w.name}/electrical.json", "process solve", "pandapower load flow"],
                              summary=line)
        out.update({k: meta[k] for k in ("id", "kind", "title", "files")})
        out["svg"] = f"/api/plant/{w.name}/artifact/{meta['id']}/one-line.svg"
    return out


def motor_proposal(w, p):
    """True when a proposal adds or re-rates a motor this plant's one-line diagram knows about."""
    cfg = config(w.name)
    return bool(cfg and motor_changes(cfg, p.get("changes") or []))


# ---------------------------------------------------------------- worker side (pandapower venv)

def _solve(net, start=None):
    import pandapower as pp
    n = pp.create_empty_network(sn_mva=1.0)

    def put(at, p, q, name, vn):
        # during a start every load is a shunt admittance, i.e. constant impedance (usual motor-starting practice; a
        # constant-impedance *load* does not converge for deep dips in pandapower's Newton-Raphson, a shunt is linear)
        if start:
            pp.create_shunt(n, at, p_mw=p, q_mvar=q, vn_kv=vn, name=name)
        else:
            pp.create_load(n, at, p_mw=p, q_mvar=q, name=name)
    bus, kv = {}, {}
    for b in net["buses"]:
        bus[b["id"]] = pp.create_bus(n, vn_kv=b["vn_kv"], name=b["id"])
        kv[b["id"]] = b["vn_kv"]
    g = net["ext_grid"]
    src = pp.create_bus(n, vn_kv=kv[g["bus"]], name="source")
    pp.create_ext_grid(n, src, vm_pu=g.get("vm_pu", 1.0))
    z = 1.0 / g["s_sc_mva"]  # p.u. on 1 MVA
    x = z / math.sqrt(1 + g.get("rx", 0.1) ** 2)
    pp.create_impedance(n, src, bus[g["bus"]], rft_pu=x * g.get("rx", 0.1), xft_pu=x, sn_mva=1.0)
    tr = {}
    for t in net["transformers"]:
        tr[t["id"]] = pp.create_transformer_from_parameters(
            # off-load tap as a ratio: tap_percent > 0 raises the LV side (rated LV voltage above nominal)
            n, bus[t["hv"]], bus[t["lv"]], sn_mva=t["sn_mva"], vn_hv_kv=kv[t["hv"]],
            vn_lv_kv=kv[t["lv"]] * (1 + float(t.get("tap_percent", 0)) / 100),
            vkr_percent=t["vkr_percent"], vk_percent=t["vk_percent"], pfe_kw=0.0, i0_percent=0.0, name=t["id"])
    for s in net["generators"]:
        pp.create_sgen(n, bus[s["bus"]], p_mw=s["p_mw"], q_mvar=s.get("q_mvar", 0.0), name=s["id"])
    for ld in net["loads"]:
        put(bus[ld["bus"]], ld["p_mw"], ld["q_mvar"], ld["id"], kv[ld["bus"]])
    lines = {}
    for m in net["motors"]:
        term = pp.create_bus(n, vn_kv=kv[m["bus"]], name=f"{m['id']}-term")
        ct = net["cable_types"][m["cable"]["type"]]
        lines[m["id"]] = pp.create_line_from_parameters(
            n, bus[m["bus"]], term, length_km=m["cable"]["length_km"], r_ohm_per_km=ct["r_ohm_per_km"],
            x_ohm_per_km=ct["x_ohm_per_km"], c_nf_per_km=ct.get("c_nf_per_km", 0), max_i_ka=ct["max_i_ka"], name=f"{m['id']}-cable")
        if start and start["motor"] == m["id"]:  # locked rotor at its starting kVA
            put(term, start["p_mw"], start["q_mvar"], m["id"], kv[m["bus"]])
        else:
            put(term, m["p_mw"], m["q_mvar"], m["id"], kv[m["bus"]])
    for i, init in enumerate(("flat", "dc", "auto")):  # flat first: it lands on the high-voltage (physical) solution
        try:
            pp.runpp(n, init=init, max_iteration=100)
            break
        except pp.LoadflowNotConverged:
            if i == 2:
                raise
    names = n.bus["name"]
    return {"buses": [{"id": names[i], "vm_pu": round(float(n.res_bus.vm_pu[i]), 5)} for i in n.bus.index if names[i] != "source"],
            "transformers": [{"id": tid, "loading_percent": round(float(n.res_trafo.loading_percent[i]), 2),
                              "p_hv_mw": round(float(n.res_trafo.p_hv_mw[i]), 4)} for tid, i in tr.items()],
            "cables": [{"id": f"{mid}-cable", "loading_percent": round(float(n.res_line.loading_percent[i]), 2)} for mid, i in lines.items()],
            "grid_import_mw": round(float(n.res_ext_grid.p_mw.sum()), 4)}


if __name__ == "__main__":
    if "--solve" in sys.argv:
        a = json.loads(sys.stdin.read())
        print(json.dumps(_solve(a["net"], a.get("start"))))
        raise SystemExit
    cfg = config("chem_c01")
    r = check(cfg, None, overrides=[{"unit": "P4712", "kw": 11}])
    assert r["start"]["unit"] == "P4712" and r["start"]["terminal_dip_percent"] > 0, r["start"]
    print(json.dumps({k: r[k] for k in ("checks", "start")}, indent=1)[:2000])
    print("ok")
