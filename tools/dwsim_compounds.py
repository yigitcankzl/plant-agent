"""List DWSIM databank compounds whose name matches any of the given words (case-insensitive).
python -m tools.dwsim_compounds ethanol glucose xylose ..."""
import sys

from plantagent.process import _dwsim

mgr = _dwsim()
sim = mgr.CreateFlowsheet()
names = sorted(str(k) for k in sim.AvailableCompounds.Keys)
print(len(names), "compounds in the databank")
for w in sys.argv[1:]:
    hits = [n for n in names if w.lower() in n.lower()]
    print(f"{w}: {hits[:12]}")
