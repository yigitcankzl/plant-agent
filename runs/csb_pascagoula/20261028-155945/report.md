DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — CSB Pascagoula (csb_pascagoula) — A-Train BAHX Rupture, June 27, 2016

**Facility:** Enterprise Products Pascagoula Gas Plant, brazed aluminum heat exchanger rupture, fires and explosions, Pascagoula, Mississippi, June 27, 2016
**Source:** U.S. Chemical Safety and Hazard Investigation Board, Loss of Containment, Fires, and Explosions at Enterprise Products Midstream Gas Plant, Report No. 2016-02-I-MS, 2019 (public record) — https://www.csb.gov/enterprise-pascagoula-gas-plant-explosion-and-fire-/
**Model reference:** muse-spark-1.3-contributor

## Purpose

On the night of June 27, 2016, while operators were curtailing and then shutting in NGL production on A-Train, a sudden explosion and fire destroyed much of the A-Train cryogenic area; task statement cites 13 pieces of piping and equipment ruptured. Using timeline, DCS data, physical evidence, BAHX operating and repair history and industry guidance in the JSON record, identify the most likely initial failure point and damage mechanism, explain how it led to sudden rupture on that night, and recommend operator and industry changes (operation, monitoring, repair practice, mechanical integrity / risk assessment) to prevent repeat.

> **Standards / costs traceability note (required):** `standards_checks` = [] — no entries to quote. `cost_estimates` = {} — no entries to quote. Design Criteria below are from `collection.criteria` (p.32, p.36, p.41, p.12, p.19, p.46, p.15), not independent standards-check results. Costs in Alternatives are ASSUMPTION estimates with reason, not `cost_estimates` values. Where analysis text disagrees with independent checks or prior runs, this memo states the disagreement explicitly instead of picking one — see QA/QC Summary and Limitations.

## Background

- Plant built 1998/1999; Enterprise purchased remaining 60% interest March 2016, assumed operatorship June 1, 2016 (p.12). Employs 30 people (p.12).
- Design capacity 1.5 billion cubic feet per day raw gas and up to 50,000 bpd NGLs (p.58). Throughput at time ~500 million standard cubic feet per day raw gas and 16,000-18,000 bpd NGLs (p.58) — ~33% gas, 32-36% NGL by stated capacities.
- Feed: raw gas via Destin pipeline from offshore Gulf of Mexico (p.17). Products: (1) natural gas condensate; (2) lighter natural gas mainly methane; (3) heavier NGLs (p.17) — condensate + residue gas + NGLs (ethane, propane, butanes, natural gasoline).
- Flow path per `units_on_path`: Offshore feed – Destin → Slug catcher (condensate trucked offsite) → Dehydrator + dust collector → Warm separator → Turboexpander (about -90 degF (p.59)) + parallel JT/expander paths → Cold separator → Demethanizer with ACSR/AWSR reboiling → NGL bullets → Tri-States pipeline; Residue gas → Destin; Flare/vent for emergency let-burn.
- NGL export via Tri-States pipeline; onsite bullets allow some flexibility (p.18; p.57) — capacity limited. Residue gas via Destin (black) pipeline; NGLs via red pipeline (p.57).
- Night of incident: 2 personnel on duty — board + outside — stopping NGL production due to downstream pipeline problems (p.12; p.13) — non-routine curtailment/shut-in of A-Train.
- At 11:22 p.m., sudden explosion and fire. No abnormal alarms or other indicators warned personnel (p.13).
- Fire intensified several times over ~next 35 minutes as additional piping/equipment failed (p.14). Equipment, piping, vessels in A-Train extensively damaged. After incident, 12 different breaches identified (p.14; p.62).
- Fire-service: first departments dispatched ~4 minutes after initial explosion (p.14; p.20); unified command; allow fire to burn out while cooling where feasible (p.14; p.20). Philosophy: vent fuel to flare or vent and let burn to minimize vapor-cloud explosion extending offsite (p.19).
- Cryogenic plant definition: usually below minus 50 degF (p.12 n.7). Turboexpander reduces to about -90 degF (p.59).

