# Blind NETL design reproduction (2026-10-29)

Source: NETL, [*Comparison of Commercial, State-of-the-Art, Fossil-Based Hydrogen Production Technologies*](https://netl.doe.gov/projects/files/ComparisonofCommercialStateofArtFossilBasedHydrogenProductionTechnologies_041222.pdf) (2022), Case 2. The source PDF is local at `/home/kizil/Desktop/hackathon/case-data/raw/factory/netl_hydrogen/NETL_H2_Comparison_2022.pdf` and is **not** copied into this repository. PDF page numbers here are physical PDF pages, not printed report pages.

## Method

The agent received only PDF p.96 (the block flow diagram) and the inlet boundaries in each question. PDF pp.97–98 (stream tables), p.104 (CO2 compressor auxiliary power), and p.112 (equipment duties) were withheld as applicable; CO2 stage pressures on p.102 were also withheld. The question gives inlet values taken from the withheld table because a forward design cannot start without inlet conditions. Neither the answer key nor withheld PDF pages were sent to the agent. The leak check searched the *allowed page text* for each answer-key number, including Celsius/MPa representations of T/P: **zero hits** for both cases. Page images were restricted by `Case.page_image` to the same allowed page.

Each model used the same case prompt, DWSIM tools, and 12-step focused `Study.loop`. The final DWSIM run, not a narrative claim or the best earlier run, was scored against the answer key. An errored or missing run scores zero. Temperature was compared in K; pressure in bar absolute; mass and component flows in kg/h; duties in kW. Every metric has equal weight; rates are the fractions within relative ±2%, ±5%, and ±10%. Component mass-flow references are derived from NETL's rounded mole fractions and reported total mass flow, so their last digits are approximate. The run JSONs contain every metric and its source page.

| Section | Model | Valid DWSIM runs | ±2% | ±5% | ±10% | Run |
|---|---|---:|---:|---:|---:|---|
| Syngas cooler, streams 8→9 | Muse contributor | 1 | 8/10 | 8/10 | 8/10 | [result](../../runs/designcheck/netl_syngas_cooler/20261029-085528-muse.json) |
| Syngas cooler, streams 8→9 | Muse Spark Open / Baseten | 1 | 8/10 | 8/10 | 8/10 | [result](../../runs/designcheck/netl_syngas_cooler/20261029-090204-baseten.json) |
| CO2 compression/drying, streams 18+19→20 | Muse contributor | 1 | 5/7 | 5/7 | 5/7 | [result](../../runs/designcheck/netl_co2_compression/20261029-090641-muse.json) |
| CO2 compression/drying, streams 18+19→20 | Muse Spark Open / Baseten | 2 | 4/7 | 4/7 | 4/7 | [result](../../runs/designcheck/netl_co2_compression/20261029-090758-baseten.json) |

At ±10% by variable type, both syngas runs passed P (1/1), total mass (1/1), and component mass flows (6/6), but failed T (0/1) and cooling duty (0/1). CO2 Muse passed T, P, total mass, CO2 mass and compressor power; failed residual water and final aftercooler duty. CO2 Baseten passed T, P, total mass and CO2 mass; failed residual water and aftercooler duty, while pressure-elevation power was **unscorable/failed** because DWSIM reported essentially zero volumetric flow and 0.01 kW through a dense-CO2 pump carrying about 192,001 kg/h. Exact values and error percentages are in the run JSONs.

The initial CO2 attempts with a 3,000-output-token cap produced no `run_process` call in 12 steps (both 0/7); they are retained as [Muse](../../runs/designcheck/netl_co2_compression/20261029-090131-muse.json) and [Baseten](../../runs/designcheck/netl_co2_compression/20261029-090419-baseten.json), **not** silently discarded. The cap was raised to 8,000 for both CO2 retries; the successful syngas runs used 3,000. This is a harness limit, so the initial CO2 zeros should not be interpreted as thermodynamic-model failures.

## What failed, and what this does not prove

- Both syngas models independently assumed a 350 °C shift inlet; NETL stream 9 is 204 °C. Their cooling duties were ~100,749 kW versus the reported 126,944 kW. The excellent component-flow scores mainly reflect conservation of the **given** inlet composition, not successful design inference.
- Both CO2 models assumed roughly 150 bar product pressure, close to NETL's 152.7 bar, and imposed final temperature setpoints. Those T/P matches are *assumptions*, not independently predicted design values. The target 30 °C also equals the supplied stream-18 inlet temperature, making it especially weak evidence.
- Both over-dried the product: 2.25 and 1.13 kg/h H2O versus ~39 kg/h inferred from NETL stream 20. Fixed-split TEG approximations and interstage knockout placement control this result; no TEG solvent circulation or equilibrium design was modeled.
- The final aftercooler duties were 4,495 and 3,016 kW versus NETL's 8,889 kW. Their assumed intercooling and last-stage/pump topology removed more heat before the final cooler. Baseten's 8th pressure-raising device was a liquid pump, while the report describes an eight-stage integrally geared compressor; DWSIM's dense-CO2 volumetric/pump-power output was inconsistent with its mass flow.
- The allowed diagram contains no outlet specifications, stage pressures, exchanger area, utility conditions, or heat-recovery duty. Exact reproduction of those withheld choices is not identifiable from these inputs. The benchmark measures how far an autonomous **assumption-driven** model lands from NETL; it does not validate the plant design, prove a unique flowsheet, establish uncertainty bands, or compare thermodynamic packages fairly. PR-vs-Aspen property-method differences were not isolated.

## Spend and reproducibility

All six attempts together added **$0.01508 Muse** and an **estimated $0.21478 Baseten** to the local usage ledger, below the task caps of $3/$5. Baseten's figure uses the repository's conservative default token price, not an invoice. `MUSE_BUDGET_USD` in the local `.env` was respected; no credentials are committed. Run JSONs and focused Study tool logs are in `runs/`. The local PDF and DWSIM/.NET installation are required to rerun: `python -m plantagent.designcheck --case netl_syngas_cooler` or `--case netl_co2_compression`, optionally `--model baseten:meta-models/muse-spark-open-1026`.

The NETL 2025 power-plant baseline was inspected but not made a third case: these two 2022 Case 2 sections supply matched inlet/outlet stream identifiers and a tractable DWSIM boundary. No WGS or reformer reactor score is claimed; a Gibbs-reactor prototype did not reproduce WGS conversion reliably and was left out of the patch.
