# NREL 2011 ethanol plant: status (2026-11-01)

Source: Humbird et al. 2011, NREL/TP-5100-47764. `tools/nrel_tables.py` extracts the Appendix E stream tables: 154 of 155
streams parsed; 150 close their mass balance within 0.2 %.

## Feasibility per area (DWSIM)
| Area | Verdict | Why |
|---|---|---|
| A100 feed handling | not simulated | solids conveying only |
| A200 pretreatment | feasible, simplified; not built | stand-in reactions work, but the A201/A202 topology (acid water, flash vapour routing) is not readable from the stream tables alone |
| A300 hydrolysis + fermentation | **built by Muse** | fixed-conversion reactors, mass-balanced stand-in stoichiometry (Tables 9-14) |
| A400 enzyme production | feasible, simplified | aerobic conversion reactor |
| A500 distillation + dehydration | **built by Muse** (5th attempt, accepted on replay) | rigorous columns need CO2 off upstream, D-501 modelled from the draw tray down, glycol traces stripped |
| A600 wastewater | feasible, simplified | anaerobic/aerobic conversion of organic lumps |
| A700 storage | trivial | |
| A800 boiler/turbogenerator | not feasible in DWSIM | solid lignin combustion |
| A900 utilities | partial | utility loads only |

## Match against the withheld stream tables (tools/nrel_compare.py)
- A300 (Muse Wonder, $4.30, one build): 8 streams, 35 checks: 26 within 3 %, 33 within 5 %. Beer S501: 451,600 vs
  450,740 kg/h; ethanol 21,229 vs 21,941 kg/h (-3.2 %).
- A500 (Muse Wonder, 18 units, all 10 P&ID tags): 17 streams, 64 checks: 22 within 3 %, 27 within 5 %. Ethanol product
  S515 21,755 vs 21,673 kg/h (+0.4 %), beer column side draw S510 ethanol 21,755 vs 21,691 kg/h. Not calibrated: water in
  the D-502 overhead and the sieve regeneration loop is several times the report's; 0 of 7 duties within 10 %.
- Plant join A300 -> A500 (no LLM): 29 units, 54 streams; S501, S305, S317 joined; S551 torn. A300 and D-501 solve;
  D-502 does not converge on the joined beer with Muse's fixed-rate column specs, so the plant join is not yet a working model.

## Area 500 build history
1. 16 column trials, then an API connection error ($1.78). 2. Killed by a machine shutdown ($0.82). 3. Submitted a 2-unit
model; the review let it through, so a coverage gate now blocks submits missing most P&ID equipment ($3.15). 4. Full
flowsheet, D-502 never converged; root cause: glycol traces (x ~ 1e-7) in the column feed ($8.88). 5. Full flowsheet,
blocked by DWSIM's 0.01 % column mass-balance check ($2.90); after the engine fixes its own last submission re-solved
and passed review and the coverage gate (accepted by replay, no LLM, recorded in model.json "accepted").

## Engine changes
- Rigorous column: several feeds, side draws, Murphree efficiency, partial-condenser vapour rate, solver method, loop
  tolerance (default 1e-4), automatic and reported stripping of non-volatile feed traces when the solver fails.
- Column products report their compound split. The DWSIM worker no longer crashes on compound pairs without NRTL data.
- Plant cases list `areas`; their models join deterministically. Submit is blocked when most P&ID equipment is missing.

## Calibration session (after the merge)
- Muse Wonder calibration session on A500 ($5.84, 777 s, `runs/ws/nrel_ethanol_a500/20261101-140645`), against the
  design-basis text only (no withheld stream tables): every D-502 purity/recovery spec it tried failed to converge; the
  one change that converged (molecular sieve removes 95 % of the water, 18 % regeneration slipstream) is rev 1.
- Engineer correction, rev 2 (`tools/nrel_d502_boilup.py`, no LLM): at the documented molar reflux 3.5, D-502 boilup
  0.47 is the lowest that converges; it gives 89.7 wt % ethanol overhead against the documented 92.5 wt % (0.43 and
  below do not converge).
- A500 after both: 64 checks, 24 within 3 %, 28 within 5 % (was 22 / 27). D-502 overhead S511 29,844 vs 29,213 kg/h
  (+2.2 %, was +61 %); water in the sieve loop S512/S521 +47 % (was +920 %); D-502 reboiler 9.5 vs 6.6 MW (was 60 MW),
  condenser 36.3 vs 27.0 MW (was 85 MW). Still 0 of 7 duties within 10 %; temperatures of the solids streams and the
  D-501 condenser duty are not calibrated.
- Join A300 -> A500: still does not converge. On the joined feed D-502 fails its ethanol mass balance (~95 % relative
  error) at boilups 0.47-0.8, a different failure from the standalone area.

## Spend
$21.83 of the build task's $30; calibration session $5.84 of its $9.