## Design Criteria

From `collection.criteria` only (no `standards_checks` to quote):

| Criterion | Source | Value as stated |
|---|---|---|
| BAHX rate-of-change limit – start-up / shutdown | p.32 Table 3 - ALPEMA / Chart / GPA Midstream / API 662 guidance | ROC no more than 3.6 degF (2 degC)/min during start-up or shutdown |
| BAHX rate-of-change limit – normal operation | p.36 - standards summary; p.32 Table 3 | 1.8 degF (1 degC)/min during normal operation |
| BAHX total temperature change limit | p.32 Table 3 - ALPEMA / Chart / GPA guidance (API 662 No) | Total temperature change no more than 108 degF (60 degC) in an hour |
| BAHX cyclic operation suitability | p.41 - BP Group Practice GP-26-10 Guidance on Practice for Heat Exchangers | Advise against using BAHXs in service that experiences fluctuations in temperature / thermal cycling |
| PSM coverage | p.12 - OSHA 29 CFR 1910.119 [citation corrected — see QA/QC] | PGP is PSM-covered; requires PHA, operating procedures, MOC, mechanical integrity, incident investigation |
| RMP coverage | p.12 - EPA 40 CFR 68 [unsupported — see QA/QC] | PGP is RMP-covered; requires hazard review and release prevention |
| Emergency response philosophy | p.19 - PGP emergency response plan | Vent fuel to flare or vent to atmosphere and let fire burn to minimize vapor-cloud explosion extending offsite |
| Leak-before-break (LBB) use conditions | p.46 - LBB methodology discussion | LBB only valid if crack growth rate low, leaking fluid not above auto-ignition / dangerous condition, in-service monitoring to detect leaks, and engineering calculation that leaking crack size < critical crack size |
| BAHX structural integrity criterion | p.15 Fig.5 discussion | Fins and braze joints must hold layers together against fluid pressure; loss of braze / fatigue crack = loss of containment integrity |

Supporting integrity description: stacked layers: parting sheets, fins, side bars, cap sheets; fin-to-sheet braze = truss (p.15); critical fin connections to cap/parting sheet hold layers acting like truss on bridge (p.15).

Mechanisms as stated: differential thermal expansion -> cyclic stress -> fatigue cracks -> leak to atmosphere or between passes (p.16); single large delta-T event = thermal shock distinct from cyclic fatigue (p.16).

**Disagreement to state explicitly:** Review finds PSM citation should be p.40 (As PSM-covered facility required to address 14 elements), not p.12; and 40 CFR 68 RMP coverage is unsupported in available pages — no RMP text found. This memo uses p.40 for PSM and withdraws RMP claim.

## Data and Assumptions

### Data (from `data_register` — quotes abbreviated, p.N retained)

- Staffing, build/operatorship, capacities, throughput, feed, products, export routes, personnel, timing, damage extent, construction, mechanisms, DCS, lab, drivers, ROC history, repairs, vent practice, fire response as listed in Background plus:
- DCS ACSR: bottom metal T stopped 11:20-11:21 p.m., remainder within next minute (p.61); A- and B-pass dP drop 11:21-11:22 p.m. most likely core rupture both passes, dP sensor stop by 11:24 p.m. (p.61).
- DCS AWSR: B-pass dP steady then drop 11:22-11:23, stop 11:23-11:24; metal T stop 11:23-11:25 (p.61). A-pass dP began dropping at 10:50 p.m. when operator began curtailment (p.61 n.157).
- Lab: clear service thermal fatigue at several locations; other mechanisms eliminated per Table 1 (p.22) — Table 1 contents withheld.
- Driver: turndown/shutdown → boiling-regime change → B-pass flow/pressure instability → liquid-vapor oscillation → localized rapid T fluctuation (p.34).
- History: ROC bins 1.8-3.6, 3.6-12.6, 12.6-21.6, 21.6-30.6, >30.6 degF/min (p.37; p.38); Jan 1, 2011-June 27, 2016 normalized to run time (p.38). Metal vs stream ROC conflict on p.38 (see Assumptions).
- Repairs: ACSR 4 repairs, 16 defects, last Sept 2015 (Sept 16, 2015 per Table 8) (p.66): 5 side-bar leaks (9,11,12,13,14), 9 cap-sheet cracks (1,2,3,4,5,6,8,15,16), 1 cap under plate (7), 2 pass sealings (10) (p.66). Table 8 dates 10/16/2007, 9/15/2011, 10/23/2014, 9/16/2015; docs do not state which crack leaked for early repairs (p.67).
- Sisters: B-cold 3 repairs (4/12/2007 LOC, 2/26/2010 LOC, 3/7/2012 LOC) incl passes 97,98,99 sealing (p.67); AWSR 1 repair 1/8/2008 cap-to-attachment 4 welds (p.68); B-warm 9/21/2010 same crack (p.68).
- Repair types: block/seal passes; grind-and-weld side bar; grind-and-fill cap; external-only inspection (p.66).
- Vents: blocked passes with sealed vent holes at PGP; silicone-filled (ventable) elsewhere (p.44; p.45).
- Timestamps did not match; CSB used signals/visual clues for relative shifts (p.60).

