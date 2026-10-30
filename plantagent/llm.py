"""Muse client with a disk cache and a hard spend cap.

Every call is cached by (model, messages, params), so re-running a scenario during
development costs nothing. Every billed call is appended to runs/usage.jsonl and
the client refuses new calls once the ledger reaches BUDGET_USD.
"""
import hashlib
import io
import json
import os
import threading
import wave
from contextlib import contextmanager
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
_TAG = threading.local()
_LOCK = threading.RLock()


def set_tag(value):
    _TAG.value = str(value or "")


def current_tag():
    return getattr(_TAG, "value", "")


def inherit_tag(function):
    """Carry the caller's spend label into a worker thread."""
    tag = current_tag()

    def call(*args, **kwargs):
        set_tag(tag)
        return function(*args, **kwargs)
    return call


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()
BUDGET_USD = float(os.getenv("MUSE_BUDGET_USD", "120"))  # read after .env so the file cap applies


def spent(tag=None):
    if not LEDGER.exists():
        return 0.0
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l]
    return sum(r["usd"] for r in rows if tag is None or r.get("tag") == tag)


@contextmanager
def _billing_lock():
    """Serialize cache/budget/ledger across threads and local server processes."""
    import fcntl
    with _LOCK:
        lock = ROOT / "runs" / ".llm.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


# Open-weights hosts, addressed as "<host>:<model id>" (e.g. "baseten:meta-models/muse-spark-open-1026"); own key and budget each.
OPEN_HOSTS = {"fireworks": ("https://api.fireworks.ai/inference/v1", "FIREWORKS_API_KEY", float(os.getenv("FIREWORKS_BUDGET_USD", "80"))),
              "baseten": ("https://inference.baseten.co/v1", "BASETEN_API_KEY", float(os.getenv("BASETEN_BUDGET_USD", "80")))}
# ponytail: hackathon credit hosts publish no per-token price for this model; a conservative default over-counts spend
OPEN_DEFAULT_PRICE = (1.0, 3.0)


def _host(model):
    return model.split(":", 1)[0] if model.split(":", 1)[0] in OPEN_HOSTS else None


def cost(model, usage):
    pin, pout = PRICES.get(model) or (OPEN_DEFAULT_PRICE if _host(model) else PRICES[model])
    return (usage.prompt_tokens * pin + usage.completion_tokens * pout) / 1e6


_client, _open = None, {}


def _client_for(model):
    """Meta Model API by default; "<host>:<model id>" runs Muse Spark Open on an open-weights host (own key and budget)."""
    global _client
    _load_env()
    host = _host(model)
    if host:
        url, key, budget = OPEN_HOSTS[host]
        if spent(host) >= budget:
            raise RuntimeError(f"{host} budget reached (${spent(host):.2f} of ${budget}).")
        if host not in _open:
            _open[host] = OpenAI(api_key=os.environ[key], base_url=url, timeout=300, max_retries=2)
        return _open[host], model.split(":", 1)[1]
    if spent() - sum(spent(h) for h in OPEN_HOSTS) >= BUDGET_USD:
        raise RuntimeError(f"Muse budget reached (${spent():.2f} of ${BUDGET_USD}). Raise MUSE_BUDGET_USD deliberately.")
    _client = _client or OpenAI(api_key=os.environ["META_API_KEY"], base_url=os.getenv("META_BASE_URL", "https://api.meta.ai/v1"), timeout=480, max_retries=1)
    return _client, model


def _provider_spend(model):
    host = _host(model)
    return spent(host) if host else spent() - sum(spent(name) for name in OPEN_HOSTS)


def _budget(model):
    host = _host(model)
    return OPEN_HOSTS[host][2] if host else BUDGET_USD


def _reserve(model, messages, params):
    pin, pout = PRICES.get(model) or OPEN_DEFAULT_PRICE
    input_tokens = max(1, len(json.dumps(messages, default=str)) // 4)
    output_tokens = int(params.get("max_tokens") or 4096)
    return (input_tokens * pin + output_tokens * pout) / 1e6


def _append_usage(row):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as handle:
        handle.write(json.dumps(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def complete(model, messages, **params):
    """Returns the assistant message as a dict {content, tool_calls}. Cached; raises once the budget is used up."""
    key = hashlib.sha256(json.dumps([model, messages, params], sort_keys=True).encode()).hexdigest()
    hit = CACHE / f"{key}.json"
    with _billing_lock():
        if hit.exists():
            return json.loads(hit.read_text())["message"]
        reserve = _reserve(model, messages, params)
        if _provider_spend(model) + reserve > _budget(model):
            raise RuntimeError(f"{_host(model) or 'Muse'} budget would be exceeded by this call; no model call made")
        client, model_id = _client_for(model)
        r = client.chat.completions.create(model=model_id, messages=messages, **params)
        m = r.choices[0].message
        msg = {"content": m.content, "tool_calls": [
            {"id": t.id, "name": t.function.name, "arguments": t.function.arguments} for t in (m.tool_calls or [])]}
        usd = cost(model, r.usage)
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = hit.with_name(f".{hit.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps({"message": msg}))
        os.replace(tmp, hit)
        _append_usage({"model": model, "tag": _host(model) or current_tag(), "in": r.usage.prompt_tokens,
                       "out": r.usage.completion_tokens, "usd": round(usd, 5)})
        return msg


def transcribe(wav: bytes):
    """Muse Voice Transcribe (push-to-talk). Billed per audio hour; logged in the same ledger and budget."""
    import urllib.request
    try:
        with wave.open(io.BytesIO(wav)) as audio:
            estimated = audio.getnframes() / max(audio.getframerate(), 1) / 3600 * 0.18
    except (wave.Error, EOFError) as exc:
        raise ValueError("invalid WAV audio") from exc
    with _billing_lock():
        if _provider_spend("muse-spark-1.3") + estimated > BUDGET_USD:
            raise RuntimeError("Muse budget would be exceeded by this transcription; no model call made")
        _load_env()
        b = "----plantagent" + hashlib.sha1(wav[:64]).hexdigest()
        req = json.dumps({"model": "muse-voice-transcribe-1.0", "audioEncoding": "WAV", "mode": "PUSH_TO_TALK"}).encode()
        body = (f"--{b}\r\nContent-Disposition: form-data; name=\"request\"\r\nContent-Type: application/json\r\n\r\n").encode() + req + \
               (f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"speech.wav\"\r\nContent-Type: audio/wav\r\n\r\n").encode() + \
               wav + f"\r\n--{b}--\r\n".encode()
        request = urllib.request.Request(os.getenv("META_BASE_URL", "https://api.meta.ai/v1") + "/asr/transcribe", data=body, method="POST",
                                         headers={"Authorization": "Bearer " + os.environ["META_API_KEY"],
                                                  "Content-Type": f"multipart/form-data; boundary={b}", "Accept": "application/json"})
        out = json.loads(urllib.request.urlopen(request, timeout=60).read())
        usd = out.get("audioDurationMs", 0) / 3.6e6 * 0.18
        _append_usage({"model": "muse-voice-transcribe-1.0", "tag": current_tag(), "in": 0, "out": 0,
                       "usd": round(usd, 6), "audio_ms": out.get("audioDurationMs")})
        return out


def chat(model, messages, **params):
    return complete(model, messages, **params)["content"]


if __name__ == "__main__":
    print(f"spent ${spent():.4f} of ${BUDGET_USD}")
