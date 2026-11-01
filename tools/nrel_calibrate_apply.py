"""Record a Muse calibration session's proposals on NREL Area 500 as one correction revision (no LLM).

python tools/nrel_calibrate_apply.py <session dir> [answer index]
Every proposal whose changes patch and solve is applied together; the revision names the session and Muse as the author
of the values. Then scores the result with tools/nrel_compare.py."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from plantagent.plant import PlantWorkspace, patch  # noqa: E402
from tools.nrel_compare import compare  # noqa: E402

if __name__ == "__main__":
    session = Path(sys.argv[1])
    ans = json.loads((session / "answers.json").read_text())[int(sys.argv[2]) if len(sys.argv) > 2 else -1]
    w = PlantWorkspace("nrel_ethanol_a500")
    spec, used = w.built["spec"], []
    for p in ans.get("proposals") or []:
        try:
            spec = patch(spec, p.get("changes") or [])
            used.append(p.get("title"))
        except ValueError as e:
            print("skipped", p.get("title"), e)
    titles = "; ".join(t for t in used if t)
    w.correct(spec, "Calibration to the design basis (Muse Wonder session)", user="calibration session",
              reason=f"Values proposed by Muse Wonder in calibration session {session.name} against the design-basis text "
                     f"(report section 3.5.2), not the withheld stream tables: {titles}")
    r = w.revisions[-1]
    print("review", r["review"]["status"], "errors", (r["result_after"] or {}).get("errors", [])[:3])
    print(json.dumps(compare("nrel_ethanol_a500")["summary"], indent=1))