### Assumptions — all labelled ASSUMPTION with reason

- ASSUMPTION with reason: 12 primary breaches per p.62 governs, 13th item is ACSR core counted separately; reason CSB forensic count (p.62) more specific than synopsis.
- ASSUMPTION with reason: Initial breach in ACSR core B-pass/parting-sheet/fin joints where cyclic boiling instability + prior repairs concentrate; reason p.34 B-pass instability + p.61 simultaneous A+B dP loss + p.22 thermal fatigue + p.66 most-repaired.
- ASSUMPTION with reason: Curtailment transient imposed rapid cooldown/boiling-regime shift; night ROC rate unmeasured — history of exceedances including >30.6 degF/min bin (p.37-p.38) does not prove 10:50-11:22 p.m. rate; reason Fig.42 raw values not legible, pending T-02.
- ASSUMPTION with reason: Metal ROC damps fluid ROC ~4-10x but still exceeded limits 2-3% of run time in 2011 (p.38); reason both wordings “about 10 times less” and “about four times less” appear in same p.38 paragraph indicating damping yet persistent exceedance, fluid ROC governs fatigue (conservative).
- ASSUMPTION with reason: Multiple LOCs per ACSR campaign (e.g. repairs 13/14/15 all LOC 9/16/2015 per p.67), not one per campaign; reason p.67 groups LOC per date, conservative for LBB invalidation (p.46).
- ASSUMPTION with reason: 2015 ACSR blocked-pass vents left sealed (PGP practice p.45); reason p.45 states PGP is facility using sealed holes, silicone practice described as other/recent.
- ASSUMPTION with reason: ACSR rated for cryogenic service below -50 degF (p.12) with ~-90 degF feed (p.59), without effective dummy-layer buffer; reason p.42 Chart-dummy-layer debate and cryogenic bounds, verify by nameplate.
- ASSUMPTION with reason: Relative sequence ACSR 11:20-11:22 before AWSR 11:22-11:25 correct after CSB time-shift correction (p.60-p.61); reason corroborated by video intensification over ~35 min (p.62). Absolute timing ±60 s pending T-01.
- ASSUMPTION with reason: Model compositions 70/20/10 cold and 20/30/50 hot mol% C1/C2/C3 and pressures/flows (e.g. COLD 50000 kg/h at -40C 40 bar, HOT 25000 kg/h at 10C 30 bar; blocked P1 30.0 bar at -45.6C = -50 degF) are representative; reason bounded by p.17 products, p.57-p.59 flow/refrigeration description, not plant lab data — illustrative direction only.

## Model Calibration

Re-run traceable runs only: **BASE-A**, **CURT-B**. Prior unverified numbers rejected — see QA/QC.

