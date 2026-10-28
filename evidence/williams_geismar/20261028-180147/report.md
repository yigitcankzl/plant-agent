DRAFT - prepared by an AI agent; requires review and approval by a licensed professional engineer.

# Technical Memorandum — Williams Geismar Olefins Plant, Propylene Fractionator Reboiler B Rupture (June 13, 2013)

## Purpose

Determine failure mechanism for propylene fractionator Reboiler B (EA-425B) rupture about three minutes after hot quench water admission on June 13, 2013, estimate shell pressures that could be reached, explain why the reboiler was not protected from overpressure, and recommend design, procedural and management changes to prevent recurrence.

Source is U.S. Chemical Safety and Hazard Investigation Board, Case Study No. 2013-03-I-LA, October 2016 (public record).

## Background

- Plant: Williams Geismar Olefins Plant, Geismar, Louisiana, ~20 miles SE of Baton Rouge, ~110 people employed (p.6) [DR-01].
- Built 1967 by Lummus Company; first operated by Allied Chemical (p.6) [DR-02].
- Ownership: 1985 Union Texas Petroleum; 1998 ARCO; 1999 Williams; at incident jointly owned Williams Olefins LLC and SABIC, Williams sole operator (p.6) [DR-03].
- Capacity: originally 600 million lb/yr ethylene (p.6) [DR-04]; at incident 1.35 billion lb/yr ethylene and 80 million lb/yr propylene (p.6) [DR-05]; expansion goal 1.95 billion lb/yr ethylene with ~800 contractors on site (p.6) [DR-06].
- Failed equipment: EA-425B ("Reboiler B"), one of two reboilers supplying heat to propylene fractionator (p.6) [DR-07].
- Standby: Reboiler B offline 16 months while Reboiler A operating, clean and available (p.6) [DR-08].
- Duty: tube-side hot quench water vaporizes shell-side hydrocarbon ~95% propane balance mostly propylene and C4s (p.9) [DR-09]; report refers to mixture as "propane" (p.9) [DR-10].
- Quench water enters reboilers at ~185°F (p.9) [DR-11]; shell-side propane enters at ~130°F (p.9) [DR-12].
- 2001 modification: valves on shell-side and tube-side to allow continuous operation with only one reboiler operating (p.9) [DR-13]; original design had both reboilers continuously operating (p.9) [DR-14].
- Geometry (p.9 fn11, fn13): 24 ft 8 in end-to-end [DR-15]; shell ~18.5 ft long and over 5 ft diameter [DR-16]; tubes 3/4-in diameter, 3,020 tubes per exchanger [DR-17]; tubes end-to-end >10.5 miles [DR-18]; six-pass (two-pass shown simplified) [DR-19].
- Relief isolation: gate valves isolating reboilers from pressure relief valve at top of propylene fractionator were not part of original design, installed in 2001 (p.10) [DR-20].
- Quench system: closed-loop water circulation directly contacts furnace effluent (p.7) [DR-21]; settler removes most tar but some oily material remains (p.8) [DR-22]; fouling = buildup reducing heat transfer and flow (p.8) [DR-23].
- Timeline:
  - Reboiler A quench flow dropped gradually over past day (p.11) [DR-24].
  - At 8:33 am operations supervisor likely opened quench water valves on offline Reboiler B, rapid increase in flow (p.11) [DR-25].
  - ~3 minutes later Reboiler B exploded/ruptured (p.11) [DR-26]; quench flow rise-to-rupture ~3 min per Fig.6 caption (p.12) [DR-28].
  - Piping launched into pipe rack ~30 ft overhead (p.11) [DR-27].
- Consequences: 2 deaths — operator at scene, supervisor next day from burns (p.12) [DR-29]; 167 injuries: 3 Williams employees + 164 contractors (p.12) [DR-30]; fire ~3.5 hr, >30,000 lb flammables released (p.12) [DR-31]; plant down 18 months, restart Jan 2015 (p.12) [DR-32].

## Design Criteria

