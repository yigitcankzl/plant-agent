#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  cat <<'EOF'
Usage: ./start.sh [--live]

  ./start.sh         Install once and open the stored replay (no API key).
  ./start.sh --live  Also enable Meta calls, using your own META_API_KEY.
EOF
}

mode="${1:-}"
case "$mode" in
  "") export WEB_ALLOW_RUNS=0 ;;
  --live)
    export WEB_ALLOW_RUNS=1
    export MUSE_BUDGET_USD="${MUSE_BUDGET_USD:-5}"
    if [[ -z "${META_API_KEY:-}" ]] && ! grep -Eq '^META_API_KEY=.+$' .env 2>/dev/null; then
      [[ -t 0 ]] || { echo "META_API_KEY is required for --live." >&2; exit 2; }
      read -r -s -p "Your Meta Model API key (not saved): " META_API_KEY
      echo
      [[ -n "$META_API_KEY" ]] || { echo "No key entered." >&2; exit 2; }
      export META_API_KEY
    fi
    ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

python="${PYTHON:-}"
if [[ -z "$python" ]]; then
  for candidate in python3.12 python3; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))'; then
      python="$candidate"
      break
    fi
  done
fi
[[ -n "$python" ]] && "$python" -c 'import sys; raise SystemExit(sys.version_info[:2] != (3, 12))' || {
  echo "PlantAgent needs Python 3.12." >&2
  exit 2
}

requirements_hash="$($python -c 'import hashlib; print(hashlib.sha256(open("requirements.txt", "rb").read()).hexdigest())')"
if [[ ! -x .venv/bin/python || "$(cat .venv/.plantagent-requirements 2>/dev/null || true)" != "$requirements_hash" ]]; then
  [[ -x .venv/bin/python ]] || "$python" -m venv .venv
  .venv/bin/pip install -r requirements.txt
  printf '%s\n' "$requirements_hash" > .venv/.plantagent-requirements
fi

echo "PlantAgent: http://127.0.0.1:${PORT:-8765}/home.html"
exec .venv/bin/python -m plantagent.web --port "${PORT:-8765}"