| Measured (p.N) | Simulated (run_label) | Residual / Note | Source | Test that closes it |
|---|---|---|---|---|
| Throughput ~500 MMscf/d + 16,000-18,000 bpd (p.58) vs design 1.5 Bcf/d + 50,000 bpd (p.58) | BASE-A vs CURT-B directional turndown analogue only — mass-volume (kg/h to Bcf/d/bpd) calibration withdrawn | No residual claimed; prior 3% residual withdrawn as unsupported (no MW/density conversion on record) | p.58; p.13; p.18 | T-06 Flow-path walkdown |
| Turboexpander about -90 degF (p.59); cryogenic below -50 degF (p.12) | BASE-A refrigeration boundary matched by cooler setpoint | Exact match by design; validates boundary only | p.59; p.12 | T-06 |
| ACSR metal stop 11:20-11:21 + A+B dP drop 11:21-11:22 (p.61); AWSR drop 11:22-11:23, stop 11:23-11:24, metal stop 11:23-11:25 (p.61); explosion 11:22 no alarm (p.13) | BASE-A core-loss analogue; CURT-B duty fall illustrates hydraulic/thermal precursor direction analogue to A-pass dP drop from 10:50 p.m. (p.61 n.157) | Sequence proves ACSR first; CSB shift corrected (p.60). No alarm finding retained | p.61; p.13 | T-01 time alignment |
| Historical ROC bins to >30.6 degF/min (p.37), 2011-2016 normalized (p.38); metal exceedances 2-3% in 2011 (p.38) vs limits 3.6 shutdown, 108/hr (p.32) and 1.8 normal (p.36) | CURT-B HOT_OUT swing illustrates density/quality transient driving B-pass oscillation (p.34) — steady-state delta, NOT degF/min rate | Chronic loading established; night rate unmeasured | p.37; p.38; p.32; p.36 | T-02 ROC re-analysis |
| ACSR 4 repairs 16 defects last Sept 2015 (p.66-p.67); Table 8 LOC dates 2007/2011/2014/2015 (p.67) | BASE-A blocked-pass analogue: screening 769.0 bar for -45.6C to 10C heating vs operating 30 bar ASSUMPTION — screening only | Most-repaired unit; external-only exam (p.66); types per p.66 | p.66; p.67 | T-04 NDE + T-05 leak test |
| B-cold 3 repairs incl 97-99 sealing (p.67); AWSR 1 repair 1/8/2008 (p.68); B-warm 9/21/2010 (p.68) | BASE-A as sister analogue | Fleet-wide cracking supports BP GP-26-10 advise-against-cycling (p.41) | p.67; p.68; p.41 | T-05 |

**Disagreement to state explicitly:** Analysis text previously claimed BASE-A duty 1149.2 kW LMTD 4.6C, CURT-B 601.8 kW HOT_OUT 29.39C vapour 0.5248, REC-C 552 kW, blocked 835.0 bar, fluid 695 to 182/94 kg/m3 — all returned KeyError on re-run (no log) and are rejected as unverified. Re-run values now used: BASE-A duty 1068.6 kW LMTD 21.37C; CURT-B duty 408.0 kW LMTD 8.16C; blocked 769.0 bar (11140 psig) rise 13.3 bar/K bubble 42.32 bar at 10C; fluid 687.86 kg/m3 at -45.6C to 182.13 kg/m3 + vapour 0.2204 at 10C. Steady-state cannot prove ROC degF/min compliance (p.34 transient, p.37-p.38 rate). Prior -50C (-58F) blocked basis rejected; corrected to -45.6C = -50 degF (p.32 units).

## Capacity Evaluation (table)

