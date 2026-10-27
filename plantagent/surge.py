"""Water hammer (transient) check with TSNet, method of characteristics, on the same network spec as sim.py.

TSNet needs numpy<2, so it runs in its own environment (.venv-surge) as a subprocess:
    uv venv .venv-surge && uv pip install --python .venv-surge/bin/python tsnet "numpy<2" "wntr<1.2" "setuptools<70"
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv-surge" / "bin" / "python"
VAPOUR_GAUGE_M = -10.0  # gauge pressure head at which water column separation (vapour) starts, approx.

SPEC_HELP = {
    "spec": "the run_hydraulics network spec (US or SI); pipes need realistic lengths (>= ~50 ft)",
    "event": "{type: pump_trip, pump: id, closure_s=1.0}. Every listed pump trips at t=0 unless `pumps` lists several ids.",
    "protection": "optional [{type: surge_tank (open) | air_chamber (closed), node: junction id, area_m2, height_m (air_chamber), "
                  "water_m (air_chamber, initial water height)}]. The node must not be a pump's own discharge node: "
                  "add a junction a short pipe (~100 ft) downstream of the pump for it.",
    "wave_speed_mps": "pressure wave speed: ~1000-1200 steel/ductile iron, ~300-450 PVC/HDPE (default 1000)",
    "sim_time_s": "simulated time (default 60)",
}


def run(spec, event, protection=(), wave_speed_mps=1000.0, sim_time_s=60.0):
    payload = json.dumps({"spec": spec, "event": event, "protection": list(protection),
                          "wave_speed_mps": wave_speed_mps, "sim_time_s": sim_time_s})
    out = subprocess.run([str(PY), "-m", "plantagent.surge", "--worker"], input=payload, capture_output=True,
                         text=True, cwd=ROOT, timeout=600)
    if out.returncode:
        raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr.strip() else "surge worker failed")
    return json.loads(out.stdout.strip().splitlines()[-1])


def _worker(a):
    import os
    import tempfile

    import tsnet

    from . import sim
    spec, u = a["spec"], sim._u(a["spec"])
    to_press = (9.81 * 1000 / u["press"])  # metres of head -> spec pressure unit
    with tempfile.TemporaryDirectory() as t:
        inp = os.path.join(t, "m.inp")
        sim.write_inp(spec, inp)
        tm = tsnet.network.TransientModel(inp)
        tm.set_wavespeed(float(a["wave_speed_mps"]))
        dt = min(p.length / (2 * float(a["wave_speed_mps"])) for _, p in tm.pipes()) * 0.9
        tm.set_time(float(a["sim_time_s"]), dt)
        ev = a["event"]
        for pid in ev.get("pumps") or [ev["pump"]]:
            tm.pump_shut_off(pid, [float(ev.get("closure_s", 1.0)), 0.0, 0.0, 1])
        for p in a["protection"]:
            if p["type"] == "air_chamber":
                tm.add_surge_tank(p["node"], [p["area_m2"], p["height_m"], p["water_m"]], "closed")
            else:
                tm.add_surge_tank(p["node"], [p["area_m2"]], "open")
        devnull = open(os.devnull, "w")
        stdout, sys.stdout = sys.stdout, devnull  # TSNet prints progress
        try:
            tm = tsnet.simulation.Initializer(tm, 0, "DD")
            tm = tsnet.simulation.MOCSimulator(tm, os.path.join(t, "res"), "steady")
        finally:
            sys.stdout = stdout
        nodes = []
        for j in spec.get("junctions", []):
            n = tm.get_node(j["id"])
            pmin, pmax, p0 = (float(n.head.min() - n.elevation), float(n.head.max() - n.elevation),
                              float(n.head[0] - n.elevation))
            sep = pmin <= VAPOUR_GAUGE_M
            nodes.append({"id": j["id"], f"steady_{u['press_u']}": round(p0 * to_press, 2),
                          # below vapour pressure the computed number is not physical: report the vapour limit instead
                          f"max_{u['press_u']}": round(pmax * to_press, 2) if not sep else None,
                          f"min_{u['press_u']}": round(max(pmin, VAPOUR_GAUGE_M) * to_press, 2),
                          "vapour_risk": sep, "note": "column separation: min shown at vapour pressure; max after rejoin not modelled" if sep else ""})
    return {"event": ev, "protection": a["protection"], "wave_speed_mps": a["wave_speed_mps"], "time_step_s": round(tm.time_step, 4),
            "nodes": nodes, "screening": "PRE-SCREEN ONLY: pump trip modelled as a 1 s closure without pump inertia (WR2), "
                          "check-valve dynamics or a column-separation model. Confirm surge protection with a full transient model "
                          "(e.g. Bentley HAMMER, KYPipe Surge) before design.",
            "note": "MOC transient (TSNet), sea-level vapour limit about -10 m gauge."}


if __name__ == "__main__":
    if "--worker" in sys.argv:
        print(json.dumps(_worker(json.loads(sys.stdin.read()))))
    else:
        spec = {"reservoirs": [{"id": "wet", "head_ft": 0}, {"id": "top", "head_ft": 100}],
                "junctions": [{"id": "d", "elev_ft": 0}, {"id": "c", "elev_ft": 0}, {"id": "hi", "elev_ft": 60}],
                "pipes": [{"id": "p0", "from": "d", "to": "c", "length_ft": 100, "diameter_in": 18},
                          {"id": "p1", "from": "c", "to": "hi", "length_ft": 4000, "diameter_in": 18},
                          {"id": "p2", "from": "hi", "to": "top", "length_ft": 4000, "diameter_in": 18}],
                "pumps": [{"id": "P", "from": "wet", "to": "d", "curve": [[0, 200], [2500, 150], [4000, 90]]}]}
        bare = run(spec, {"type": "pump_trip", "pump": "P"})
        tank = run(spec, {"type": "pump_trip", "pump": "P"}, [{"type": "air_chamber", "node": "c", "area_m2": 3.0, "height_m": 4.0, "water_m": 2.0}])
        hi_bare, hi_tank = bare["nodes"][2]["min_psi"], tank["nodes"][2]["min_psi"]
        print(bare["nodes"], tank["nodes"], sep="\n")
        assert hi_tank > hi_bare, "an air chamber at the pump must raise the minimum pressure at the high point"
        print("ok")
