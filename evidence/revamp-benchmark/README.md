# Published plant-revamp blind benchmark

This benchmark asks PlantAgent to reproduce a published debottlenecking decision from the plant state that existed before the project. The agent receives only `basis.md`, the question and the case configuration. `outcome.json` is the withheld answer key and must never be placed in an agent prompt.

No source PDF or article is redistributed. The public or publisher URL is recorded in each `case.json`. Downloaded documents remain outside Git.

## Accepted cases

| Case | Published source | Equipment and exposed premise | Withheld engineering outcome | Evidence class |
|---|---|---|---|---|
| `revamp_butyraldehyde_t2103` | [Summers, Monaco and Britto, AIChE Spring Meeting paper 112b (2013)](https://www.sulzer.com/en/-/media/files/products/separation-technology/articles/butyraldehyde_tower_capacity_limitations.pdf) | 1.9 m, 90-tray isomer tower; 9.5 to 11.5 t/h | internals, second-liquid-phase control, operating changes and 2011-12 test data | named plant operating history in a major conference paper |
| `revamp_whangarei_cdu` | [Majumder, Mosca and Mahon, PTQ Q1 2013](https://www.sulzer.com/en/-/media/files/products/separation-technology/articles/high_capacity_tray_for_debottlenecking_a_crude_distillation_unit.pdf) | Whangarei CDU-1 C-150; 8,500 to 13,000 t/d | section internals and September 2010 performance test | named refinery field revamp in an established refining journal |
| `revamp_bp_lima_deethanizer` | [Deley and Graf, Oil & Gas Journal, 1 August 1994](https://www.ogj.com/home/article/17211675/random-packing-debottlenecks-refinery-de-ethanizing-stripper) | BP Lima 9 ft stripper; 76,000 to 92,000 b/d | packed-section/distributor/preheat scope and operating results | named refinery field revamp in a long-running trade journal |
| `revamp_toledo_h2_compressors` | [Gupta et al., 29th Turbomachinery Symposium (2000)](https://oaktrust.library.tamu.edu/server/api/core/bitstreams/1d293649-f0a1-4d58-a477-a87dbe4e0904/content) | two LM-3 hydrogen compressors; about 12% more recycle gas | cylinder/valve rerate, achieved flow and power | named refinery field rerate in the Texas A&M proceedings archive |
| `revamp_texas_diesel_charge_pumps` | [Sulzer, Reviving Pump Performance (2020)](https://www.sulzer.com/en/-/media/files/services/rotating-equipment-services/pump-services/white-paper/reviving_pump_performance_a10348_en_201001_web.pdf) | BB5 charge pump; 1,110 to 1,628 gpm | hydraulic-passage/impeller/stage scope and achieved duty | vendor-authored field case; useful but not peer reviewed |
| `revamp_kuwait_cdu_hen` | [Al-Riyami et al., Case Studies in Thermal Engineering 28 (2021) 101030](https://www.sciencedirect.com/science/article/pii/S2214157X21001933) | real Kuwait CDU, 19-exchanger HEN, 93 MW furnace | exchanger relocation/addition, duties, area and economics | open-access peer-reviewed retrofit design; not field commissioning |
| `revamp_michigan_depropanizer` | [Golden and Martin, Oil & Gas Journal, 25 August 2003](https://www.ogj.com/refining-processing/petrochemicals/article/17239602/revamp-troubleshooting-optimize-ngl-depropanizer-operations) | 195 psig NGL depropanizer; 25,000 to 30,500 b/d | tray/feed-zone scope, flood diagnosis and operating outcomes | field revamp and gamma-scan troubleshooting in an established trade journal |

Exact citation counts were not frozen because they change by index and date, and several strong industrial cases are trade papers rather than academic articles. Selection instead records venue and evidence class. The set contains one peer-reviewed open-access design study, two conference/proceedings papers, three named field reports in established process-industry journals, and one vendor-authored field report.

## What the blind runner withholds

For every case:

- `basis.md` contains existing geometry, before operation and the project premise only;
- `outcome.json` contains the engineers' change categories and quantitative after data;
- `case.json` retains the source URL for audit, but a blind runner must pass only the basis and question to the agent;
- `purity.json` is added only when the publication gives a compatible mass-basis criterion. BP Lima reports liquid-volume percent and the Michigan paper does not state the fraction basis, so those values stay in the basis/outcome instead of being silently converted to a DWSIM mass fraction.

The source papers do not always publish complete assays or vendor curves. Each case's `data_note` identifies the resulting scale or property assumptions. A successful score therefore means reproduction of the published decision at screening level, not a certified mechanical design.

## Contamination check

`tests/test_revamp_compare.py` applies the same recommendation-clause redactor used by `plantagent.docs.redact` to every `basis.md`, then checks:

1. no clause is removed by the redactor;
2. none of each answer key's `leak_phrases` occurs in the basis; and
3. no numeric item marked `withheld: true` occurs as a standalone value in the basis.

Current result: **7/7 clean, zero redacted clauses, zero phrase hits and zero withheld-value hits.** Values that are also the public project target are marked `withheld: false`; they are intentionally visible as the premise.

## Deterministic scoring

Run:

```text
PYTHONPATH=. .venv/bin/python tools/revamp_compare.py <case> <worklog.json-or-session-folder>
```

The tool writes `revamp-comparison.json` and a Markdown table. It makes no model call.

1. **Loop status:** `done` only when a worklog explicitly says `done`. A bare session without that completion marker scores `not`, even if it contains a verified proposal.
2. **Change type:** each published category has explicit keywords in `outcome.json`. All required categories found is `match`; some is `partial`; none is `miss`. Optional categories do not change that grade.
3. **After data:** values are read from named engine-check rows and, where declared, `replace_unit.new_rating` or `add_unit` fields. Error is absolute percentage error from the published value. A published range has zero error inside the range and distance to the nearest bound outside it. Missing values remain `not reported`; the scorer does not infer or invent them.

The JSON records the exact row or rating used for every extracted value. There is deliberately no fuzzy LLM judge.

## Rejected candidates

| Candidate | Reason rejected |
|---|---|
| Evonik C4 superfractionator, AIChE 2009 | Open abstract gives an approximate capacity gain but not enough feed, pressure, geometry or before/after operating data for a reproducible model. |
| Anonymous C2 splitter in Sulzer HiFi brochure | Shell/tray counts and purity are shown, but feed, pressure and absolute throughput are missing; too sparse and too close to the existing Norco case. |
| Koch-Glitsch amine absorber capacity example | Advertised gain is quantitative, but the accessible material lacks solvent/feed composition, pressure and packing-bed data. |
| MRPL LPG-amine extraction revamp | Quantitative case, but liquid-liquid extraction is not represented credibly by the current DWSIM layer; a component-separator approximation would predetermine the answer. |
| Singapore condensate-pump MAWP rerate | Pressure-rating change is reported, but no before/after flow, head or system curve is published. |
| Dividing-wall-column revamp brochures | The present process schema has no defensible dividing-wall-column model and the public summaries omit enough internal data that scoring would reward guesswork. |

No benchmark runs or result claims are included here. Those are generated later from blind loop worklogs.
