# WaterTAP reverse osmosis

DWSIM has no reverse-osmosis unit. Seawater RO cases use WaterTAP (NAWI/DOE, IDAES/Pyomo) through `plantagent/ro.py`. DuPont WAVE PRO has no automation API; it is a manual reference only and is not called.

The DWSIM virtualenv (`.venv`) is not used for this. WaterTAP lives in `.venv-watertap`, which is gitignored. The parent process never imports WaterTAP. It keeps one worker (`.venv-watertap/bin/python -m plantagent.ro --serve`) and speaks JSON, the same arrangement as `process.py`.

## Install

```bash
python3 -m venv .venv-watertap
.venv-watertap/bin/pip install --no-cache-dir -r requirements-watertap.txt
.venv-watertap/bin/idaes get-extensions
```

`idaes get-extensions` puts Ipopt in `~/.idaes`, not in the virtualenv.

| Piece | Version |
| --- | --- |
| Python | 3.12.3 |
| watertap | 1.8.0 |
| idaes-pse | 2.13.0 |
| pyomo | 6.10.1 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |
| Pint | 0.24.4 |
| watertap-solvers | 24.12.9 |
| parameter-sweep | 0.2.0 |
| IDAES solvers and function libraries | 3.4.2 20240811 ubuntu2204-x86_64 |

Disk: `.venv-watertap` is 668 MB. `~/.idaes` is 99 MB.

## Reproduction of the seawater RO example

`ro.example()` builds `watertap.flowsheets.seawater_RO_desalination` with the function defaults the packaged test locks: pressure exchanger and a 0D RO. The module's `__main__` sets `RO_1D=True`; this check does not.

Measured on this machine (initialize 1.889 s, then the flowsheet solve plus the costing solve 0.710 s):

| Result | Value |
| --- | --- |
| Recovery | 0.420696 |
| RO inlet / HP discharge pressure | 70.0 bar |
| Permeate TDS | 0.2126 g/L |
| Permeate flow | 468.19 m3/h |
| Specific energy | 3.3917 kWh/m3 |
| HP pump | 1120.5 kW |
| Booster pump | 162.5 kW |
| Boron | not modelled |

Specific energy is WaterTAP's `specific_energy_consumption` (kWh/m3 of product). On this flowsheet it includes zero-order pretreatment and post-treatment electricity, not only the high-pressure pump. The example property list is TDS and TSS.

A 100 m3/h plant built with `ro.run` (one stage, pressure exchanger, 70 bar) solved in 2.6 s: SEC 2.61 kWh/m3, permeate TDS 0.220 g/L, brine leaving at the feed pressure. The same plant with a turbine instead of a pressure exchanger solved at 3.43 kWh/m3 against 5.94 kWh/m3 with no energy recovery. The example reproduction and a flux-limited capacity search together took 12.4 s once the worker was up.

## What the plant model does not represent

- Boron, unless the feed includes it and every stage, including a second pass, sets `B_boron_m_per_s`. Otherwise the result says boron is not modelled.
- Ions other than boron. They are summed into one TDS solute (the example coefficients A = 4.2e-12 m/Pa/s and B = 3.5e-8 m/s, not a vendor datasheet).
- Pretreatment chemistry and post-treatment reactions. A media or cartridge filter is a specified pressure drop and recovery. Chemicals and post-treatment are notes.
- Second-pass concentrate recycled to the first-pass feed. It is an outlet, so a full second pass can show a low plant recovery and a high specific energy.
- Fouling and time-varying A and B. `normalize()` is ASTM D4516 (FilmTec Form 609-02004, U = 3020, differential-pressure exponent 1.4) and runs in-process so plant data can be compared with the model. It does not estimate osmotic pressure.
- A per-element flux profile in the default 0D stage. The lead flux is the feed-end flux and the average is the length average. `resolution: "1D"` discretizes the vessel.
- Temperature change across pretreatment.
- WAVE, and any number that did not come from the solve.

## Build, coverage and review

Cases with `"engine": "watertap"` in `case.json` are built as seawater RO models, not DWSIM flowsheets.

- **Tools.** The builder sees `run_ro` and `ro_capacity` (plus shared reads, `check_coverage`, `report_gap`, `ro_normalize`). It does **not** see `run_process` or `process_capacity`. DWSIM cases keep their existing tool list.
- **Build prompt.** Instructs a full process boundary (intake, pretreatment losses/recoveries, HP pumps, stages/trains, one-train-out, PX/turbine + booster, second pass where documented, post-treatment as notes, permeate and concentrate), every documented rating as a WaterTAP check, `report_gap` for unsupported physics (especially boron without `B_boron_m_per_s`), and at least one design run, one cold/high-salinity run, and a capacity search before `submit_model`.
- **Coverage (`ro_coverage`).** Reads the WaterTAP spec structure (feed, pretreatment blocks, HP pump, stages, ERD/booster, second pass, product/concentrate, post-treatment notes) and the submitted mapping. Post-treatment and chemical pretreatment are **notes**, not simulated chemistry. Grouped P&ID tags can map onto one WaterTAP block.
- **Review (`review_ro`).** Deterministic: solver errors, positive feed, mass/volume balance (feed vs permeate + concentrate + pretreatment losses within 2 %), recovery consistency, pressure order/maxima, finite positive SEC and pump power, finite product TDS, every configured stage present, finite active checks, no check above 100 % at design unless submitted as a failing baseline, boron marked not modelled when coefficients are missing, and explicit second-pass / one-train-out assumptions. Same UI shape as the DWSIM review (`status`, `findings`, `blocking`, `review_status`). An RO spec is never passed to `process.run`, `process.capacity`, `coverage()` or `review_model()`.
- **Saved model.** `model.json` stores the WaterTAP spec and result, `engine: "watertap"`, coverage, review, assumptions, mapping, gaps, model name, cost and elapsed time. `state()`, `capacity()` and `precompute()` replay through `ro.run` / `ro.capacity`.

DWSIM cases are unchanged: same build prompt, tools, `coverage()` and `review_model()`.