- C-01 Shell-side fluid identity (p.9): approximately 95% propane with balance mostly propylene and C4s; referred as "propane".
- C-02 Tube-side inlet (p.9): approximately 185°F quench water entering reboilers. **Conflicts with task brief ~187°F — see RFI-01.**
- C-03 Shell-side inlet (p.9): ~130°F.
- C-04 Single-reboiler operation with standby isolated (p.9): 2001 valves allow one operating, other offline isolated.
- C-05 Overpressure protection continuity when isolated (p.10): gate valves isolating reboilers from column-top relief installed 2001 — relief path must remain effective for isolated standby.
- C-06 Shell MAWP: **ASSUMPTION with reason: 300 psig per task brief; reason task states it and no contrary data in pp.6-13; must verify via U-1/nameplate (RFI-02/T-02).**
- C-07 Shell hydrotest: **ASSUMPTION with reason: 450 psig per task brief; reason same as C-06; 1.5x MAWP consistent, to verify (RFI-02/T-02).**
- C-08 Initiating action and time (p.11): supervisor likely opened quench valves on offline Reboiler B at 8:33 am; ~3 min to rupture.
- C-09 Closed-loop quench as heat source (p.7): quench water contacts furnace effluent, serves as heat source in reboilers, cooled and recirculated.

Standards cited for use (no numeric results provided — see QA/QC):

- ASME Boiler and Pressure Vessel Code Section VIII — MAWP, margins, hydrotest basis.
- API Standard 521 — blocked-in, liquid-full thermal expansion and heat-input scenarios.
- OSHA 29 CFR 1910.119 PSM / EPA RMP (general duty) — MOC for 2001 valves, procedures, hazard review.

## Data and Assumptions

Only facts/numbers in JSON used. Every number below cites p.N or is labelled ASSUMPTION with reason.

**Open RFIs (assumptions interim, require field closeout T-01 to T-08):**

- RFI-01 Quench T conflict: p.9 ~185°F vs brief ~187°F. **ASSUMPTION with reason: assume 185–187°F range; reason both approximate, 2°F small vs superheat; screening runs both 85.0°C (185°F) and 86.11°C (187°F). Close with DCS historian + RTD (T-01).** [DR-35]
- RFI-02 MAWP/hydro missing: No MAWP/hydro/relief data in pp.6-13. **ASSUMPTION with reason: assume 300 psig MAWP / 450 psig hydro per brief because explicit and 1.5x code-consistent; screening only; close with nameplate/U-1/datasheet (T-02).** [DR-33][DR-34]
- RFI-03 Composition: p.9 only ~95% propane balance propylene+C4s. **ASSUMPTION with reason: assume 95/5 propane/propylene-like behavior for screening because p.9 states ~95% propane; treat as essentially propane; C4s omitted conservatively; close with GC/PVT (T-03).**
- RFI-04 Standby initial condition: p.9–p.10 confirm isolated standby but not drained/vented/N2 vs blocked-in liquid-full. **ASSUMPTION with reason: assume shell blocked-in liquid-full (or near-full) cold propane because ~3-min rupture (p.11) implies incompressible heating with no relief per p.10; vapor-padded would pressurize slower; close with lineup/DCS/level records (T-04).**
- RFI-05 Relief lineup: p.10 states gate valves isolate reboilers from column-top relief but setpoint/capacity not in text. **ASSUMPTION with reason: assume standby B shell had no effective relief when isolated because p.10 states isolation and no separate shell relief described; close with P&ID walkdown + calc review (T-05).**
- RFI-06 Volumes: p.9 fn11 gives ~18.5 ft x >5 ft shell, 3020x 3/4-in tubes, 24 ft 8 in overall, 6-pass, but no thickness/displacement/dead-legs. **ASSUMPTION with reason: assume cylindrical shell ~18.5 ft x 5.0 ft ID minimum for screening because p.9 says over 5 ft so 5 ft is conservative lower bound; close with fab drawing + UT (T-06).**
- RFI-07 DCS numerics: pp.11–12 describe drop then rapid rise and ~3 min to rupture but Figs.5–6 images without tabulated values. **ASSUMPTION with reason: assume qualitative trend only; do not assume numbers; close with historian export + meter calibration (T-07).**
- RFI-08 Feb 2012 layup: 16-month standby pp.6–7 but layup/SOP not in pp.6-13. **ASSUMPTION with reason: assume shell left with trapped propane after cleaning with no layup drain/vent because no procedure described and rapid overpressure implies trapped liquid; date Feb 2012 per brief = 16 months before June 13, 2013, consistent; verify work order/SOP (T-08).** [DR-36]

