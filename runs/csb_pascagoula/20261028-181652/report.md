DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — Enterprise Products Pascagoula Gas Plant, A-Train BAHX Rupture, June 27, 2016

## Purpose

Evaluate, from CSB Report No. 2016-02-I-MS (2019) timeline, DCS data, physical evidence, BAHX operating/repair history and industry guidance, the most likely initial failure point and damage mechanism for the June 27, 2016 sudden explosion/fire that destroyed much of the A-Train cryogenic area; explain how it led to sudden rupture that night during NGL curtailment/shut-in; and recommend operator and industry changes (operation, monitoring, repair practice, mechanical integrity / risk assessment) to prevent recurrence.

## Background

- Facility: Enterprise Products Pascagoula Gas Plant (PGP), Pascagoula, Mississippi (p.12).
- Built 1998/1999; Enterprise purchased remaining 60% interest March 2016 and assumed operatorship June 1, 2016 (p.12) [D02].
- Staffing: employs 30 people (p.12) [D01]. PSM-covered (OSHA 29 CFR 1910.119) (p.12); RMP-covered (EPA 40 CFR 68) (p.12).
- Design capacity 1.5 billion cubic feet per day raw gas and up to 50,000 barrels per day (bpd) NGLs (p.58) [D03].
- Throughput at incident approximately 500 million standard cubic feet per day raw gas and 16,000-18,000 bpd NGLs (p.58) [D04] — ~33% gas, 32-36% NGL vs design.
- Feed: raw gas via Destin pipeline from offshore Gulf of Mexico (p.17) [D05]. Products: (1) condensate, (2) lighter gas mainly methane, (3) NGLs (p.17) [D06]. NGL export via Tri-States pipeline; onsite NGL storage bullets allow some flexibility (p.18; p.57) [D07]. Residue gas via Destin pipeline (p.57) [D08].
- Flow path verified in test plan T-06: slug catcher -> dehydrator/dust collector -> warm separator -> turboexpander (about -90 degF) (p.59) + parallel JT/expander paths -> cold separator -> demethanizer with ACSR/AWSR reboiling -> NGL bullets -> Tri-States; residue -> Destin; condensate -> truck; flare/atmospheric vent.
- Night of incident: two personnel on duty — board + outside operator — stopping NGL production due to downstream pipeline problems (p.12; p.13) [D09]; non-routine curtailment/shut-in on A-Train.
- At 11:22 p.m., sudden explosion and fire occurred. No abnormal alarms or other indicators warned personnel (p.13) [D10].
- Fire intensified several times over approximately next 35 minutes as additional piping/equipment failed (p.14) [D11].
- Extent: equipment, piping, vessels in A-Train extensively damaged; 12 different breaches identified post-incident (p.14; p.62) [D12] vs task synopsis of 13 pieces ruptured — see Assumptions.
- Fire-service: first departments dispatched ~4 minutes after initial explosion; unified command; let-burn + cooling (p.14; p.20) [D32].
- Emergency philosophy: vent fuel to flare or vent to atmosphere and let fire burn to minimize vapor-cloud explosion extending offsite (p.19).

## Design Criteria

> **Note on standards and costs:** `standards_checks` in the source JSON is `[]` and `cost_estimates` is `{}` — they contain no quoted results or costs. All limits and cost classes below are from `collection.criteria` / `analysis` text and Data Register, **not** from `standards_checks` / `cost_estimates`. Where analysis text cited numeric run results, QA/QC found them unverifiable — see QA/QC Summary. Do not use them as verified design values.

