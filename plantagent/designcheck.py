"""Blind NETL design-reproduction check. Usage: python -m plantagent.designcheck --case netl_syngas_cooler.

Only the agent's final DWSIM run is scored. Answer-key values are never sent to the agent.
"""
import argparse
import json
import re
import time
from pathlib import Path

from . import llm
from .docs import Case
from .study import DOC_TOOLS, PROCESS_TOOLS, Study

ROOT = Path(__file__).resolve().parent.parent
MODELS = ("muse-spark-1.3-contributor", "baseten:meta-models/muse-spark-open-1026")
CAPS = {"muse": 3.0, "baseten": 5.0}
RESERVE = {"muse": 0.10, "baseten": 0.25}
SUBMIT = {"type": "function", "function": {"name": "submit_design", "description": "Finish the design reproduction after at least one DWSIM run.",
          "parameters": {"type": "object", "properties": {"run_label": {"type": "string"}, "assumptions": {"type": "string"},
                         "limitations": {"type": "string"}}, "required": ["run_label", "assumptions", "limitations"]}}}


def _provider(model):
    return "baseten" if model.startswith("baseten:") else "muse"


def _spend():
    rows = [json.loads(line) for line in llm.LEDGER.read_text().splitlines() if line] if llm.LEDGER.exists() else []
    return {"muse": sum(r["usd"] for r in rows if r.get("tag") not in ("baseten", "fireworks")),
            "baseten": sum(r["usd"] for r in rows if r.get("tag") == "baseten")}


def _leak_hits(case, metrics):
    text = case.visible_text()
    hits = []
    for metric in metrics:
        value = metric["expected"]
        forms = {str(value)}
        if metric["type"] == "T_K":
            forms.add(str(round(value - 273.15, 2)).rstrip("0").rstrip("."))
        if metric["type"] == "P_bar":
            forms.add(str(round(value / 10, 3)))  # NETL tables use MPa
        for form in forms:
            if re.search(r"(?<![\d.])" + re.escape(form) + r"(?!\d)", text):
                hits.append({"metric": metric["id"], "number": form})
    return hits


def _actual(metric, run):
    streams, units = run.get("streams") or {}, run.get("units") or {}
    typ = metric["type"]
    stream = streams.get(metric.get("stream"), {})
    if typ == "T_K":
        return stream.get("T_C") + 273.15 if stream.get("T_C") is not None else None
    if typ == "P_bar":
        return stream.get("P_bar")
    if typ == "kg_h":
        return stream.get("kg_h")
    if typ == "component_kg_h":
        return (stream.get("components_kg_h") or {}).get(metric["component"])
    if typ == "compressor_kW":
        pressure_units = [u for u in units.values() if u.get("type") in ("compressor", "pump")]
        if any(u["type"] == "pump" and (u.get("dP_bar") or 0) > 10 and (u.get("m3_h") or 0) < 1
               for u in pressure_units):
            return None  # DWSIM's dense-CO2 volumetric flow can be ~0 despite large mass flow
        values = [u.get("kW") for u in pressure_units]
        return sum(abs(v) for v in values) if values and all(v is not None for v in values) else None
    if typ == "cooling_kW":
        values = [u.get("duty_kW") for u in units.values() if u.get("type") in ("cooler", "hx")]
        return sum(abs(v) for v in values) if values and all(v is not None for v in values) else None
    if typ == "aftercooler_kW":
        spec_units = {u["id"]: u for u in run.get("spec", {}).get("units", [])}
        values = [u.get("duty_kW") for uid, u in units.items() if u.get("type") in ("cooler", "hx")
                  and (spec_units.get(uid, {}).get("out") == metric["stream"] or
                       metric["stream"] in (spec_units.get(uid, {}).get("cold") or []) + (spec_units.get(uid, {}).get("hot") or []))]
        return abs(values[0]) if len(values) == 1 and values[0] is not None else None
    raise ValueError(f"unknown metric type {typ}")


def score(metrics, run):
    rows = []
    for metric in metrics:
        actual = _actual(metric, run) if run and not run.get("errors") else None
        error = abs(actual - metric["expected"]) / abs(metric["expected"]) * 100 if actual is not None else None
        rows.append({**metric, "actual": actual, "error_pct": round(error, 3) if error is not None else None,
                     "within_2pct": error is not None and error <= 2,
                     "within_5pct": error is not None and error <= 5,
                     "within_10pct": error is not None and error <= 10})
    def rates(group):
        return {f"within_{n}pct": round(sum(r[f"within_{n}pct"] for r in group) / len(group), 3) for n in (2, 5, 10)}
    types = sorted({r["type"] for r in rows})
    return {"overall": rates(rows), "by_type": {t: rates([r for r in rows if r["type"] == t]) for t in types},
            "metrics": rows}