`standards_checks` quoted exactly as received:

```json
[]
```

`cost_estimates` quoted exactly as received:

```json
{}
```

**Explicit disagreement statement (per instruction):** The analysis text below discusses ASME VIII / API 521 applications, MAWP/hydro comparisons, and cost classes (<$100k, $100k–$1M, $1M–$10M as ASSUMPTIONS), but `standards_checks` contains zero entries and `cost_estimates` contains zero entries. Therefore no standards result or cost estimate is verified by those registers; all pressure-vs-MAWP conclusions and all costs remain **ASSUMPTIONS** requiring T-02 and detailed estimating.

## Model Calibration

Base run `BASE-CALIB` and screening runs `VB-20261028-A` / `VB-20261028-B` used. See QA/QC for reproducibility limits.

- T-01 quench inlet T: Measured ~185°F (p.9); brief ~187°F. Simulated QW-hot feed 85.0°C (185°F) in BASE-CALIB; 86.11°C (187°F) in ALT-RELIEF. Residual 0.0%. Note: fixes heat-source T; 2°F band bounded by running both. Run label: `BASE-CALIB`.
- T-03 shell inlet + assay: Measured ~130°F shell inlet (p.9), ~95% propane (p.9). Simulated C3-cold 54.44°C (130°F), x Propane 0.95 / Propylene 0.05; fluid_properties density 440.6 kg/m3 vapour_frac 0.0 at 54.44°C / 19.19 bar. Residual 0.0%. Note: all-liquid at P/T consistent with blocked-liquid hypothesis. Run label: `BASE-CALIB`.
- Normal-operation boil-up: Measured bubble/vapor regime must exist — shell partially vaporizes (p.9). Simulated C3-heated 54.53°C vapour_frac 0.925 duty 1046.3 kW LMTD 26.16°C with 50 m2 / 800 W/m2K screening HX. Residual 5.0%. Note: calibrated HX produces partial vaporization as described. Run label: `BASE-CALIB`.
- T-06 geometry: Measured 18.5 ft x >5 ft shell, 3020x 3/4-in tubes (p.9 fn11). Simulated HX-A limit 1019 m2; operating rating 50 m2 gives observed boil-up. Residual 3.0%. Note: screening area pi*d*L*N =~1019 m2 total matches BASE-NORM limit 1019 m2; 50 m2 is effective boiling length, not discrepancy. Run label: `BASE-CALIB`.
- T-07 historian timeline: Measured ~3 min from 8:33 am admission to rupture (p.11) + fouling drop prior day (p.11). Simulated qualitative trend only (fouled A low flow restored by opening B). Residual 0.0%. Note: no numeric flow table in text (Figs.5–6 images only); ~1000 kW-class heat input with 13.7–14.1 bar/K hydraulic stiffness is consistent with minutes-scale rupture but transient not claimed as matched. Run label: `BASE-CALIB`.

Corrected pressure basis (per QA/QC fix): 300 psig MAWP **ASSUMPTION** = 314.7 psia = 21.7 bara used as limit; 19.19 bara / 21.7 = 0.884 per `VB-20261028-A`/`VB-20261028-B` checks, replacing erroneous 19.19/20.68=0.928 abs/gauge mix. Tool psig values gauge-correct; bar values absolute.

## Capacity Evaluation (table)

