"""Generate the SYNTHETIC historian export for the chem_c01 demonstration unit (there is no real plant behind the DEXPI
reference P&ID, so there is no real historian). Each sample is a DWSIM solve of the agent-built model with daily swings
in product flow and cooling-water temperature, an imposed slow fouling drift on H1007, and measurement noise.
Seeded, so it is reproducible:  python tools/make_synthetic_historian.py
"""
import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from plantagent import process  # noqa: E402
from plantagent.plant import patch  # noqa: E402

OUT = ROOT / "cases" / "chem_c01" / "historian_synthetic.csv"
DAYS, STEP_H = 30, 2
U0, U1 = 640.0, 585.0  # imposed H1007 overall coefficient drift over the window (fouling), W/m2K

TAGS = {  # tag: (stream id, quantity) in the agent-built model
    "FI-47121 product flow (m3/h)": ("s47121", "m3_h"),
    "TI-47122 H1007 product in (C)": ("s47122", "T_C"),
    "TI-47123 H1007 product out (C)": ("s47123a", "T_C"),
    "FI-47130 cooling water flow (m3/h)": ("s47130", "m3_h"),
    "TI-47130 cooling water supply (C)": ("s47130", "T_C"),
    "TI-47131 cooling water return (C)": ("s47131", "T_C"),
    "TI-4750 T4750 / dispatch (C)": ("sDispatch", "T_C"),
    "FI-47140 chilled water flow (m3/h)": ("s47140", "m3_h"),
    "TI-47141 chilled water return (C)": ("s47141", "T_C"),
}


def main():
    spec = json.loads((ROOT / "runs" / "ws" / "chem_c01" / "model.json").read_text())["spec"]
    rng = random.Random(47)
    rows = []
    for i in range(DAYS * 24 // STEP_H):
        t_h = i * STEP_H
        day = t_h / 24
        flow = 18.0 * (1 + 0.03 * math.sin(2 * math.pi * (t_h % 24) / 24) + rng.gauss(0, 0.01))
        cw_T = 25.0 + 2.0 * math.sin(2 * math.pi * ((t_h - 9) % 24) / 24) + rng.gauss(0, 0.2)
        U = U0 + (U1 - U0) * day / DAYS
        s = patch(spec, [{"path": "units.H1007.U_W_m2K", "value": round(U, 1)}, {"path": "feeds.s47130.T_C", "value": round(cw_T, 2)}])
        r = process.run(s, flow / 18.0)
        if r["errors"]:
            continue
        row = {"time": f"2026-09-{1 + int(day):02d}T{int(t_h % 24):02d}:00"}
        for tag, (sid, q) in TAGS.items():
            v = r["streams"][sid][q]
            row[tag] = round(v + (rng.gauss(0, 0.15) if q == "T_C" else v * rng.gauss(0, 0.01)), 2)
        rows.append(row)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["time", *TAGS])
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, len(rows), "samples")


if __name__ == "__main__":
    main()
