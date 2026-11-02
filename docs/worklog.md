# Engineering loop work log

`plantagent/loop.py` runs a change through the full engineering loop. Muse proposes; the engines re-solve and run every check; the failed checks go back to Muse with their numbers; Muse fixes them. This repeats until every check passes, Muse says the remaining issue cannot be solved, or the round or budget limit is reached. Each run writes one work log.

## API
- `POST /api/plant/<case>/work` with body `{goal, max_rounds?, budget_usd?}` starts a run and returns `{job}`. Follow it like `ask`, through `/api/jobs/<job>`.
- `GET /api/plant/<case>/work` returns the list `[{id, goal, status, rounds, usd_total, started}]`, newest first.
- `GET /api/plant/<case>/work/<id>` returns the full log, in the shape below.

Stored at `runs/ws/<case>/work/<id>/worklog.json`.

## Shape
```json
{
  "id": "20261102-101500",
  "case": "salt_mvr",
  "goal": "Get the unit to 120 % of today's throughput ...",
  "label": "post-hoc engineering run" ,
  "status": "done | unsolved | max_rounds | budget | error",
  "approval_status": "open | ready_for_review | not_reached",
  "started": "2026-11-02T10:15:00+0300", "finished": "...",
  "usd_total": 6.12, "seconds_total": 1830,
  "rounds": [
    {
      "n": 1,
      "answer_index": 8,
      "steps": [
        {"actor": "muse", "kind": "propose", "title": "Clean E-201; add parallel compressor K-202; trim purge steam",
         "detail": "headline of the answer", "status": "info", "usd": 2.10, "seconds": 410,
         "changes": [{"path": "units.E-201.U_W_m2K", "value": 2500}]},
        {"actor": "engine", "engine": "DWSIM", "kind": "solve", "title": "Combined design re-solved",
         "status": "pass", "numbers": {"capacity_pct": 120.1, "target_pct": 120}},
        {"actor": "engine", "engine": "pandapower", "kind": "check", "check": "electrical",
         "title": "TX-1 loading 132.8 % of 2.5 MVA", "status": "fail", "numbers": {"value": 132.8, "limit": 100, "unit": "%"}},
        {"actor": "engine", "engine": "curves", "kind": "check", "check": "surge", "title": "K-202 surge margin 33 %", "status": "pass"},
        {"actor": "engine", "engine": "transient", "kind": "check", "check": "startup", "title": "Anti-surge recycle 35,823 vs 34,030 m3/h", "status": "fail"},
        {"actor": "engine", "engine": "uncertainty", "kind": "check", "check": "confidence", "title": "Target met in 31 % of 64 re-solves", "status": "fail",
         "numbers": {"p_target": 0.31}}
      ],
      "open_issues": [{"check": "electrical", "detail": "TX-1 132.8 % of rating"}]
    }
  ],
  "result": {"answer_index": 11, "headline": "...", "passes": ["process", "electrical"], "fails": [], "open": ["piping"]},
  "deliverables": [{"kind": "moc", "title": "MOC pack", "path": "runs/ws/salt_mvr/decision/..."}],
  "needs_human": ["Vendor curve for K-202", "Confirm TX-1 nameplate"]
}
```

Fields:
- `actor`: `muse` (language model), `engine` (deterministic solver or check) or `engineer` (a recorded human correction). The UI must show who did each step.
- `status`: `pass`, `fail`, `open` (not calculable) or `info`.
- Top-level `status: done` means the deterministic checks have no failures. `approval_status` stays `open` while vendor or human items remain; it is never an engineering approval.
- `label`: `post-hoc engineering run` when the case is a blind incident whose outcome is already known to us. The blind answer stays separate and unchanged.

`tests/fixtures/worklog_sample.json` is an ILLUSTRATIVE sample for UI work. Its numbers are not results.
