# Decision file: Unit 47 product cooling and storage (DEXPI reference P&ID C01)

**Status: DRAFT for engineering review, not approved.** Prepared 2026-10-29 11:13 +03 by PlantAgent from the working model.

**Question:** Sales wants +20% throughput (18.0 to 21.6 m3/h). Can the unit do it? Which equipment limits first, and what is the cheapest fix that works?

**Result at 120 % of today's throughput (re-solved in DWSIM for this file):** all stated limits within 100 %.

## 1. What changes and why

| Rev | Change | Reason | Proposed by | Applied |
|---|---|---|---|---|
| Rev 1 | Cooling water to H1007 flow: 20 → 27 m³/h | decision-file test: Raise H1007 cooling water to 27 m3/h | muse-spark-1.3-contributor | 2026-10-29T11:12:12+0300 |
| Rev 2 | Chilled water to H1008 flow: 15 → 18 m³/h | decision-file test: Raise H1008 chilled water to 18 m3/h | muse-spark-1.3-contributor | 2026-10-29T11:12:35+0300 |
| Rev 3 | T4750 tank working volume: 20.8 → 22.1 m³ | decision-file test: Raise T4750 working level to 22.1 m3 | muse-spark-1.3-contributor | 2026-10-29T11:13:00+0300 |

## 2. Limits before and after, at 120 % (DWSIM, re-solved now)

| Equipment or stream | Check | Before | After | Value after | Limit |
|---|---|---|---|---|---|
| H1007 heat exchanger | area needed for hot outlet 35 C | 106 % | 81 % | 37.76 m2 | 46.8 m2 |
| P4712 outlet (product leaving the unit) | temperature vs design | 103 % | 96 % | 23.9 C | 25 C |
| T4750 tank | residence time | 103 % | 97 % | 62.09 min | 60 min |
| H1007 outlet to T4750 | temperature vs design | 101 % | 96 % | 33.5 C | 35 C |
| P4711 pump | head vs rated | 88 % | 88 % | 10.54 m | 12 m |
| P4712 pump | flow vs rated | 88 % | 88 % | 43.86 m3/h | 50 m3/h |
| P4711 pump | flow vs rated | 86 % | 86 % | 21.6 m3/h | 25 m3/h |
| Chilled water to H1008 | flow vs 90 % of available supply | 83 % | 100 % | 18.0 m3/h | 18.0 m3/h |
| P4712 pump | shaft power vs motor | 81 % | 81 % | 6.09 kW | 7.5 kW |
| H1007 heat exchanger | installed area vs frame | 78 % | 78 % | 46.8 m2 | 60 m2 |
| Cooling water to H1007 | flow vs 90 % of available supply | 74 % | 100 % | 27.0 m3/h | 27.0 m3/h |
| H1007 heat exchanger | cold-side pressure drop vs available | 50 % | 86 % | 0.858 bar | 1.0 bar |

## 3. Drawing

Redlined P&ID: `redline.svg` (revision clouds at H1007, H1008, T4750).

## 4. Relief protection (P&ID relief scan)

- H1007 MN side: no relief on this P&ID. no relief device reachable Heated side that can be blocked in.
- H1007 WK side: no relief on this P&ID. no relief device reachable (lines leave the drawing: check the connecting P&ID) Heated side that can be blocked in.
- H1008 MN side: isolatable. relief 47125/SpringLoadedGlobeSafetyValve only through 47126/C7: if one is closed the side has no relief Heated side that can be blocked in.
- H1008 QS side: no relief on this P&ID. no relief device reachable (lines leave the drawing: check the connecting P&ID) Heated side that can be blocked in.
- T4750 MN side: no relief on this P&ID. no relief device reachable
- T4750 ? side: no relief on this P&ID. no relief device reachable

- The changes are operating changes; the relief scan reads the drawing, so its findings above are unchanged by them and still need closing.

## 5. Field checks and assumptions

