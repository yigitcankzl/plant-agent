# Limits and honesty

## Caveats of the headline results
- **Norco (real plant):** the flood result follows mostly from Muse's assumed tray capacity (factor 1.85, vendor to confirm; Muse's own sweep put the minimum near 1.80), the uncertainty run varies other inputs but not that factor, and Muse names generic high-capacity tray vendors as examples; the model's distillate ethane is 0 ppm where the plant ran at 487 ppm, so separation was matched to hydraulics, not to the product analysis, and the reflux margin is optimistic; the server verified the design at today's feed composition; the 69 wt % premise appears only in Muse's own runs; the feed-tray move was missed; and Muse's text cites the paper and tray vendors, so training-data exposure is possible. Earlier runs reported a 65 % flood "match" with Shell's 64.7 % under a flow scaling we have since corrected; we withdrew it. Details: [`evidence/real-plant-norco/`](../evidence/real-plant-norco/README.md).
- **BASF C02:** The column's duty is Muse's assumption (the drawing gives none), and the drawing already contains a 600 mm column section (KX 2750) next to the 500 mm chamber, so the 600 mm shell is less of a discovery than it looks. This case shows the drawing-to-simulator path works; it does not show Muse found a real plant's bottleneck.
- **Red team:** A harsher stress set (1.25x the target with two or three deviations stacked, beyond any credible single-jeopardy case) broke it 8 of 8 (flood 116–118 %); the loop answered with a 700 mm shell and ended done ($1.59), which is over-design against an unrealistic attack, shown only to demonstrate the loop. Temperatures now move by at most ±15 °C, not a percentage of °C.

## General

- **Illustrative and synthetic inputs are labelled where they appear.** Labelled data includes:
  - the chem_c01 data sheet;
  - salt ratings the patent does not give, and its one-line diagram;
  - the salt historian, which is **SYNTHETIC**;
  - fouling prices;
  - RO membrane coefficients.
- **The model's calibration table** compares measured values with the solved model. Some of those values are model inputs, and the table marks which.
- **"Verified" means process-verified.** Other disciplines are shown next to it as gates, and an electrical or robustness fail is never hidden by a process pass.
- **DWSIM is steady state.** Valve and pipe calculations are incompressible-liquid screens. The solve scales exchanger U from one test point; the ht/fluids check computes U from geometry and flags any disagreement.
- **Surge is a pre-screen.** TSNet has no pump inertia or column separation.
- **The gravity profile has no open-channel step method.**
- **Costs are AACE Class 5, with no contingency.**
- **Drafted discipline files are screening values.** Their check rows say "draft (assumed values)"; the start-up check uses typical inertia and load curves until vendor data is uploaded.
- **No vendor curves, no rigorous dynamics, no multidisciplinary HAZOP, no relief sizing.** Everything PlantAgent produces is a draft for a licensed engineer.