def run_case(name, model):
    if name not in ("netl_syngas_cooler", "netl_co2_compression"):
        raise ValueError("designcheck accepts only the two NETL design-reproduction cases")
    if model not in MODELS:
        raise ValueError(f"model must be one of {MODELS}")
    case = Case(name)
    key = json.loads((case.dir / "answer_key.json").read_text())
    allowed = set(case.pages)
    withheld = {p for a, b in case.cfg["withheld_pages"] for p in range(a, b + 1)}
    if allowed & withheld:
        raise ValueError(f"allowed and withheld pages overlap: {sorted(allowed & withheld)}")
    leaks = _leak_hits(case, key["metrics"])
    if leaks:
        raise ValueError(f"answer-key values visible on allowed pages: {leaks}")

    output = ROOT / "runs" / "designcheck" / name
    output.mkdir(parents=True, exist_ok=True)
    budget_file = ROOT / "runs" / "designcheck" / "budget_baseline.json"
    if not budget_file.exists():
        budget_file.write_text(json.dumps(_spend(), indent=2))
    baseline = json.loads(budget_file.read_text())
    provider = _provider(model)
    if _spend()[provider] - baseline[provider] + RESERVE[provider] >= CAPS[provider]:
        raise RuntimeError(f"designcheck {provider} cap would be exceeded; no model call made")
    spend_before = _spend()[provider]

    study = Study(name, model)
    llm.TAG = "designcheck:" + name
    original = llm.complete
    def bounded_complete(requested_model, messages, **params):
        if _spend()[provider] - baseline[provider] + RESERVE[provider] >= CAPS[provider]:
            raise RuntimeError(f"designcheck {provider} cap reached before next model call")
        return original(requested_model, messages, max_tokens=8000, **params)
    llm.complete = bounded_complete
    started = time.time()
    submission, failure = None, None
    try:
        submission = study.loop("design", """You are a process engineer reproducing a published design blindly. Only pages explicitly listed as available can be read or viewed. Never search the web or use remembered NETL values. Build the section yourself with DWSIM. An assumed T_out_C, P_out_bar, recovery, efficiency, or duty is an assumption, not independent validation; explain it. Run the model, inspect errors, and submit your final run label. Do not claim unavailable stream-table values.""",
                                f"Available PDF pages: {case.pages}. {case.question}", DOC_TOOLS + PROCESS_TOOLS + [SUBMIT],
                                "submit_design", 12)
    except Exception as exc:  # keep failed and over-budget attempts as evidence
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        llm.complete = original
        study.log.close()

    process_runs = [(label, item) for label, item in study.surges.items() if "units" in item.get("spec", {})]
    valid_runs = [(label, item) for label, item in process_runs if not (item.get("result") or {}).get("errors")]
    submitted_label = submission.get("run_label") if isinstance(submission, dict) else None
    submitted_item = study.surges.get(submitted_label) if submitted_label else None
    submitted_errors = (submitted_item.get("result") or {}).get("errors") if submitted_item else None
    if submission and (not submitted_item or "units" not in submitted_item.get("spec", {}) or submitted_errors):
        reason = (f"submitted run label {submitted_label!r} has solve errors: {submitted_errors}" if submitted_errors else
                  f"submitted run label {submitted_label!r} does not name a solved DWSIM process run")
        failure = (failure + "; " if failure else "") + reason
        final_label, final_item = submitted_label, None
    else:
        final_label, final_item = submitted_label, submitted_item
    final_run = {**final_item["result"], "spec": final_item["spec"]} if final_item else None
    # The key was not passed to Study or the model; scoring begins after its tool loop.
    result = {"case": name, "model": model, "allowed_pages": case.pages,
              "withheld_pages": sorted(withheld), "leak_hits": leaks, "submission": submission,
              "failure": failure, "final_run_label": final_label, "dwsim_runs": len(valid_runs),
              "dwsim_attempts": len(process_runs),
              "steps": study.steps, "wall_time_s": round(time.time() - started, 1),
              "spend_usd": round(_spend()[provider] - baseline[provider], 5),
              "model_run_cost_usd": round(_spend()[provider] - spend_before, 5),
              "score": score(key["metrics"], final_run), "final_run": final_run,
              "tool_log": str(study.dir / "log.jsonl")}
    path = output / (time.strftime("%Y%m%d-%H%M%S") + "-" + provider + ".json")
    path.write_text(json.dumps(result, indent=2))
    print(json.dumps({"result": str(path), "model": model, "failure": failure,
                      "score": result["score"]["overall"], "dwsim_runs": len(valid_runs),
                      "task_spend_usd": result["spend_usd"]}, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=("netl_syngas_cooler", "netl_co2_compression"))
    parser.add_argument("--model", default=MODELS[0], choices=MODELS)
    args = parser.parse_args()
    run_case(args.case, args.model)


if __name__ == "__main__":
    main()