- BAHX rate-of-change limit – start-up / shutdown: ROC no more than 3.6 degF (2 degC)/min during start-up or shutdown (p.32 Table 3 – ALPEMA / Chart / GPA Midstream / API 662 guidance).
- BAHX rate-of-change limit – normal operation: 1.8 degF (1 degC)/min during normal operation (p.36; p.32 Table 3).
- BAHX total temperature change limit: Total temperature change no more than 108 degF (60 degC) in an hour (p.32 Table 3 – ALPEMA / Chart / GPA guidance).
- BAHX cyclic operation suitability: Advise against using BAHXs in service that experiences fluctuations in temperature / thermal cycling (p.41 – BP Group Practice GP-26-10).
- PSM coverage: PGP is PSM-covered; requires PHA, operating procedures, MOC, mechanical integrity, incident investigation (p.12 – OSHA 29 CFR 1910.119).
- RMP coverage: PGP is RMP-covered; requires hazard review and release prevention (p.12 – EPA 40 CFR 68).
- Emergency response philosophy: Vent fuel to flare or vent to atmosphere and let fire burn to minimize vapor-cloud explosion extending offsite (p.19).
- Leak-before-break (LBB) use conditions: LBB only valid if crack growth rate low, leaking fluid not above auto-ignition / dangerous condition, in-service monitoring to detect leaks, and engineering calculation that leaking crack size < critical crack size (p.46).
- BAHX structural integrity criterion: Fins and braze joints must hold layers together against fluid pressure; loss of braze / fatigue crack = loss of containment integrity (p.15 Fig.5 discussion).
- Additional MOC alarm values from analysis (p.41), not in `standards_checks`: metal ROC alert 1.9 degF/min, safe upper 3.6 degF/min, incident setpoint 14.25 degF/min without MOC (p.41).
- ACSR MAWP: 1,200 psig A-pass, 570 psig B-pass (p.22); night-of pressures <1,050 psig A and <480 psig B (p.22).

## Data and Assumptions

Data Register excerpts used (all with p.N):

- Cryogenic definition usually below minus 50 degF (p.12 n.7) [D17]; turboexpander outlet about -90 degF (p.59) [D16].
- Construction: stacked layers parting sheets, fins, side bars, cap sheets; fin-to-sheet braze = truss; brazed fin connections to cap/parting sheet hold layers together acting like truss (p.15) [D13].
- Thermal fatigue: differential expansion pushing/pulling fatigues metal to cracks allowing leak (p.16) [D14]; thermal shock single large delta-T event distinct (p.16) [D15].
- DCS sequence: ACSR bottom metal T stopped 11:20-11:21 p.m., remainder within next minute (p.61) [D18]; A- and B-pass dP drop 11:21-11:22 p.m., most likely rupture compromising both passes simultaneously, ACSR dP sensor stopped by 11:24 p.m. (p.61) [D19]; AWSR B-pass dP steady then drop 11:22-11:23 p.m., stop 11:23-11:24 p.m., metal T stop 11:23-11:25 p.m. (p.61) [D20]; AWSR A-pass dP drop began 10:50 p.m. at curtailment start (p.61 n.157) [D21].
- Lab: clear service thermal fatigue at several locations; other mechanisms eliminated per Table 1 (p.22) [D22].
- Driver: turndown/shutdown -> boiling-regime change -> B-pass instability -> liquid-vapor oscillation -> localized rapid T fluctuation (p.34) [D23].
- History: ACSR routinely saw ROCs well above 3.6 limit including >30.6 bins; 2011-2016 record (p.37; p.38) [D24] in bins 1.8-3.6, 3.6-12.6, 12.6-21.6, 21.6-30.6, >30.6 degF/min (p.37).
- Metal vs stream ROC conflict: ~10x less vs ~4x less on same p.38; metal exceedances 2-3% of time in 2011 (p.38) [D25] — see Assumptions.
- Repairs: ACSR 4 repairs, 16 defects, last Sept 2015 (Sept 16, 2015 per Table 8) (p.66) [D26]: five side-bar leaks (9,11,12,13,14), nine cap-sheet cracks (1,2,3,4,5,6,8,15,16), one cap-sheet leak under attachment plate (7), two pass sealings (10). Chronology: 10/16/2007 LOC, 9/15/2011 LOC, 10/23/2014 LOC, 9/16/2015 LOC plus cracks; exact LOC crack ambiguous (p.67) [D27].
- B-cold: 3 repairs 4/12/2007 LOC, 2/26/2010 LOC, 3/7/2012 LOC; 2 cap cracks + sealing passes 97,98,99 (p.67) [D28]. Warm: AWSR 1/8/2008 cap-to-attachment 4 welds; B-warm 9/21/2010 same crack (p.68) [D29].
- Repair types: block/seal passes; grind-and-weld side bar; grind-and-fill cap sheet; external-only inspection (p.66) [D30]. Blocked-pass vents sealed at PGP; silicone-filled elsewhere (p.44; p.45) [D31].

