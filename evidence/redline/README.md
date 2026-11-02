# Engineer's redline

An engineer can upload a photograph or image of a P&ID with red annotations, review Muse Wonder's interpretation, and send the confirmed design through the same proposal verifier and discipline-check adapter used for Muse's designs.

**No live vision read has been run.** Development and browser tests use fake recorded-shaped responses. Model spend for this task: **USD 0**.

## Try it

Start the server on an unused local port:

```sh
WEB_ALLOW_RUNS=1 .venv/bin/python -m plantagent.web --port 8781
```

Open `http://127.0.0.1:8781/redline.html?case=salt_mvr`, or use **Engineer's redline** next to Ask in the plant workspace. A real read needs a configured Muse key and incurs usage under the existing budget cap. Engine verification needs the same installed engines as other proposals.

1. Upload a PNG/JPEG of the marked-up sheet (20 MB / 25 megapixels maximum).
2. Read the red ink with Muse Wonder. The image, equipment/stream tags and current model are supplied to vision. The prompt restricts the interpretation to `path`, `replace_unit`, `add_unit` and `reroute` changes.
3. Inspect the verbatim ink, attached tag, confidence, unreadable details and validation errors. All interpretations remain visible, including invalid ones. Tick items to keep; edit their structured JSON when needed. Unticked items are recorded as rejected.
4. Confirm selected changes. The complete edited set is validated again against the current model. Existing limits still cannot be raised by a plain path edit; physical changes require their usual evidence.
5. Check both designs. The engineer's confirmed set is one combined proposal passed to `PlantWorkspace.verify()`. When it verifies, `designchecks.checks_for_design()` runs on an isolated answer record. The saved Muse featured design uses the same adapter in a separate comparison workspace. Rows are aligned by check identifier, with status, numbers and source in both columns.
6. If the engineer's design verifies and the case has an SVG, open its Rev B drawing. The existing `revb.from_workspace()` renderer is reused. Confirming/checking never applies a plant revision.

## Stored records and API

Runtime records are written only when the feature is used; no demo workspace or case records were edited for this feature.

`runs/ws/<case>/redline/<content-hash>/` contains:

- `image.png`: bounded, normalised upload used by vision;
- `read.json`: `{id, model, spec_hash, items, unreadable, errors, status}`; each item has `{index, ink, tag, confidence, change, unreadable, errors, valid}`;
- `confirmed.json`: `{id, spec_hash, items, changes, rejected, user, reason, status, hash}`;
- `comparison.json`: `{id, key, confirmation_hash, engineer, muse, answer, muse_headline, drawing_url}`;
- `engineer/` and `muse/`: separate engine-result caches, so comparison gates and uncertainty results do not overwrite the featured design's cache.

The read cache is keyed by image, equipment/stream tags, model, current spec and prompt. Every confirmed item is appended individually to the existing hash-chained audit log, with its original ink, edited change and confirmation hash; a final event records the selected and rejected lists. This uses the audit log rather than pretending design changes are scalar assumptions. A model change after the read or confirmation requires a new read/review. Reopening a saved redline restores the edited confirmation and its selection.

| Request | Payload / response |
|---|---|
| `POST /api/plant/<case>/redline` | `{image_b64}` → `{job}`; poll existing `/api/job/<job>` for `answer` containing the read |
| `GET /api/plant/<case>/redline/<id>` | stored `read.json` |
| `GET /api/plant/<case>/redline/<id>/image.png` | stored normalised image |
| `POST /api/plant/<case>/redline/<id>/confirm` | `{items:[{index, change?}], reason?}` → confirmed list; omission of `change` keeps the read value |
| `GET /api/plant/<case>/redline/<id>/check` | `{engineer:[check rows], muse:[check rows], answer, ...}` |
| `GET /api/plant/<case>/redline/<id>/drawing.svg` | verified engineer's Rev B SVG when supported |

All POSTs use the existing JSON-only, same-origin and access controls. The upload route additionally requires `WEB_ALLOW_RUNS=1` before reserving a paid job. Confirmation and comparison make no Muse call. All Muse access in this module is behind `_muse()`, which tests replace. An unavailable engine yields an open verification row and no verified drawing.

## Verification

`tests/test_redline.py` uses a synthetic salt workspace and fake vision response: “E-201 clean to U 2,500”, an incomplete “add parallel pump P-101B”, and an unknown tag. It checks that invalid items remain listed, engineer edits are revalidated, rejected items are retained, the audit chain verifies, the real proposal verifier is called with fake solver results, both design adapters run, the saved Muse answer stays unchanged, stale models are refused, and upload/origin/spend boundaries hold.

`tools/ui_smoke.js` stubs the upload job, read, confirmation and comparison endpoints. It verifies the image, invalid-item explanation, edited confirmation value, two design columns, and pass/fail/open rows. Screenshot: `/tmp/redline-smoke/engineer_redline_stub.png`.

Results: **317 Python tests passed, 21 skipped** (`unittest discover -s tests -q`); the **7 focused redline tests passed**. Full `tools/ui_smoke.js http://127.0.0.1:8781 /tmp/redline-smoke` passed with exit 0, including the new stubbed redline flow. The browser flow was also rerun at 1920×1080. Engine-dependent suites emitted existing subprocess ResourceWarnings, but no test failed. The smoke's existing optional cost/start-up and discipline-layout assertions now use fixed browser fixtures, so a missing or stale saved assessment does not turn a layout assertion into a data-cache test. Browser/server checks ran in a separate temporary clone with paid actions disabled; the test server was stopped afterward.

Limits: handwriting accuracy is unmeasured until a live read is reviewed. Missing ratings, split/join topology and vendor evidence must be supplied by the engineer; the reader is prompted not to invent them. JSON editing is intentionally the smallest complete editor for all four change forms. Confirmation records intent; it does not grant MOC approval or apply the design.

## First live read (2026-11-02, salt_mvr)
- **Input:** `salt_redline.png`, the salt plant's Rev A with three red notes drawn on it by a script (typed red text and circles, not handwriting): "CLEAN E-201, U back to 2,500 W/m2K"; "ADD K-202 parallel to K-201, ~55 t/h, 2.4 MW"; "FV-301: purge 7.0 %".
- **Muse Wonder read** (`runs/ws/salt_mvr/redline/386b1891…/read.json`): all three notes transcribed verbatim.
  - E-201 was mapped to the right model field (`units.V-201.U_W_m2K = 2500`; the model carries E-201 as V-201's heater, confidence 0.9). Validation refused it because the ink gives no `physical_change` or `rating_source`.
  - K-202 (0.75) and FV-301 (0.45) were left unmapped: the ink names no split/join connections or model setpoint. That is the prompt's "never invent a size or topology" rule working.
- **Engineer confirmation:** the E-201 change, with its physical change and source filled in; K-202 and FV-301 rejected for missing detail. Hash-chained in the audit log.
- **Side-by-side check** (no model call):

| | Engineer's design (clean E-201 only) | Muse's saved design (clean + K-202 + purge trim) |
|---|---|---|
| Process, 120 % target | fail: max 100 %, K-201 suction flow limits | pass: 120 % |
| Robustness envelope | fail: 1/4 scenarios | fail: 3/4 (heater fouled to design U) |
| Electrical | not affected | fail: TX-1 133 % loaded |

- **Reading:** cleaning alone does not move the bottleneck, which is the compressor. Muse's design reaches the target but fails the electrical and fouled-heater checks. The engineer sees both, with the same checks.
