# SAM-assisted scanned P&ID experiment

## Outcome: reachable, no demonstrated improvement

Meta SAM 3.1 accepted all six concept requests for the upright salt patent FIG. 1. Each response was `completed`, reported one processed image, and contained empty output text: **zero masks**. No crops or decorative overlay were passed to Wonder when there were no regions.

The single new Wonder read returned null content, with 6,000 output tokens charged (the requested cap). The shared client did not retain the finish reason, so token exhaustion is an inference, not a recorded termination reason. There was no retry and no usable new topology to score. Do not describe this as an accuracy gain or score a missing read as zero correct connections.

| Metric | Stored baseline | New SAM-assisted attempt |
|---|---:|---:|
| Reader | muse-spark-1.3 | muse-wonder-1.0 |
| Equipment found | 13/13 | unavailable: read failed |
| Equipment type correct | 12/13 | unavailable |
| Directed connections + printed line ID | 16/20 | unavailable |
| Missing / extra connections | 4 / 4 | unavailable |
| Directed connections ignoring line ID | 17/20 | unavailable |
| SAM regions | not used | 0 |

The baseline is Spark, not Wonder. Even a successful new read would not isolate the effect of SAM from the change of reader. The baseline's BP-1 is classified as pump instead of the confirmed heat exchanger. Scores use the engineer-confirmed record; it is not independent ground truth.

## API and reproducibility

Official references: [segmenting](https://dev.meta.ai/docs/sam/segmenting), [reading output](https://dev.meta.ai/docs/sam/reading-segmentation), [client libraries](https://dev.meta.ai/docs/sam/client-libraries), [SAM 3.1 pricing](https://dev.meta.ai/models/sam-3-1), [wire protocol](https://github.com/meta-models/meta-sam/blob/main/protocol/sam3.md).

`POST https://api.meta.ai/v1/responses`, model `sam-3.1`, non-streaming. User content: one `input_text` concept and one `input_image` data URL. Metadata requests `mask_encoding: one_bit` and confidence. The API supports one concept per request, so `segment()` sends six requests, not one multi-concept request: pump, heat exchanger, vessel, compressor, valve, pipe. No retries or fallback model. Successful HTTP responses are charged in the existing ledger and guarded by its provider and task budgets.

Source: [US5366514A](https://patents.google.com/patent/US5366514A/en), PDF page index 1, rotated 90 degrees, 170 dpi. The original PDF remains outside the repo. Rendered input: 1932 × 1315 pixels, SHA256 `473780c13c2dd7d50d84b02a229d37544885227abed2fd0e9d89612d87bece9e`.

Actual responses, sanitized request metadata, rendered input, empty region manifest, failed read message, baseline score and task-only ledger are committed under `runs/ws/salt_mvr_vision/sam/`. The initial pump accessibility probe is reused from cache in the six-concept set: six actual SAM requests total. No key or authorization header is stored.

Install optional parser: `.venv/bin/pip install -r requirements-sam.txt`. Enable through `pidvision.read(..., sam_assisted=True, sam_dir=...)` or `PID_SAM=1`. Default is off, with the original messages and parameters unchanged. Nonempty masks produce numbered crops, overlay and source-image coordinates; concepts are explicitly unverified hints, never confirmed topology. Fake mask tests demonstrate that branch; the live scan did not exercise it.

Deterministic scoring: `.venv/bin/python tools/pid_read_eval.py runs/ws/salt_mvr_vision/pid_read.json`. Equipment matches normalized printed labels and occurrence one-to-one; classes match normalized strings exactly. Connections match directed endpoints and normalized printed line ID; duplicates count as extras. No semantic grading or hidden answer is supplied to the reader.

## Cost and checks

- SAM: 6 × $0.0025 = **$0.015**.
- One Wonder read: **$0.13414**.
- Total: **$0.14914**, below $1. The task ledger is a filtered copy of the main checkout usage ledger.
- Full suite before the final cache fast-path and null-response guard: **332 tests, OK (skipped=21)**.
- Targeted offline tests cover request/cache/budget/errors, official fake mask decoding, coordinate prompt, empty-region behavior, unchanged default request, failed reader response and deterministic scoring.

Limits: no evidence that SAM segments engineering line drawings reliably with these prompts; no controlled Wonder-only comparison, no additional paid retries. Keep opt-in and do not advertise improved connection accuracy.
