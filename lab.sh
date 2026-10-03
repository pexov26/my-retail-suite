#!/usr/bin/env bash
# lab.sh — Terminal wrapper for the Retail Suite (micromamba-based).
#
# Usage:  ./lab.sh [setup|run|update|remove|help]     (default: run)
# Env overrides:  ENV_NAME (default retail-suite)  PORT (default 8501)  PYTHON_VERSION (default 3.12)

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

ENV_NAME="${ENV_NAME:-retail-suite}"
PORT="${PORT:-8501}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"   # pandas 3.0 requires Python >= 3.11

command -v micromamba >/dev/null 2>&1 || {
  echo "error: micromamba not found in PATH" >&2
  exit 1
}

env_exists() {
  micromamba env list | awk '{print $1}' | grep -qx "$ENV_NAME"
}

setup() {
  if env_exists; then
    echo ">> env '$ENV_NAME' already exists (use './lab.sh update' to sync packages)"
  else
    echo ">> creating env '$ENV_NAME' (python=$PYTHON_VERSION)"
    micromamba create -y -n "$ENV_NAME" -c conda-forge "python=$PYTHON_VERSION" pip
  fi
  update
}

update() {
  micromamba run -n "$ENV_NAME" python -m pip install --upgrade -r requirements.txt
}

run() {
  env_exists || setup
  exec micromamba run -n "$ENV_NAME" python -m streamlit run app.py \
    --server.port "$PORT" --browser.gatherUsageStats false
}

remove() {
  micromamba env remove -y -n "$ENV_NAME"
}

case "${1:-run}" in
  setup)  setup ;;
  run)    run ;;
  update) update ;;
  remove) remove ;;
  help|-h|--help) sed -n '2,5p' "$0" ;;
  *) echo "unknown command: $1 (try: setup|run|update|remove|help)" >&2; exit 2 ;;
esac
