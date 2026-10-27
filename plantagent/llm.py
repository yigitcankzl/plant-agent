"""Muse client with a disk cache and a hard spend cap.

Every call is cached by (model, messages, params), so re-running a scenario during
development costs nothing. Every billed call is appended to runs/usage.jsonl and
the client refuses new calls once the ledger reaches BUDGET_USD.
"""
import hashlib
import json
import os
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "runs" / "llm_cache"
LEDGER = ROOT / "runs" / "usage.jsonl"

# USD per 1M tokens (input, output), from dev.meta.ai pricing.
PRICES = {
    "muse-wonder-1.0": (4.00, 20.00),
    "muse-spark-1.3": (1.25, 4.25),
    # Contributor tier: data may be used to train Meta models. Public documents only.
    "muse-spark-1.3-contributor": (0.10, 0.20),
}
# ponytail: one global cap; keep ~$30 of the $150 for final demo runs and video takes.
BUDGET_USD = float(os.getenv("MUSE_BUDGET_USD", "120"))
TAG = ""  # written to each ledger line (e.g. the case name) so cost can be split per study


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def spent(tag=None):
    if not LEDGER.exists():
        return 0.0
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l]
    return sum(r["usd"] for r in rows if tag is None or r.get("tag") == tag)


def cost(model, usage):
    pin, pout = PRICES[model]
    return (usage.prompt_tokens * pin + usage.completion_tokens * pout) / 1e6


_client = None


def complete(model, messages, **params):
    """Returns the assistant message as a dict {content, tool_calls}. Cached; raises once the budget is used up."""
    global _client
    key = hashlib.sha256(json.dumps([model, messages, params], sort_keys=True).encode()).hexdigest()
    hit = CACHE / f"{key}.json"
    if hit.exists():
        return json.loads(hit.read_text())["message"]

    if spent() >= BUDGET_USD:
        raise RuntimeError(f"Muse budget reached (${spent():.2f} of ${BUDGET_USD}). Raise MUSE_BUDGET_USD deliberately.")
    if _client is None:
        _load_env()
        _client = OpenAI(api_key=os.environ["META_API_KEY"], base_url=os.getenv("META_BASE_URL", "https://api.meta.ai/v1"))

    r = _client.chat.completions.create(model=model, messages=messages, **params)
    m = r.choices[0].message
    msg = {"content": m.content, "tool_calls": [
        {"id": t.id, "name": t.function.name, "arguments": t.function.arguments} for t in (m.tool_calls or [])]}
    usd = cost(model, r.usage)

    CACHE.mkdir(parents=True, exist_ok=True)
    hit.write_text(json.dumps({"message": msg}))
    with LEDGER.open("a") as f:
        f.write(json.dumps({"model": model, "tag": TAG, "in": r.usage.prompt_tokens, "out": r.usage.completion_tokens, "usd": round(usd, 5)}) + "\n")
    return msg


def chat(model, messages, **params):
    return complete(model, messages, **params)["content"]


if __name__ == "__main__":
    print(f"spent ${spent():.4f} of ${BUDGET_USD}")
