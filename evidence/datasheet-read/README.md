# Vendor data sheet read by Muse vision

**Source** (not redistributed; see `SOURCE.txt`): a public vendor pump performance data sheet, 3 pages, for a 475 GPM 8" 75 HP seven-stage submersible turbine (curve 475SR60F86-0786). It was published as Exhibit F of an Oregon State University bid.

**Path:** Upload inputs → *Equipment data sheet or vendor curve* (PDF or image) → `plantagent/datasheet.py`.
1. Muse Spark Open (Baseten) reads up to three pages into a fixed JSON schema: each value with its unit, page and printed label, plus 5–8 points read off the drawn head-flow curve. The PDF text layer is passed along so digits come out exact.
2. Python converts the units and runs plausibility checks:
   - efficiency is between 0 and 1;
   - curve flow rises and head falls;
   - the rated point lies on the curve within 10 %;
   - shaft power is within 30 % of ρgQH/η.
   A reading that fails any check is refused.
3. The engineer checks the table, enters the plant tag and confirms. Only then is the reading written through the typed-upload path (`inputs/curves.json`, `inputs/motors.json`), so the checks use it ahead of case files and drafts. The source note keeps the sheet name, pages, model and who confirmed it.

## Printed vs extracted (`osu_475SR.read.json`)

| Field | Printed on the sheet | Muse read | In working units |
|---|---|---|---|
| Rated flow (p. 1) | 500.0 USgpm | 500 USgpm | 113.56 m³/h |
| Rated head (p. 1) | 435.0 ft requested, 437.3 ft actual | 435 ft, "Head, rated (requested)" | 132.59 m |
| Efficiency (p. 1) | 79.98 % | 79.98 % | 0.7998 |
| Shaft power, rated (p. 1) | 69.02 hp | 69.02 hp | 51.47 kW |
| Motor (model line) | 75 HP | 75 hp | 55.93 kW |
| Speed (p. 1) | 3450 rpm | 3450 rpm | 3450 rpm |
| MCSF (p. 1) | 348.2 USgpm | 348.2 USgpm | 79.08 m³/h |
| Head max., shut-off (p. 1) | 726.6 ft | 726.6 ft | 221.47 m |
| Curve (p. 2), drawn | shut-off about 727 ft, rated point 500 gpm / about 437 ft, BEP about 80 % | 7 points, 0–690 gpm; 500 gpm → 438 ft, 80 % | 0–157 m³/h; 113.6 m³/h → 133.5 m |

- **Checks:** all 5 pass. ρgQH/η gives 51.3 kW against the printed 51.5 kW. The curve gives 133.5 m at the rated flow against the rated 132.6 m.
- **Not read:** Muse listed "Motor rating" and "Power, hydraulic" as unreadable. It did read the 75 HP motor from the model line, but labelled it "Motor rating", so the engineer must check that label against the sheet.
- **Defects found on this sheet and fixed in code:**
  - Muse returned whole axis titles as curve units, e.g. "USgpm | Head - ft | …". Units are now matched by whole tokens of the first segment.
  - Muse wrote prose in the tag field. A tag is now kept only if it looks like a plant tag.
- **Cost:** $0.040 on Baseten (8,153 in, 7,042 out tokens). No Meta-hosted model was called.

**End to end:** the confirmed reading was applied to chem_c01 as tag P4711, then removed. `drafts.case_file("chem_c01", "curves.json")` returned the vendor curve, anchored at 113.6 m³/h / 133.5 m / 80 %, with minimum flow at 0.70 of rated (the MCSF) and the basis "vendor data (uploaded): vendor data sheet osu_475SR …, page(s) 1, 2; read by Muse vision …". The motor went into the electrical file the same way.
