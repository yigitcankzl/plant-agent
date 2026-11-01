# Assumptions: provenance and engineer confirmation

Every numeric engineering input of a plant is one assumption, and each one carries a source:

| source | meaning |
|---|---|
| `documented` | read from the project documents (basis, report, patent) |
| `datasheet` | from a vendor or site data sheet, or a file the engineer uploaded |
| `muse_default` | drafted by Muse or by a deterministic default (drafts) |
| `assumed` | illustrative or typical value that nobody has checked |
| `engineer_confirmed` | confirmed or entered by the engineer (logged) |

## Where values come from (`plantagent/assumptions.py`)
- `cases/<case>/*.json`, except `case`, `historian_map`, `outcome` and `prefeed`. A value without a source is `assumed`.
- `runs/ws/<case>/drafts/*.json`: drafts for a new plant. The default source is `muse_default`.
- `runs/ws/<case>/inputs/*.json`: uploads. The default source is `datasheet`.

## File contract for drafts and inputs
- A leaf written as `{"value": <number>, "unit": "...", "source": "<one of the sources above, or free text>"}` is one assumption with its own source.
- A plain number inherits the `source` of the nearest enclosing object. Free text is classified: "ILLUSTRATIVE" and "assumed" map to `assumed`, "vendor datasheet" to `datasheet`, "basis.md p. 3" to `documented`.
- List items are named by their `id`, `tag` or `name`.
- An assumption id is `<file>:<dotted.label>`, e.g. `electrical:motors.M-P4711.kw` or `drafts/economics:capex`.

## Confirmation
`POST /api/plant/<case>/assumptions {"id": ..., "value": <number, optional>}`
- Appends a line to `runs/ws/<case>/assumptions_log.jsonl`. The latest line per id wins and marks the value `engineer_confirmed`. The action is also written to the audit chain.
- New values are written back to drafts and inputs files, and to the case files of uploaded projects.
- Shipped demo cases keep their files; the value is taken from the log.

`GET /api/plant/<case>/assumptions` returns `{summary, sources, items}`.

## Uploads
`POST /api/plant/<case>/inputs?kind=motors|curves|datasheet` takes the raw file as the body (`Content-Type: application/octet-stream`, `X-Filename`). Rows are validated before anything is stored.
- **motors.csv:** columns `tag,kw`; optional `voltage_kv,start(dol|soft|vfd),cable_m`. Stored as `inputs/motors.json`.
- **curves.csv:** columns `tag,flow_m3h,head_m`; optional `efficiency_pct,speed_rpm`. At least 3 points per tag, with flow rising. Stored as `inputs/curves.json`.
- **datasheet:** a PDF, stored under `inputs/datasheets/` as a documented source.

`GET /api/plant/<case>/inputs` returns the templates and the stored files.