| Unit | Limit (collection.criteria) | Evidence / Binds at | Limits_target |
|---|---|---|---|
| ACSR A-Train cold side reboiler (initial failure point p.61-p.62) — run BASE-A / CURT-B | ROC no more than 3.6 degF/min shutdown/start-up, 1.8 degF/min normal, 108 degF/hr total (p.32 Table 3, p.36) | Chronic 2011-2016 exceedance incl >30.6 bin (p.37-p.38); night curtailment from 10:50 p.m. A-pass dP drop (p.61 n.157) to 11:20-11:22 rupture (p.61). BASE-A 1068.6 kW LMTD 21.37C vs CURT-B 408.0 kW LMTD 8.16C directional analogue; B-pass liquid-vapor oscillation per p.34 | false |
| AWSR A-Train warm side reboiler (second failure) | Same ROC limits (p.32, p.36); secondary fire/overpressure beyond design | Steady then drop 11:22-11:23, stop 11:23-11:24; metal stop 11:23-11:25 (p.61) after ACSR fire; first explosion vicinity ACSR/AWSR (p.62). Fire ~35 min (p.14, p.62); 12 breaches (p.62); T spikes Fig.44 (p.62). Single prior repair 1/8/2008 (p.68) | false |
| B-Train cold + warm reboilers (sister BAHXs) | LBB only if low growth, non-dangerous leak, monitoring, leaking < critical with calcs (p.46); sealed vents violate venting | Repeat LOCs 2007/2010/2012 with passes 97-99 sealed (p.67); same cap-attachment cracking (p.68). Sealing types incl closing passes (p.66); sealed at PGP vs silicone elsewhere (p.44-p.45); blocked screening 769 bar vs 30 bar ASSUMPTION | false |
| NGL export via Tri-States + bullets surge + curtailment procedure | PSM PHA/procedures/MOC/MI (p.40 corrected); RAGAGEP Table 2/Table 3 (p.31-p.32) [RMP withdrawn] | Curtailment for downstream problems (p.13, p.18); bullets limited (p.18, p.57); 2 persons non-routine shut-in (p.12-p.13); no alarm before 11:22 (p.13). Metal damped 4-10x (p.38) missed internal fatigue; sensors external only (p.61 Fig.41) | false |
| Flare / vent + emergency response | Emergency vent to flare/atmosphere and let burn (p.19); design for release, not sustained multi-breach fire | Initial release vicinity, ~35 min escalation (p.14); dispatch ~4 min (p.14, p.20); let-burn to minimize offsite VCE (p.19); 30 staff (p.12), 2 on duty (p.13); throughput/design per p.58; products per p.57 | false — **disagreement stated:** prior capacity table marked true for VCE prevention; corrected to false for escalation prevention — no RAGAGEP limit for sustained BAHX shrapnel + multi-breach fire in available pages |

## Alternatives (table with cost class)

Costs are ASSUMPTION estimates (no `cost_estimates` entries); to be verified by estimate. `meets_target=false` means steady-state screening does NOT prove ROC-rate compliance pending T-02.