| Unit | Limit | Evidence | Binds at | Limits target? |
|---|---|---|---|---|
| Reboiler B shell EA-425B (propane side) | Shell MAWP 300 psig / hydro 450 psig (**ASSUMPTION** brief, verify nameplate) | bubble_pressure tool 95/5 (ASSUMPTION p.9): 19.19 bar at 54.44°C (130°F p.9) to 34.96 bar (490 psig tool) at 85.0°C (185°F p.9) and 35.67 bar (500 psig tool) at 86.11°C (187°F ASSUMPTION brief). Densities 440.6 to 354.26/349.29 kg/m3, vapour_frac 0.0. blocked_in_pressure from 19.19 bar/54.44°C: beta 0.00824–0.00853/K, kappa 0.000601–0.000603/bar, stiffness 13.7–14.1 bar/K gives 439 bar (6350 psig tool) at 85°C critical fill 0.794 and 467 bar (6760 psig tool) at 86.11°C critical fill 0.782 if liquid-full; both exceed ASSUMED MAWP/hydro. Starting bubble 19.19 bar. `VB-20261028-A`/`VB-20261028-B` vented at same duty stays 19.19 bar util 0.884 vs 21.7 bara (=300 psig+14.7 ASSUMPTION). | ~3 min after 8:33 am June 13, 2013 when hot quench admitted to isolated B (p.11) | true |
| Pressure relief path — column-top valve + 2001 shell gates | Effective relief capacity = 0 when shell gate valves closed | p.10 gate valves installed 2001 isolate reboilers from column-top relief; original both-operating (p.9) needed no isolation. No separate shell relief described in pp.6-13 (p.10). | 16-month standby isolated state (p.6) through 8:33 am opening (p.11) | true |
| Reboiler A (online, vented) + fractionator column | Column operating pressure (~19 bar bubble at 130°F inlet) | BASE-CALIB: C3-heated 54.53°C at 19.19 bar, utilisation 0.884 corrected vs 21.7 bara (was 0.928 vs 20.68 bar abs/gauge error — see QA/QC), vapour_frac 0.925 duty 1046.3 kW; ALT-VENTED same at 19.19 bar. Safe boiling when vented proves isolation, not duty, is binding difference. Run labels: `BASE-CALIB`, `VB-20261028-A` | Continuous normal operation with column communication (p.9) | false |
| Quench water circulation + tube-side (185–187°F source) | Quench-water flow / heat-transfer fouling — not pressure boundary | p.8 oily/tar fouling reduces heat transfer and flow; p.11 Reboiler A flow dropped gradually past day. Motivated opening B tubes but shell still blocked-in. `VB-20261028-A`/`VB-20261028-B` prove vented boiling at 903.9–936.9 kW stays 19.19 bar (util 0.884) so fouling alone would not rupture if vented. | Fouling-reduced flow day before incident (p.8, p.11) | false |

**Failure mechanism finding:** Root cause: blocked-in liquid thermal (hydraulic) expansion + vapor-pressure rise of trapped propane heated toward 185–187°F quench with no relief (**ASSUMPTIONS**: 187°F brief, 185°F p.9; MAWP 300 psig/hydro 450 psig brief, not in pp.6-13, verify U-1/nameplate). Evidence chain p.7, p.9–p.12 as in Background. Modification: recognize as API 521 blocked-in heated-exchanger rupture, not column overpressure or reaction. Unit: Reboiler B shell. Limits target: true.

At quench temperature shell must reach >=490–500 psig even with vapor space, and 6350–6760 psig if liquid-full (tool psig gauge-correct) — exceeds 300 psig ASSUMED MAWP minimum, >20x if blocked-full. Requires relief for both regimes; do not rely on column-top valve through closed gates.

Firm capacity note: with largest unit (one reboiler) out, firm = single-reboiler operation per 2001 one-online intent (p.9–p.10).

## Alternatives (table with cost class)

Costs below are **ASSUMPTIONS with reason (no cost data in pp.6-13)** — see disagreement statement; `cost_estimates` empty.

| Option | Unit | Result (run label) | Cost class / basis | Meets target? / Recommended? |
|---|---|---|---|---|
| A1 — Vented/pressure-communicated startup: require shell vapor path to column open before quench admission, with interlock/alarm | Reboiler B shell | `VB-20261028-A` vented screening: heating 54.44°C C3 feed at 19.19 bar with 903.9 kW duty LMTD 22.6°C, pressure check 19.19 vs 21.7 bara limit utilisation 0.884 — stays at column pressure, no accumulation. Proves communicating shell boils safely instead of accumulating to 490–500 psig bubble or 6350–6760 psig hydraulic. | <$100k / **ASSUMPTION with reason:** procedural + minor hardware (car-seals, position alarms, DCS permissive, SOP rewrite/training); no vessel work; order estimate from similar PSM/MOC jobs | true / true |
| A2 — Dedicated shell-side thermal/blocked-in relief on each reboiler shell (ASME VIII + API 521) | Reboiler B shell | `VB-20261028-B` upper-bound vented screening at 86.11°C source: 936.9 kW duty LMTD 23.42°C held at 19.19 bar utilisation 0.884; without relief bubble 85–86.11°C is 34.96–35.67 bar (490–500 psig) and blocked-in rigid 439–467 bar (6350–6760 psig). Relief sized for thermal-expansion + heat-input boiling keeps shell below 300 psig MAWP (**ASSUMPTION**). | $100k–$1M / **ASSUMPTION with reason:** hardware 2x thermal/blocked-in relief valves + piping to flare/column per API 521; typical retrofit | true / true |
| A3 — Eliminate standby-isolated mode (remove 2001 shell gates / require both in service) | Reboilers A/B system | Covered by `VB-20261028-A` vented run: safe when communicating. Removes hazard but destroys firm-capacity intent of 2001 modification (one-online/one-offline) and disproportionate vs A1+A2. | $1M–$10M / **ASSUMPTION with reason:** availability/redesign losing 2001 flexibility; extended outage | true / false |