- No field checks were raised in the answer.
- Assumption (model): Site datasheets supersede P&ID where stated: P4711 rated 25 m3/h at 12 m, motor 2.2 kW, min 8 m3/h, NPSHr 2.5 m used; P&ID 200 m3/h/10 m/60 kW is template error per P&ID data_quality warning.
- Assumption (model): P4712 P&ID 420 m3/h/84 kW is same template error; site max stroke 50 m3/h + motor 7.5 kW used, P&ID DesignPressureHead 40 m retained (no site head given), PSV set 6 barg from P&ID valve set_pressure + site confirmation.
- Assumption (model): T4750 P&ID DN20000x4 m (=1257 m3) inconsistent with 26 m3 nominal per data_quality warning; site nominal 26 m3 used, working volume 20.8 m3 at current 80% level per Current operation row (tank volume_m3 is working volume).
- Assumption (model): H1007/H1008 U=600 W/m2K fouled 2024 test used at current flows (U_ref [18,20] and [22.5,15] m3/h); clean 900 W/m2K not used - normal fouled operation.
- Assumption (model): H1007/H1008 installed area 46.8 m2 from P&ID DesignHeatTransferArea; H1007 frame limit 60 m2, CW available dP 1.0 bar and supply limits 30/20 m3/h (90% planning margin enforced by simulator) from site datasheets.
- Assumption (model): Product 7 mol% ethanol modelled as Water 0.93 / Ethanol 0.07 mole, NRTL package for polar liquids.
- Assumption (model): T4750 modelled as well-mixed tank at 1.013 bar; two inlets (H1007 product + H1008 recirc) combined in MIX_TANK mixer upstream (DWSIM tank has one inlet); residence_basis sDispatch (product leaving for good) per 60-min QC requirement.
- Assumption (model): Discharge branch modelled as splitter fixing recirc branch 22020 kg/h (=22.5 m3/h) letting dispatch take rest, reproducing stroke/recirc operations; PSV line 47125 excluded (standby relief, check_coverage relief_path, no normal flow).
- Assumption (model): 47124 suction trim and 47126 isolation ball valves lumped as fully open (no dP); only flow-carrying control valves 47123/C1, 47127/C1, 47141/C1 modelled explicitly with P&ID tags.
- Assumption (model): No H1008 dP_ref given in data sheet so none imposed (never invent); 47141/C1 dP 0.3 bar assumed small outlet loss to close chilled-water pressure balance (utility return not measured).

## 6. Second opinion (Muse Spark Open, answered independently)

Status: **partly**.
- Differs: limiting equipment: H1007, H1008, T4750 vs H1007, T4750
- Differs: feeds.s47140.m3_h: only the main model changes it
- Differs: verified in DWSIM: H1007, H1008, T4750 vs H1007, T4750
- Agrees: feeds.s47130.m3_h: 27.0 vs 27.0
- Agrees: units.T4750.volume_m3: 22.1 vs 22.1
- Agrees: reaches the target: yes vs yes

## 7. Pre-startup safety review (PSSR) checklist (generated from the changes)

- [ ] Verify the cooling water to h1007 can deliver 27 m³/h at header pressure, and that the branch control valve can pass it.
- [ ] Measure the pressure drop across H1007 at the new flow (model: cold side 0.858 bar, hot side 0.417 bar) and compare with the available differential.
- [ ] Confirm the cooling water to h1007 return temperature stays within the utility system's limit at the new duty.
- [ ] Confirm H1007's relief protection is unchanged by the new duty (see the relief scan section).
- [ ] Verify the chilled water to h1008 can deliver 18 m³/h at header pressure, and that the branch control valve can pass it.
- [ ] Confirm the chilled water to h1008 return temperature stays within the utility system's limit at the new duty.
- [ ] Confirm H1008's relief protection is unchanged by the new duty (see the relief scan section).
- [ ] Confirm the high-level alarm and trip on T4750 leave margin above the new working volume of 22.1 m³; update the level setpoint in the operating procedure.
- [ ] Update the P&ID, equipment datasheets and the operating procedure for every change above.
- [ ] Brief the operators on the new setpoints before start-up.
- [ ] Record the first 24 h of operation at the new throughput and compare with the model's predicted values in this file.

## 8. Sign-off (DRAFT: not approved)

| Role | Name | Signature | Date |
|---|---|---|---|
| Process engineer |  |  |  |
| Operations |  |  |  |
| Process safety (MOC) |  |  |  |
| Approver |  |  |  |

## 9. Reproducibility

- Model: v2-calibrated built by muse-spark-1.3-contributor on 2026-10-28 15:46; P&ID coverage missing connections: 0
- Audit-chain head hash: `14220a889ff646d443f2f9662a090331bce0bfcc79cca5e3d3c403243ffce743` (chain intact: True)
- Code version: 648a410; simulator: DWSIM (headless) via plantagent.process
- Values in sections 2 and 7 were recomputed when this file was made; re-run `python -m plantagent.decision chem_c01` on the same revisions to reproduce them.