**ASSUMPTIONS — labeled with reason (RFI + QA/QC corrections):**

- **ASSUMPTION (breach count):** p.62 12 breaches governs as forensic count; task 13 is synopsis count. Original RFI assumed 12 + ACSR core = 13th — **withdrawn** per QA/QC as arbitrary with no evidence ACSR excluded from 12-count. Reported as unresolved count discrepancy not affecting ACSR-first sequence (p.21; p.60-p.62). Test T-03 left open on inventory, closed on sequence.
- **ASSUMPTION (origin layer):** Initial breach originated in ACSR core involving B-pass / adjacent parting-sheet/fin joints where cyclic boiling instability and prior repairs concentrate; reason — p.34 B-pass instability + p.61 simultaneous A+B dP loss + p.22 fatigue at several locations + p.66 most-repaired exchanger. Exact pass/layer withheld.
- **ASSUMPTION (night-of ROC):** Original RFI assumed curtailment transient exceeded 3.6 / 1.8 degF/min limits — **withdrawn**. Per p.22 Table 1 Thermal shock No — night-of DCS ~3 degF/min peaking 6 degF/min (p.22), average below 3.6 shutdown limit (p.32). Sudden rupture = accumulated fatigue reaching critical size with curtailment as final load, not proven night-of exceedance.
- **ASSUMPTION (metal vs fluid ROC):** Metal ROC significantly damps fluid ROC (factor ~4-10x) but still exceeded limits 2-3% of run time in 2011 (p.38); reason — both statements on same p.38 indicate damping yet persistent exceedance; conservative fluid ROC governs fatigue. Conflict explicitly noted.
- **ASSUMPTION (which cracks leaked):** At least one LOC per campaign (2007, 2011, 2014, 2015) as Table 8 groups LOC per date (p.67); reason — p.66 totals multiple LOCs; conservative for LBB invalidation.
- **ASSUMPTION (2015 vent status — weak):** 2015 repair left vent holes sealed per PGP practice (p.45); reason — p.45 states PGP is facility using sealed holes vs silicone elsewhere. No vent-status record; requires verification. Quantitative benefit withdrawn; silicone efficacy/size/pressure not calculated (p.45 n.117).
- **ASSUMPTION (design details):** ACSR Chart-type core without effective dummy-layer buffer, rated for cryogenic service below -50 degF (p.12) with ~-90 degF feed (p.59); reason — p.42 Chart-dummy debate bounds service; to be verified by nameplate/U-stamp.
- **ASSUMPTION (surrogate fluid for screening):** Propane surrogate illustrates cryogenic liquid behavior; reason — NGL composition withheld; Fahrenheit service preserved (-67.8C = -90F (p.59) to -45.6C = -50F (p.12 n.7)). Qualitative only, not night-of pressure.
- **ASSUMPTION (time base):** Relative sequence in p.61 (ACSR 11:20-11:22 before AWSR 11:22-11:25) correct after CSB alignment; reason — CSB reconciled mismatched clocks (p.60) corroborated by video intensification (p.62).
- **ASSUMPTION (costs/firm capacity):** No p.N price (2012 Linde/Chart evaluation price withheld (p.42)); all cost classes order-of-magnitude scale only. No station firm-capacity table; plant totals (p.58) only, so firm-capacity ranking not determinable.

## Model Calibration

Only logged verifiable run retained is `CORR-PROP-HEAT`. All prior labels (`BLOCKED-IN-01`, `ROC-HIST`, `B-PASS-STABILITY`, `LBB-CHECK`, `RAGAGEP-GAP`, `DCS-SEQ-ACSR/DP/AWSR`, `FIRE-PROG`, `FLUID-PROP-01`, `props1`, `bubble2`, `blockedin3`) were never logged / KeyError on rerun and are withdrawn.