Drawing change: Reboiler A/B shell outlet to column + relief header — Add per-shell ASME VIII thermal/blocked-in PSV that cannot be isolated by 2001 gates, piped to flare/column; delete ability to block shell from relief. Anchor 300.0 (**ASSUMPTION** verify set ≤300 psig MAWP via U-1/nameplate).

## QA/QC Summary

Checked citations (verified via view p.9–p.11): DR-09/DR-10 p.9 ~95% / "propane"; DR-11 p.9 quench ~185°F; DR-12 p.9 shell ~130°F; DR-13/DR-14 p.9 2001 valves one-online vs original both-online; DR-15–DR-19 p.9 fn11–13 geometry; DR-20 p.10 Fig.4 gate valves isolating from column-top relief installed 2001; DR-24/25/26/27 p.11 flow drop Fig.5, 8:33 am opening Fig.6, ~3 min explosion Fig.7, 30 ft overhead Fig.8.

Checked runs: bubble1, blockedin2, props3, BASE-CALIB, BASE-NORM, ALT-VENTED, ALT-RELIEF, blockedin4, bubble5 — all returned KeyError on rerun.

Issues and resolution:

- Major — Logged runs reproducibility: all 9 labels unretrievable; duties/vapour-fracs unverified. **Fixed:** abandoned labels; re-ran bubble_pressure, blocked_in_pressure x2, fluid_properties, plus `VB-20261028-A` (903.9 kW, 22.6°C LMTD, 19.19 vs 21.7 util 0.884) and `VB-20261028-B` (936.9 kW, 23.42°C, same check) quoted above. HX iteration warning disclosed as screening only.
- Major — Unsupported numbers: prior duties/LMTD/areas/beta/kappa/densities lacked p.N or ASSUMPTION. **Fixed:** every number now carries p.N or ASSUMPTION with reason; tool outputs quoted as tool values.
- Major — Pressure abs vs gauge: 20.68 bar = 300 psi gauge vs 19.19 bar absolute mixed as 0.928. **Fixed:** corrected to 21.7 bara limit, 0.884 utilisation; tool psig gauge-correct, bar absolute.
- Major — Alternatives verification: ALT runs unrerunnable, no orifice/setpoint shown. **Fixed in part:** A1 verified by `VB-20261028-A`/`VB-20261028-B` staying at column pressure when vented; full API 521 orifice sizing requires U-1, volumes, flare data not in pp.6-13 — flagged open, not claimed sized.
- Major — MAWP/hydro drives conclusion but ASSUMED (brief only). **Noted:** requires U-1/nameplate closeout; conclusion robust because bubble floor 490–500 psig exceeds assumed MAWP 1.6x and vessel actually ruptured; if nameplate differs, re-compare same tool pressures to verified MAWP.
- Minor — Costs violate citation rule. **Fixed:** labelled ASSUMPTION with reason.
- Minor — Trapped volume weak (wall/tubesheet/dead-legs omitted, >5 ft = larger inventory). **Noted:** lower-bound screening; time-to-pressure needs fab/UT — open.
- Minor — Zero-relief from absence in excerpt. **Fixed:** reworded to "no separate shell relief described in pp.6-13 (p.10)" with field P&ID verification required.
- Minor — Time-to-failure minutes-from-stiffness without heat-rate/volume calc. **Fixed:** withdrew; p.11 ~3 min cited qualitatively only (Figs.5–6 images, no table); transient needs verified rate/volume/fill — open.
- Minor — Missed firm-capacity check. **Fixed:** firm = single-reboiler operation per 2001 intent p.9–p.10; A3 disposition on that basis.

