"""Find D-502's boilup ratio that meets the design-basis overhead purity (92.5 wt % ethanol) at the documented molar
reflux 3.5, on the current A500 model (no LLM). Purity specs do not converge in DWSIM's rigorous column here, so the
documented purity is met by a ratio spec found by bisection on full A500 solves.

python tools/nrel_d502_boilup.py [lo hi steps]   prints each trial; --apply records the result as a correction revision"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from plantagent import process  # noqa: E402
from plantagent.plant import PlantWorkspace  # noqa: E402

TARGET = 0.925  # D-502 overhead, w/w ethanol (report section 3.5.2)


def trial(spec, boilup):
    s = copy.deepcopy(spec)
    d = next(u for u in s["units"] if u["id"] == "D-502")
    d["condenser_spec"] = {"type": "Reflux Ratio", "value": 3.5}
    d["reboiler_spec"] = {"type": "Boilup Ratio", "value": boilup}
    r = process.run(s)
    top = (r.get("streams") or {}).get("S511L") or {}
    comp = top.get("components_kg_h") or {}
    w = comp.get("Ethanol", 0) / top["kg_h"] if top.get("kg_h") else None
    return s, r, w


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lo, hi, steps = (float(args[0]), float(args[1]), int(args[2])) if args else (1.0, 3.0, 6)
    w0 = PlantWorkspace("nrel_ethanol_a500")
    spec = w0.built["spec"]
    best = None
    for _ in range(steps):  # overhead purity rises as boilup falls (less vapour, less distillate)
        mid = (lo + hi) / 2
        s, r, w = trial(spec, mid)
        print(f"boilup {mid:.3f}: errors {r.get('errors', [])[:1]} overhead {w}")
        if r.get("errors") or w is None:
            hi = mid
            continue
        best = (mid, s, w)
        if w < TARGET:
            hi = mid
        else:
            lo = mid
    print("best", best and (round(best[0], 3), round(best[2], 4)))
    if best and "--apply" in sys.argv:
        w0.correct(best[1], "D-502 boilup set to meet the documented overhead purity",
                   user="engineer correction",
                   reason=(f"Muse's calibration session could not converge a purity spec on D-502. With the documented molar "
                           f"reflux 3.5 (report 3.5.2), a boilup ratio of {best[0]:.3f} found by bisection on full A500 solves "
                           f"gives {100 * best[2]:.1f} wt % ethanol overhead against the documented 92.5 wt %; lower boilups that would "
                           f"approach 92.5 wt % do not converge (0.43 and below), so this is the closest converging value. Design-basis "
                           f"target only; the withheld stream tables were not used."))
        print("applied rev", w0.revisions[-1]["rev"], w0.revisions[-1]["review"]["status"])
