# Pre-FEED design gate evidence

`plantagent.prefeed` is a deterministic gate around the existing PlantAgent record. It does not ask a model to judge
its own work. The selected verified changes are applied to the current process spec, every operating-envelope row is
re-solved, and a robust pass requires every stated limit to pass in every scenario.

The `salt_mvr` replay uses the previously verified clean-E-201, parallel-K-202 and purge-split design. At 120% load it
passes while clean. Returning E-201 to the documented in-service fouled U fails: required heater area is about 9,794 m²
against 8,800 m² installed. K-202 operates at about 49.5 t/h and 2.05 MW against provisional 55 t/h and 2.4 MW ratings;
these are screening margins, not a vendor selection. The report leaves guaranteed curves, surge/choke, materials,
mechanical design, exact tie-ins and numerical cost open.

Boundary mass closes in the replay. Energy closure is deliberately unavailable because process streams do not yet
carry `enthalpy_kJ_kg`. The salt case has no measured holdup/control step-test constants, so its dynamic section says
`not run` and names the required data. The FOPDT calculation itself is unit-tested with sourced constants and limit
crossing. The change-focused hazard rows are an automated preparation aid, not a team HAZOP or API/ISO relief design.

Reproduce without a paid API call:

```bash
.venv/bin/python -m plantagent.prefeed salt_mvr
.venv/bin/python -m unittest tests.test_prefeed -v
```
