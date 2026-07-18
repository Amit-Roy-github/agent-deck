#!/usr/bin/env bash
# Dev server — port aur reload yahan baked hai, ab sirf `./dev.sh` chalao.
# Reload watcher agar stuck ho jaye (route pick na kare) to: NO_RELOAD=1 ./dev.sh
set -euo pipefail
cd "$(dirname "$0")"

RELOAD_FLAG="--reload"
[[ "${NO_RELOAD:-}" == "1" ]] && RELOAD_FLAG=""

exec ./.venv/bin/uvicorn agent_deck.api.app:app ${RELOAD_FLAG} --port "${PORT:-8000}"