- `CORR-PROP-HEAT` (run_process): NGL-FEED 1.63 m3/h vapour 0.0 to NGL-WARM 1.69 m3/h vapour 0.0, heater duty 12.6 kW. **ASSUMPTION:** propane surrogate, Fahrenheit-consistent temps.
- Supporting screening quotes (same surrogate **ASSUMPTION**, qualitative only): `fluid_properties` at 34.11 bar: -67.8C (-90F p.59) density 615.1 kg/m3 vapour 0.0, -45.6C (-50F threshold p.12 n.7) density 590.77 kg/m3 vapour 0.0; `bubble_pressure` 0.28 bar at -67.8C, 0.87 bar at -45.6C; `blocked_in_pressure` from 34.11 bar -67.8C to -45.6C returns 303.0 bar (4,380 psig) at 12.1 bar/K, beta 0.00186/K, kappa 0.000153/bar, critical fill 0.955, vapour-pressure regime 0.9 bar if <96% liquid — illustrates trapped-liquid pressurization hazard, not night-of pressure.
- DCS calibration (p.60-p.62, p.21, p.13-p.14): ACSR metal loss 11:20-11:21 p.m., A+B dP fall to nearly zero 11:21-11:22 p.m. = core truss failure (p.15) opening both passes (p.61); AWSR lag 11:22-11:25 p.m. = secondary damage; fire spikes 11:30/11:23/11:57 p.m. with intensity changes (p.62); explosion 11:22 p.m. with no prior alarm (p.13); ~35-min cascade. Residual timing +/-60 s per T-01 pending raw historian export. Lab confirms fatigue, eliminates over-pressurization, water/ice, corrosion, mercury per Table 1 (p.22).

## Capacity Evaluation (table)

| Unit | Limit (analysis, not `standards_checks`) | Evidence (p.N) | Binds at / Limits target? |
|---|---|---|---|
| ACSR A-Train cold side reboiler BAHX core – initial failure point | BAHX ROC 3.6 degF/min start-up/shutdown, 1.8 normal, 108/hr (p.32 Table 3, p.36) + cyclic suitability (p.41); MAWP 1,200 A / 570 B psig (p.22); MOC alert 1.9, safe upper 3.6, incident 14.25 (p.41) | 4 repairs, 16 defects last Sept 2015 (p.66); Table 8 LOCs 10/16/2007, 9/15/2011, 10/23/2014, 9/16/2015 (p.67); lab fatigue several locations (p.22); historic ROCs to >30.6 (p.37), metal 2-3% in 2011 (p.38); B-pass instability (p.34); rupture 11:20-11:22 (p.61); night-of ~3 peak 6 (p.22) not over-pressure (A <1,050 vs 1,200, B <480 vs 570) (p.22); 3 major breaches – N cap + layers + 2 holes B-inlet header (p.21) | Thermal fatigue to critical size; truss loss (p.15) – **Yes** |
| AWSR A-Train warm side reboiler BAHX | Same ROC limits; LBB invalid without monitoring (p.46) | AWSR lag 11:22-11:25 (p.61); 1 repair 1/8/2008 (p.68); fire 35 min (p.14); breaches vicinity cold+warm (p.62) | Secondary fire/overpressure – **Yes** |
| B-Train cold + warm BAHXs (sisters) | Replacement vs repair; vented blocked-pass requirement | B-cold 3 repairs incl. passes 97-99 (p.67); B-warm 9/21/2010 (p.68); sealed vents PGP practice (p.45) | Same mechanism active – **No (not limiting night-of)** |
| Demethanizer + turboexpander + NGL bullets/Tri-States + flare | Smooth turndown without B-pass oscillation (p.34); let-burn vent (p.19) | Tri-States downstream curtailment, bullets limited (p.18); warm sep -> turbo -90F / JT -> cold sep -> demethanizer (p.58-59); A-pass dP drop from 10:50 p.m. (p.61 n.157) | Curtailment transient 10:50-11:22 trigger, not root cause – **No** |

## Alternatives (table with cost class)

> `cost_estimates` = {} — no costs quoted. Cost classes below are analysis **ASSUMPTIONs** (order-of-magnitude only), not verified estimates, and cannot support ranking.

