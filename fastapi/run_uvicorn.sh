#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/home/yangxp/Capstone"
APP_DIR="${PROJECT_ROOT}/fastapi"
PYTHON_BIN="/home/yangxp/anaconda3/envs/capstone/bin/python"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8001}"
WORKERS="${WORKERS:-1}"

cd "${PROJECT_ROOT}"
exec "${PYTHON_BIN}" -m uvicorn main:app \
  --app-dir "${APP_DIR}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --workers "${WORKERS}"
