"""One Muse calibration session on NREL Area 500 against the design-basis text (no withheld stream tables).

python tools/nrel_calibrate_ask.py
Muse returns its calibration as proposals (paths into the spec); tools/nrel_calibrate_apply.py records them as a
correction revision. Spends Muse credit."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plantagent.plant import PlantWorkspace  # noqa: E402

REQUEST = (
    "Calibration session. The as-built A500 model reproduces the ethanol product but misses the design basis elsewhere. "
    "Recalibrate it to the DESIGN BASIS in the data sheet (section 3.5.2), using only the values stated there: "
    "D-502 overhead 92.5 % w/w ethanol and bottoms 0.05 % w/w ethanol at molar reflux 3.5 (today the model fixes a boilup "
    "ratio instead and its overhead is far too wet); D-501 vapour side draw at about 40 wt % ethanol carrying more than 99 % "
    "of the feed ethanol, about 0.3 % of the feed ethanol overhead and about 0.8 % lost in the bottoms; the molecular sieve "
    "removes 95 % of the water, and its regeneration stream (pure-ethanol slipstream plus the stripped water) is about 70-72 wt % "
    "ethanol; beer column bottoms cooled to 47 C in H-512; pressure-filter cake at 35 % moisture. Re-express the column "
    "specifications as purities, recoveries or ratios (Component Fraction, Component Recovery, Reflux Ratio) rather than fixed "
    "molar rates, so the model also holds when the beer feed changes. Fix the sieve and regeneration split and the filter split "
    "to the documented values. Test each change with run_process on the calibrated model, keep only changes that converge, and "
    "return them as proposals (paths into the spec), one per equipment tag, with the run label that shows the result. "
    "This is a model calibration, not a plant change: do not add equipment.")

if __name__ == "__main__":
    w = PlantWorkspace("nrel_ethanol_a500", model="muse-wonder-1.0")
    ans = w.ask(REQUEST)
    print(json.dumps({k: ans.get(k) for k in ("headline", "summary", "cost_usd", "seconds")}, indent=1))
    print(json.dumps([{"title": p.get("title"), "tag": p.get("tag"), "changes": p.get("changes"), "verified": p.get("verified")}
                      for p in ans.get("proposals") or []], indent=1)[:8000])
    print("DIR", w.dir)
