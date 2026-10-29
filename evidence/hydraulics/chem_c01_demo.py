"""ILLUSTRATIVE valve rating only; never modifies the committed chem_c01 model or operating data."""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from plantagent import process


model = Path(__file__).resolve().parents[2] / "runs/ws/chem_c01/model.json"
spec = copy.deepcopy(json.loads(model.read_text())["spec"])
valve = next(u for u in spec["units"] if u["id"] == "47123/C1")
valve["cv_rated"] = 35  # illustrative US Cv; no valve datasheet rating is given in the case
spec["limits"] = {}  # isolate the valve: existing thermal/pump/utility limits can bind earlier

run = process.run(spec)
cap = process.capacity(spec)
print("ILLUSTRATIVE ONLY: 47123/C1 assumed Cv=35, equal-percentage, 10-90% travel")
print("Current:", run["units"][valve["id"]])
print("Valve-only capacity:", cap["capacity_multiple"], "x;", cap["limited_by"])
print("At 18.0 m3/h current feed, this corresponds to", round(18 * cap["capacity_multiple"], 2), "m3/h.")
