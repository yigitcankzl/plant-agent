"""Ask the Freeport blind question with Muse (costs money; run deliberately). python tools/freeport_ask.py [model]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plantagent import llm  # noqa: E402
from plantagent.plant import PlantWorkspace  # noqa: E402

Q = ("VIP-18 was isolated for relief-valve testing and left blocked in. What happens to its pressure over the following "
     "days, when does it exceed design, and what should have prevented it? Show the pressure history as a chart.")
w = PlantWorkspace("freeport_lng_2022", sys.argv[1] if len(sys.argv) > 1 else "muse-wonder-1.0")
usd0 = llm.spent()
a = w.ask(Q)
print(json.dumps({k: a.get(k) for k in ("headline", "summary", "cost_usd")}, indent=1)[:3000])
print("proposals:", [(p.get("title"), p.get("verified"), p.get("unverified_reason")) for p in a.get("proposals") or []])
print("artifacts:", [(x.get("kind"), x.get("title")) for x in a.get("artifacts") or []])
print("spent this ask:", round(llm.spent() - usd0, 3), "dir:", w.dir)
