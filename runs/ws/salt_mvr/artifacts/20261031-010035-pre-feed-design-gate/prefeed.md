# Pre-FEED design gate

**DRAFT — simulator screening, not approved for construction.**

**Verdict:** NOT ROBUST across 4 stated operating scenarios.

## Operating envelope

| Scenario | Load | Result | Governing check | Utilisation | Mass closure | Basis |
|---|---:|---|---|---:|---:|---|
| Clean design at today's rate | 100% | PASS | V-201 boil-up duty vs heat from the heating steam (2 % closure tolerance) | 0.98 | 0% | US 5,366,514 Table I operating point; E-201 clean U is the illustrative post-clean value in basis.md |
| Clean design at sales target | 120% | PASS | K-201 suction flow vs capacity | 1 | 0% | basis.md request: 3,000 short t/d (+20%) |
| Target with heater fouled back to current U | 120% | FAIL | V-201 heater area needed (BPE included) vs installed | 1.11 | 0% | basis.md equipment ratings: E-201 U 2,000 W/m2K in service |
| Target with five-point existing-compressor efficiency sensitivity | 120% | PASS | K-201 suction flow vs capacity | 1 | 0% | engineering sensitivity around the provisional 75% efficiency; vendor curve required |

Energy closure: not available: boundary streams do not carry enthalpy_kJ_kg

## Preliminary equipment selection

| Tag | Type | Status | Flow margin | Driver margin | Rating source |
|---|---|---|---:|---:|---|
| K-202 | compressor | provisional pass | — | 1.19 | vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating |

Vendor gate still open: guaranteed curve; efficiency/driver; surge/choke or BEP/minimum flow; materials; vibration/noise; mechanical design.



### Preliminary equipment datasheet

Provisional equipment selection only. This is not a vendor datasheet and not a mechanical design approval.

#### K-202 compressor

- Service: compressor
- Inlet: S3001_K202, 115.15 °C, 1.7 bar, phase vapour
- Outlet: S3002_K202, 191.5 °C, 3.08 bar, phase vapour
- Operating flow: to confirm
- Pressure ratio: to confirm; head: to confirm
- Calculated duty: 2.02068 MW
- Assumed efficiency: to confirm %
- Provisional rating: 55 t/h / 2.4 MW
- Rating source: vendor quote to confirm / standard size 55 t/h suction, 2,400 kW shaft at pressure ratio 1.8 (3.08 bar discharge) - proposed rating only, not an existing rating
- Missing vendor information: vendor curve, mechanical design, materials — to confirm
- Status: new equipment, rating to confirm




## Critical-loop dynamics

Not run: no measured dynamic model.

Needed: equipment liquid/vapour holdup; controller action and tuning; valve/drive response; step-test time constant and dead time; trip and permissive logic.

## Change-focused HAZOP and relief screen

| Tag | Deviation | Cause | Consequence | Existing safeguard | Action |
|---|---|---|---|---|---|
| V-201 | High pressure | vapour outlet blocked | vessel overpressure | protected | verify relief load and discharge destination |
| V-201 | High level | outlet restriction/control failure | carryover to compressor | protected | confirm independent high-high trip |
| K-202 | No flow / trip | trip, isolation or surge | loss of production; recycle heating | new equipment: relief and isolation to confirm | confirm anti-surge, trip and restart logic |
| K-202 | High pressure | blocked discharge or control failure | overpressure upstream/downstream | new equipment: relief and isolation to confirm | size relief/depressuring case; check discharge system |
| K-201 | No flow / trip | trip, isolation or surge | loss of production; recycle heating | protected | confirm anti-surge, trip and restart logic |
| K-201 | High pressure | blocked discharge or control failure | overpressure upstream/downstream | protected | size relief/depressuring case; check discharge system |
| D-201MIX | No flow | isolation or failure | loss of process function | not shown on relief scan | confirm alarms, trips and operating response |
| OVERHEAD_SPLIT | No flow | isolation or failure | loss of process function | not shown on relief scan | confirm alarms, trips and operating response |

## Cost and constructability gate

Cost classes on the proposals: <$100k, >$1M, no capex.
Outage required: yes. Exact tie-ins: to confirm on the Rev B line list.

No sourced numerical estimate supplied; these items remain unpriced: installed equipment; piping/tie-ins; electrical and controls; civil/structural; outage production loss.

- Plot space, access and lifting study
- Foundation and nozzle-load design
- Electrical load, starter and cable study
- Vendor lead time and spares
- Materials/corrosion review
- Tie-in list, isolation plan and shutdown window
- Line sizing, supports, stress and hydrotest
- Control narrative and cause/effect update
- Cleaning method, waste handling, inspection and post-clean performance test

## Gate and limitations

- A pass means all stated simulator checks passed in all stated scenarios; it is not mechanical or vendor approval.
- New equipment remains provisional until guaranteed curves and materials are checked.
- The automated hazard register does not replace a multidisciplinary HAZOP or relief-system design.
- Missing inputs stay open; PlantAgent does not invent curves, dynamic constants or costs.
