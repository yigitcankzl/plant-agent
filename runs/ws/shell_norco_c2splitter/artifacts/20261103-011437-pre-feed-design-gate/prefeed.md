# Pre-FEED design gate

**DRAFT — simulator screening, not approved for construction.**

**Verdict:** ROBUST PASS across 2 stated operating scenarios.

## Operating envelope

| Scenario | Load | Result | Governing check | Utilisation | Mass closure | Basis |
|---|---:|---|---|---:|---:|---|
| today | 100% | PASS | PV-1767 Fair flood fraction vs limit | 78% | 0% | current throughput |
| target | 125% | PASS | PV-1767 Fair flood fraction vs limit | 98% | 0% | case target |

Energy closure: not checked: the solver does not report enthalpy on the boundary streams

## Discipline impact register

| Discipline | Status | Impact | Evidence |
|---|---|---|---|
| Process | pass | design reaches 125 % (max 127 %, re-solved now) | DWSIM re-solve of the combined design on the current model |
| Mechanical | not affected | no new physical equipment | proposal calculation and provisional ratings |
| Electrical | not affected | no new driver identified | constructability gate |
| Piping Utilities | open | no calculation adapter: tie-ins, line sizing, supports and utility headers remain open for PV-1767 | proposal topology (no engine for this discipline) |
| Controls | open | no calculation adapter: control narrative, split/load-sharing control, cause & effect and permissives remain open for PV-1767 | proposal topology (no engine for this discipline) |
| Process Safety | open | no calculation adapter: change-focused HAZOP, relief case and isolation for the changed equipment remain open for PV-1767 | proposal topology (no engine for this discipline) |
| Civil Structural | open | no calculation adapter: plot, access, lifting and foundations remain open for PV-1767 | proposal topology (no engine for this discipline) |
| Robustness | fail | draft (assumed values): operating envelope 1/2 scenarios pass (fails: Target, feed +10 %) | DWSIM solves of the pre-FEED operating envelope |

## Decision-changing evidence

No decision-changing field input was identified from the recorded changes.

## Change portfolio

| Change | Role | Verified | Capacity | Cost class | New equipment |
|---|---|---|---:|---|---|
| Retray PV-1767 with high-capacity trays | standalone target | yes | 127.5% | not stated | — |
| Combined proposed design | combined envelope | yes | 125.0% | not stated | — |

not ranked: sourced numeric cost, outage and energy values are required

## Preliminary equipment selection

No new physical equipment in the selected design.

## Critical-loop dynamics

Not run: no measured dynamic model.

Needed: equipment liquid/vapour holdup; controller action and tuning; valve/drive response; step-test time constant and dead time; trip and permissive logic.

## Change-focused HAZOP and relief screen

| Tag | Deviation | Cause | Consequence | Existing safeguard | Action |
|---|---|---|---|---|---|

## Cost and constructability gate

Cost classes on the proposals: not stated.
Outage required: no identified outage work. Exact tie-ins: 0.

No sourced numerical estimate supplied; these items remain unpriced: installed equipment; piping/tie-ins; electrical and controls; civil/structural; outage production loss.


## Commissioning acceptance

Status: **OPEN** against scenario target.

No solved acceptance check maps to the changed equipment; define the acceptance measurements before issue.

## Gate and limitations

- A pass means all stated simulator checks passed in all stated scenarios; it is not mechanical or vendor approval.
- New equipment remains provisional until guaranteed curves and materials are checked.
- The automated hazard register does not replace a multidisciplinary HAZOP or relief-system design.
- Missing inputs stay open; PlantAgent does not invent curves, dynamic constants or costs.


## Economics and uncertainty

### Economics (ILLUSTRATIVE prices; order of magnitude)

- draft (assumed values): Capex ≈ $0k (class 5: $0k–$0k) plus unpriced items (replace PV-1767): capex is a lower bound; product price not given: margin, payback and NPV open (energy and utilities $0k/yr). All prices ILLUSTRATIVE.

| Proposal | Stated class | Factored capex | Check |
|---|---|---|---|
| Retray PV-1767 with high-capacity trays |  | $0 + to price: replace PV-1767 |  |

- Added Process feed: 552 t/d × 330 d; product margin $0/yr (solved 1.250 × base, capped at the 125% target; energy from dwsim solves (design at 125% vs today at 100 %)).
- Outage for tie-ins/cleaning: 2 d → $0 (muse_default shutdown for a tie-in or exchanger clean).
- Payback None years; NPV $0 (capex band: $0 to $0).

### Uncertainty of the design (Monte Carlo over assumed and illustrative inputs)

- Target 125% met in 92% of 48 samples; max throughput P10/P50/P90 127% / 127% / 128%; most often limited by PV-1767: Fair flood fraction vs limit (100%); biggest driver feeds.FEED.P_bar (assumed).
- Method: Latin hypercube, 48 samples (seed 20261101), uniform ± band per input kind; each sample re-solved (dwsim): capacity bisection plus the solve at the target; 48 of 48 samples solved.

| Input | Kind | Base | ± band |
|---|---|---|---|
| units.PV-1767.dP_bar | assumed | 1.703 | 10 % |
| feeds.FEED.P_bar | assumed | 25.5 | 10 % |
| feeds.FEED.T_C | assumed | -9.5 | 10 % |

- PV-1767: Fair flood fraction vs limit at the target: load P10/P50/P90 98% / 98% / 99%.