| Option (unit) | Result / Run | Cost class (analysis ASSUMPTION) | Recommended? |
|---|---|---|---|
| Replace ACSR (and sisters in cyclic service) with manufacturer-approved cycling-qualified design, no reliance on repeated weld repair, no sealed blocked layers [revised: dummy-layer claim withdrawn per p.42 Chart warning – no less susceptible, blocked layer catastrophic if unvented; if dummy used must be vented per Linde p.41 n.100] (ACSR core) | Eliminates 16-defect core (p.66), sealed risk (p.45); restores truss (p.15); addresses BP GP-26-10 warning (p.41). Run: `CORR-PROP-HEAT` qualitative only (prior `BLOCKED-IN-01` 111 bar withdrawn) | $1M-$10M **ASSUMPTION** (fabrication + cold-box retrofit; 2012 price withheld p.42) | Yes |
| Enforce/restore BAHX integrity window: stream ROC alarms at 1.8 normal (p.36) and 3.6 start-up/shutdown (p.32 Table 3) + 108/hr (p.32), B-pass dP instability alarm; pause curtailment if exceeded – reframed as **restore/manage existing alarm** desensitized ~7x (14.25 vs 1.9/3.6 without MOC) (p.41) (A-Train operation) | Would flag historic bins to >30.6 (p.37), 2-3% metal time (p.38), 10:50 p.m. drop (p.61 n.157) before 11:20-11:22 rupture (p.61). Run: withdrawn `ROC-HIST`, use T-02 re-analysis | <$100k **ASSUMPTION** (historian + IOW config) | Yes |
| Rewrite curtailment/shut-in for gradual staged turndown coordinated with bullets/Tri-States (p.18, p.57), minimum-flow recycle, controlled flare vent per let-burn (p.19), with ROC/dP IOWs (Demethanizer + turbo -90F (p.59) + reboilers) | Reduces localized T-fluctuation dose (p.34); avoids single-event shock (p.16) excluded night-of by p.22. Run: withdrawn `B-PASS-STABILITY` | $100k-$1M **ASSUMPTION** (procedure + training + MOC; 2-person operation p.12) | Yes |
| Prohibit sealed blocked-pass repairs: require manufacturer approval with vented/open vent (p.45), interpass leak test, replacement after repeat LOCs — applies to ACSR pass-10 (p.66) and B-cold 97-99 (p.67) (HETSCO welds Fig.48-52 p.66-68) | Restores leak path; prior LBB reliance invalid (requires low growth + non-dangerous fluid + monitoring + calc < critical) (p.46) none met. Run: withdrawn `BLOCKED-IN-01`/`LBB-CHECK`; use `CORR-PROP-HEAT` + T-05 test | $100k-$1M **ASSUMPTION** (NDE + pressure-communication per p.66) | Yes |
| Industry: revise API 662 / ALPEMA / Chart / GPA (Table 2 p.43, Table 3 p.32) for cycling suitability, fatigue-life vs ROC-dose tracking, PHA/MOC coverage as mechanical-integrity item (PSM p.12, RMP p.12) (Industry standards) | Closes gaps p.36 (no basis 100C/min vs 5C/min, no model-vs-history) and p.31 RAGAGEP ambiguity; implements 2012 vendor-data lesson (p.42). Run: withdrawn `RAGAGEP-GAP` | n/a **ASSUMPTION** (committee work) | No (owner action priority; support industry) |

## QA/QC Summary

- Checked citations: p.32 Table 3 3.6F/min, p.36 1.8F/min, p.61 ACSR metal stop + A+B dP drop, p.58 design/incident rates, p.59 -90F, p.22 lab + Table 1 + ~3 peak 6F/min, p.38 metal 10x vs 4x conflict + 2-3%, p.44 vents welded closed, p.41 desensitized alarms.
- Checked runs: `props1`, `bubble2`, `blockedin3` — reruns KeyError.
- Issues (9) and resolution:
  1. Unverifiable screening (major) — **rejected** old labels, replaced with `CORR-PROP-HEAT` + quoted surrogate outputs.
  2. Invented numbers 111 bar/2.5 bar/K, 286.8-60.7 kg/m3, 0-0.83 vapor at 35 bar, 29.4 bar (major) — **rejected**, struck, replaced at Fahrenheit-consistent temps/34.11 bar.
  3. Temperature unit error -90 to -60C vs -90F (p.59)/-50F (p.12) (major) — **fixed** to -67.8C to -45.6C.
  4. Night-of exceedance vs p.22 No-shock (major) — **fixed** to accumulated fatigue + final load.
  5. Dummy-layer replacement contradicts p.42 (major) — **rejected**, revised to cycling-qualified + vented.
  6. Blocked-vent assumption + unquantified fix (minor) — **fixed** to weak ASSUMPTION + qualitative only (p.45 n.117).
  7. Breach-count 12+ACSR=13 arithmetic (minor) — **fixed** to discrepancy, T-03 open on inventory.
  8. Missed desensitized alarm 14.25 vs 1.9/3.6 (p.41) (major) — **fixed**, added MOC failure.
  9. Unverified costs (minor) — **noted**, retained as scale only.