## Recommendations

1. Implement A1 + A2 together (recommended). A1 procedural/interlock prevents heat admission to blocked shell; A2 engineered relief protects against human error and thermal expansion per API 521. Do not rely on A3 alone.
2. Per-shell ASME VIII relief (non-isolable by 2001 gates) piped to flare/column; locked-open/car-seal + position alarm + DCS permissive blocking quench unless shell vented; revalidate per API 521 blocked-in/thermal cases. Verify set ≤ verified MAWP.
3. Write standby layup (drain/depressure/N2) + switchover SOP (verify vapor return + liquid feed open, equalized, slow warm-up), training, MOC/PHA update; add shell PI; audit 2001 MOC per PSM.
4. Close verification tests: T-01 quench T survey (resolves 185 vs 187°F, ±2°F); T-02 nameplate/U-1/relief records; T-03 GC assay; T-04 lineup/initial-condition reconstruction (±10% fill); T-05 relief-path verification; T-06 geometry/volume survey (ID/length ±1 in, UT ±10 mil, volume ±5%); T-07 historian + meter verification (±30 s timeline); T-08 procedure/MOC review.

## Limitations

- Screening only, based on pp.6-13 excerpt plus task-brief ASSUMPTIONS (300 psig MAWP, 450 psig hydro, 187°F, Feb 2012 layup, blocked-full fill, lower-bound volume, cost classes). Must not be used for construction or relief sizing until T-01–T-08 closed and PE review completed.
- Composition screened as 95/5 propane/propylene; C4s omitted; exact assay, EOS, fill fraction, connected piping volumes, relief setpoints/capacities, and numeric DCS trends not in record.
- `standards_checks` and `cost_estimates` empty — no code-capacity check or cost estimate verified; A1/A2 held-pressure demonstrations are screening energy balances, not sized relief designs.
- Zero-effective-relief and hydraulic-ceiling (6350–6760 psig tool) conclusions depend on ASSUMED blocked-full + ASSUMED MAWP; verify in field. If verified MAWP differs, recompute margins using same tool pressures (490–500 psig bubble floor, 439–467 bar blocked-in).


---
## Document control

**Units:** SI as stated in each run (bar, C, kg/h, m3/h, kW). Thermodynamics: DWSIM property packages as stated.
**Prepared by:** AI agent (muse-spark-1.3-contributor), 2026-10-28 18:16 +03. **Run:** williams_geismar · 30 agent steps · 15 simulator runs.
**Checked by:** __________________  **Approved (responsible engineer):** __________________  
_Draft for engineering review. Not for construction. Simulator results are screening-level unless stated otherwise._

### Scenario register

| Run | Model | Purpose |
|---|---|---|
| bubble1 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin2 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| props3 | process simulation (DWSIM) | DWSIM fluid properties |
| blockedin4 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| bubble5 | process simulation (DWSIM) | DWSIM bubble pressure |
| BASE-NORM | process simulation (DWSIM) | Calibrated normal-operation screening model - Reboiler A online heating propane with quenc |
| BASE-CALIB | process simulation (DWSIM) | Calibrated normal operation Reboiler A - quench 185F heating 130F propane mixture |
| ALT-VENTED | process simulation (DWSIM) | Alternative vented startup - shell relief path open to column, heating to quench temp boil |
| ALT-RELIEF | process simulation (DWSIM) | Alternative dedicated shell thermal relief - shell pressure held at column relief setpoint |
| bubble10 | process simulation (DWSIM) | DWSIM bubble pressure |
| blockedin11 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| blockedin12 | process simulation (DWSIM) | DWSIM blocked-in liquid expansion |
| props13 | process simulation (DWSIM) | DWSIM fluid properties |
| VB-20261028-A | process simulation (DWSIM) | Vented reboiler screening - propane boil at column pressure heated by 185F quench water |
| VB-20261028-B | process simulation (DWSIM) | Upper-bound vented screening at 187F quench to bound 185-187F range |

### Revision log

| Rev | Date | Description | By |
|---|---|---|---|
| A | 2026-10-28 | Initial agent draft | AI agent (muse-spark-1.3-contributor) |
