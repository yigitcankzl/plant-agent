# Memo: Vacuum-salt plant with vapour recompression evaporator (US 5,366,514 flowsheet)

2026-10-31 19:34 +03 · DRAFT, not approved

**Decision asked for:** Can the plant make 3,000 short tons of salt per day instead of 2,500 (+20%)? What limits it first, and what is the most economical way to get there?

**Recommendation:** Do not approve yet: 3 changes to reach 120 % of today's throughput - (1) Clean the main circulating heater back to its clean performance; (2) Add a small parallel vapour compressor K-202; (3) Hold purge-heater steam at today's rate by trimming the overhead split. The process changes pass in DWSIM; the electrical screen fails 8 checks (section 6.1b): resolve the supply first. Failed discipline gate(s): robustness, electrical (section 6.1c).

**Result:** At 120 %, existing plant: 3 limits over 100 % (highest K-201 compressor suction flow vs capacity 120 %); with the changes: all modelled process limits within 100 % (highest K-201 compressor suction flow vs capacity 100 %). Discipline screens outside the process model: 5 checks over their limit (section 6.1c). Simulated maximum throughput: 100.1 % → 120.1 % of today.

- (1) Clean the main circulating heater back to its clean performance - cost class <$100k
- (2) Add a small parallel vapour compressor K-202 - cost class >$1M
- (3) Hold purge-heater steam at today's rate by trimming the overhead split - cost class no capex

**Risk:** no second-opinion disagreement recorded. Relief findings on changed equipment: 2.

**Measure next:** Clean heat transfer coefficient actually achieved on E-201 after cleaning (documented 2,500 W/m²K is marked ILLUSTRATIVE); Whether the purge evaporator may boil off less per tonne of purge (no minimum boil-off, outlet concentration or disposal limit is documented); Circulation rate and brine temperature rise through E-201 at 120% (not in the calibrated model); Installed capacity of purge feed valve 5001/FV-301.

Full MOC file with Rev A/Rev B drawings and PSSR checklist (17 items) attached. Audit head `4209d50bcb7b`.