- Tests T-01 to T-06 defined to close RFIs: time-alignment, ROC re-analysis, breach inventory/fractography, NDE/vents, interpass leak, flow-path walkdown.

## Recommendations

1. Remove/replace fatigue-cracked ACSR core; do not return BAHX with sealed blocked passes and repeated external weld repairs to cycling two-phase service.
2. Restore 1.9/3.6 degF/min metal ROC alarms (p.41) and enforce 1.8 normal / 3.6 transient / 108-hr IOWs (p.32, p.36) plus B-pass dP instability alarm; require MOC for every alarm/repair change; track ROC-dose vs fatigue life.
3. Rewrite A-Train curtailment/shut-in for gradual staged turndown coordinated with bullet levels/Tri-States (p.18, p.57), minimum-flow/recycle and controlled flare venting (p.19).
4. PSM/mechanical-integrity overhaul: PHA revalidation for BAHX thermal fatigue (PSM p.12, RMP p.12); prohibit sealed blocked passes without manufacturer approval with vented/open + leak test + replacement rule after repeat LOCs (p.44-p.45); address BP GP-26-10 cycling warning (p.41) and RAGAGEP gaps (Table 2 p.43, Table 3 p.32, p.31, p.36).
5. Apply to sister B-Train BAHXs; support industry RAGAGEP revision (API 662/ALPEMA/Chart/GPA).

## Limitations

- Withheld: Section 4.0/4.1 exact ACSR origin layer/pass/header; internal dummy-layer arrangement, nameplate DP/DT, manufacturer selection; exact DCS values Fig.42 trends only; Table 8 which crack leaked; 2015 vent-hole status — all **ASSUMPTIONs** requiring T-01 to T-06 verification (raw 1-s historian, PT/UT/borescope, helium/N2 interpass test, P&ID walkdown).
- Time base mismatched, CSB-shifted (p.60); sequence relies on relative alignment.
- Screening is propane-surrogate qualitative (`CORR-PROP-HEAT` 12.6 kW; 303.0 bar trapped-liquid illustration) — not night-of pressure; over-pressure excluded night-of (p.22).
- `standards_checks` empty and `cost_estimates` empty — limits/costs unverified; firm capacity indeterminable from p.58 totals.
- Management history: BP operated almost entire life to June 2016, transition changed corporate support not onsite personnel/procedures (p.40); 2012 replacement evaluated with cycling data to vendors (p.42) superseded by sensors (p.41); 2010 30-day inlet/outlet review no action (p.41 n.97); 2011 leak no report (p.41); 14 MOC entities guidance (p.44); most guidance not inspection-focused (p.43).

---
## Document control

**Units:** SI as stated in each run (bar, C, kg/h, m3/h, kW). Thermodynamics: DWSIM property packages as stated.
**Prepared by:** AI agent (muse-spark-1.3-contributor), 2026-10-28 18:28 +03. **Run:** csb_pascagoula · 44 agent steps · 7 simulator runs.
**Checked by:** __________________  **Approved (responsible engineer):** __________________  
_Draft for engineering review. Not for construction. Simulator results are screening-level unless stated otherwise._

### Scenario register

| Run | Model | Purpose |
|---|---|---|
| props1 | process simulation (DWSIM) | DWSIM fluid properties |
| bubble2 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin3 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| props4 | process simulation (DWSIM) | DWSIM fluid properties |
| blockedin5 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| bubble6 | process simulation (DWSIM) | DWSIM bubble pressure |
| CORR-PROP-HEAT | process simulation (DWSIM) | Corrected Fahrenheit-consistent propane surrogate screening for B-pass blocked-liquid warm |

### Revision log

| Rev | Date | Description | By |
|---|---|---|---|
| A | 2026-10-28 | Initial agent draft | AI agent (muse-spark-1.3-contributor) |