| Option | Unit | Result (run_label) | Cost class / basis | Rec. / Meets |
|---|---|---|---|---|
| OP-1 Enforce BAHX integrity operating window and automated rate-limited curtailment with minimum-flow protection to keep B-pass wetted | ACSR B-pass / demethanizer reboiler system — run CURT-B | CURT-B vs BASE-A (both re-run traceable): BASE-A duty 1068.6 kW LMTD 21.37C; CURT-B duty 408.0 kW LMTD 8.16C. Directional turndown analogue only. Does NOT prove compliance with ROC no more than 3.6 degF/min shutdown (p.32) and 1.8 degF/min normal (p.36) because steady-state cannot give degF/min rate (p.34 transient, p.37-p.38 ROC). Requires T-02 historian validation. | $100k-$1M — ASSUMPTION with reason: no cost data in pages; DCS logic + IOW alarms + procedure rewrite + training, no major equipment | Recommended true / Meets false |
| MON-2 Continuous thermal-stress monitoring: metal + stream ROC + B-pass dP instability with alarm/shutdown | ACSR + AWSR instrumentation — run CURT-B | Duty fall 1068.6 kW to 408.0 kW illustrates detectable precursor analogue to A-pass dP drop from 10:50 p.m. (p.61 n.157). Triggers at 3.6 degF/min and 108 degF/hr (p.32) and 1.8 degF/min normal (p.36). Metal ROC about 10 times less and about four times less than stream in same paragraph (p.38) with 2-3% exceedance 2011 (p.38) requires both; sensor adequacy pending placement review. | $100k-$1M — ASSUMPTION with reason: no cost data; add/retain metal-T + stream-T + A/B dP historian, ROC alarming using existing types per Fig.41 (p.61) | Recommended true / Meets false |
| REP-3 Prohibit sealing/blocking passes with sealed vent holes; require vented (silicone) design, MOC + FFS, external + internal NDE, replacement after repeat LOC | ACSR repairs 1-16 + B-cold 97-99 — run BASE-A | Screening via blocked_in_pressure tool (ASSUMPTION 20/30/50 mol% C1/C2/C3, P1 30.0 bar ASSUMPTION at -45.6C = -50 degF (p.32 units, p.59 -90 degF context) to 10C): 769.0 bar (11140 psig), rise 13.3 bar/K, bubble 42.32 bar at 10C. fluid_properties same mix: 687.86 kg/m3 at -45.6C to 182.13 kg/m3 + vapour 0.2204 at 10C. Proves sealed layer cannot survive heating; external-only exam (p.66) would not catch. Vent status 2015 unverified pending T-04/T-05. | $100k-$1M — ASSUMPTION with reason: no cost data; procedure + NDE program + spare core | Recommended true / Meets true (screening) |
| DES-4 Replace ACSR (and FFS-review sisters) with cycling-tolerant design or remove BAHX from cyclic reboiler service; revalidate PHA/MOC per PSM (p.40) | A-Train ACSR + fleet — run BASE-A | BASE-A screening analogue (ASSUMPTION feeds: COLD 50000 kg/h at -40C 40 bar, HOT 25000 kg/h at 10C 30 bar, 70/20/10 and 20/30/50 mol%): duty 1068.6 kW. Must tolerate routine bins 1.8-3.6, 3.6-12.6, 12.6-21.6, 21.6-30.6, >30.6 degF/min (p.37) or service change per BP GP-26-10 advise-against-cycling (p.41). Firm capacity (largest unit out) not evaluated: A/B redundancy not quantified. | $1M-$10M — ASSUMPTION with reason: no cost data; cryogenic BAHX + piping/cold-box + PHA revalidation | Recommended true / Meets true |

## QA/QC Summary

- **Checked citations (verified):** D03 design 1.5 Bcf/d + 50k bpd (p.58); D04 ~500 MMscf/d +16-18k bpd (p.58); D10 11:22 no alarm (p.13); D11 ~35 min (p.14); D13 truss (p.15); D16 about -90 degF (p.59); ROC 3.6 +108/hr (p.32); 1.8 normal (p.36); thermal fatigue several locations Table 1 (p.22); B-pass oscillation (p.34); metal vs stream 10x vs 4x conflict +2-3% 2011 (p.38) exists; Table 8 16 defects dates LOC (p.67); sealed vs silicone (p.44-p.45); let-burn VCE (p.19).
- **Checked runs:** BASE-A, CURT-B, REC-C, props3, blockedin4 — re-run audit found REC-C/props/blockedin prior logs missing.
- **Issues and resolution (explicit disagreements fixed or noted):**
  - Major: Logged runs traceability — reruns returned KeyError; prior numbers unverified → **fixed:** rejected old numbers, re-ran BASE-A/CURT-B, dropped REC-C.
  - Major: Base calibration invented compositions/pressures/kg/h with 0-5% residuals, no p.N, no MW conversion → **fixed:** withdrew mass-volume calibration, reframed as illustrative screening with ASSUMPTION inputs.
  - Major: Steady-state used to prove transient ROC compliance/damping → **fixed:** rejected, OP-1/MON-2 meets_target false pending T-02.
  - Major: Blocked -50C unit error + unsupported 30 bar/mix + 835 bar implausible → **fixed:** re-ran correct -45.6C = -50 degF basis to 769.0 bar screening only, inputs ASSUMPTION.
  - Major: Exact origin layer/pass/header/nozzle not in pages; withheld Sec 4.0/4.1, Table 1/App D (p.21-p.22); no crack-size/growth calc → **noted:** ACSR first per p.61-p.62 retained, within-core B-pass/fin downgraded to ASSUMPTION.
  - Major: Night ROC never quantified; history ≠ night proof; no IOW setpoint analysis → **fixed:** night rate marked unmeasured ASSUMPTION pending T-01/T-02.
  - Minor: Metal vs fluid 10x vs 4x conflict (p.38) + truncated sentence → **fixed:** retained both wordings, require dual monitoring.
  - Minor: Repair history understated (multiple LOCs per campaign e.g. 13/14/15 all LOC 9/16/2015, p.67; docs-do-not-state-which-leaked p.67); no leaking<critical calc per p.46 → **fixed:** corrected severity, T-04/T-05 still required, external-only gap (p.66) retained.
  - Minor: 2015 vent sealed assumed, unverified → **fixed:** downgraded to ASSUMPTION pending pick-test/communication T-04/T-05.
  - Minor: 12 vs 13 count + time-shift (p.60); absolute ±60 s not shown; 10 secondaries over ~35 min not mapped (p.14, p.62) → **fixed:** relative sequence retained, absolute + inventory pending T-03.
  - Minor: PSM p.12→p.40 correction; RMP unsupported; costs invented; firm capacity not applied; limits_target subjective → **fixed:** PSM p.40, RMP withdrawn, costs ASSUMPTION, firm capacity unevaluated.

## Recommendations

**Most likely initial point:** ACSR (A-Train cold side reboiler) ruptured first ~11:21-11:22 p.m. June 27, 2016 (p.61); AWSR + others secondary over ~35 min (p.14, p.62). Evidence: ACSR bottom metal stop 11:20-11:21, remainder next minute; A+B dP drop 11:21-11:22 indicating core rupture both passes, stop by 11:24 (p.61); AWSR B dP steady to 11:22-11:23 then drop/stop 11:23-11:24, metal stop 11:23-11:25 (p.61); first explosion vicinity ACSR/AWSR (p.62); timestamps shifted via signals/visual (p.60); no alarm (p.13). ASSUMPTION with reason: 13th count is ACSR counted separately vs 12 breaches (p.62).

**Damage mechanism (root cause):** Thermal fatigue cracking of brazed fin/parting-sheet/side-bar/cap joints (p.15-p.16, p.22) grown over 1998/1999-2016 life (p.12), last repair Sept 2015 (p.66). Lab clear fatigue several locations, others eliminated Table 1 (p.22). Push-pull fatigue→cracks→leak (p.16) distinct from single thermal shock (p.16). Chronic ROCs to >30.6 bin (p.37), 2011-2016 (p.38) vs limits 3.6/108 (p.32) and 1.8 (p.36). ASSUMPTION with reason: B-pass/parting-sheet/fin concentration most plausible per p.34 + p.66; exact layer/header/nozzle unproven without Sec 4.0/4.1.

**Trigger:** 10:50-11:22 (~92 min per p.61 times) curtailment for Tri-States problems (p.13, p.18) with limited bullets (p.18); A-pass dP drop from 10:50 (p.61 n.157); simultaneous A+B loss 11:21-11:22 (p.61) = sudden rupture of pre-cracked core with no warning (p.13). Illustrative CURT-B vs BASE-A 1068.6→408.0 kW direction only; night rate unmeasured ASSUMPTION pending T-02.

**Contributing repair/MI:** Repeat weld/seal + external-only NDE (p.66) to critical; multiple LOCs per campaign (p.67); B-cold passes 97-99 sealing 3/7/2012 (p.67); AWSR/B-warm cap-attachment welds (p.68); sealed vents at PGP vs silicone elsewhere (p.44-p.45); BP/HETSCO/Chart blocking-yes/yes without FFS (p.44); LBB requires 4 conditions + calcs (p.46) never presented. ASSUMPTION sealed 2015 repair per PGP practice (p.45).

**Systemic PSM:** BP control to June 2016, transition changed support not onsite ops/procedures same June 27 (p.40); 2012 replacement considered, exemplar cycling, Chart vs Linde dummy debate Chart no dummy no less susceptible (p.42); GP-26-10 advises against cycling while A-Train service deemed unclear (p.41); 14 MOC entities since 1999 (p.44); RAGAGEP any-one-source (p.31), Table 2/3 (p.31-p.32). Gap: PHA/MOC/MI did not treat cycling+ROC+repeat LOCs as design-limit exceedance under 29 CFR 1910.119 (p.40).

**Operator + industry actions (all recommended):** Implement OP-1 (IOW + rate-limited curtailment, minimum circulation, prohibit B-pass dryout p.34), MON-2 (metal+stream ROC + dP instability alarm/shutdown), REP-3 (vented-only blocked layers, MOC+FFS, internal NDE, replacement rule; invalidate LBB without monitoring p.46), DES-4 (replace ACSR/FFS sisters or remove BAHX from cycling; PHA revalidation; share data via ALPEMA/Chart/GPA/API 662 p.31-p.32). Retain let-burn + flare venting for VCE prevention (p.19) but add automated depressuring/isolation on leak/dP-instability to limit 35-min progression; review staffing/procedure for non-routine shut-in (p.13, p.18).

**Verification tests required:** T-01 DCS/video alignment ±60 s ACSR before AWSR; T-02 per-minute ROC histograms bins 1.8-3.6 to >30.6 vs 3.6/1.8/108 limits; T-03 P&ID breach inventory 12 vs 13 with fractography; T-04 NDE + vent pick-test + nameplate/dummy drawings; T-05 interpass pressure-communication/helium leak; T-06 P&ID walkdown + curtailment procedure + bullet levels.

## Limitations

- Withheld Sec 4.0/4.1 exact breach layer/pass/header/nozzle; Table 1 + App D fractography withheld (p.21-p.22) — within-core origin remains ASSUMPTION.
- No raw DCS values (Fig.42 trends only); night ROC rate, absolute timing, and IOW setpoints unverified — pending T-01/T-02.
- Metal vs fluid attenuation 10x vs 4x on same p.38 contradictory; sensor placement adequacy unevaluated.
- Table 8 ambiguity which crack leaked (p.67); vent status of 2015 pass-10 repair unverified; no leaking vs critical calc per p.46; T-04/T-05 not done.
- 12 vs 13 reconciliation, 10-secondary progression mapping, A/B-Train firm-capacity redundancy, design pressures/temps, manufacturer selection, and costs all unevaluated or ASSUMPTION — no `standards_checks` or `cost_estimates` entries to validate screening (BASE-A/CURT-B 1068.6/408.0 kW, 769.0 bar) which are illustrative only.


---
## Document control

**Units:** as stated in each run. **Elevations:** feet, datum as shown on the source drawings (not re-surveyed).
**Prepared by:** AI agent (muse-spark-1.3-contributor), 2026-10-28. **Run:** csb_pascagoula · 43 agent steps · 8 simulator runs.
**Checked by:** __________________  **Approved (PE, seal):** __________________  
_Draft for engineering review. Not for construction. Simulator results are screening-level unless stated otherwise._

### Scenario register

| Run | Model | Pumps | Flow (mgd) | Purpose |
|---|---|---|---|---|
| BASE-A | process simulation (DWSIM) | - | - | Screening analogue of A-Train cold-side reboiler steady duty at normal |
| CURT-B | process simulation (DWSIM) | - | - | Illustrative turndown analogue - half throughput to show duty and outl |
| props3 | process simulation (DWSIM) | - | - | DWSIM fluid properties |
| blockedin4 | process simulation (DWSIM) | - | - | DWSIM blocked-in liquid expansion |
| REC-C | process simulation (DWSIM) | - | - | Alternative with minimum-circulation recycle to keep ACSR B-pass wette |
| blockedin6 | process simulation (DWSIM) | - | - | DWSIM blocked-in liquid expansion |
| props7 | process simulation (DWSIM) | - | - | DWSIM fluid properties |
| bubble8 | process simulation (DWSIM) | - | - | DWSIM bubble pressure |

### Revision log

| Rev | Date | Description | By |
|---|---|---|---|
| A | 2026-10-28 | Initial agent draft | AI agent |
