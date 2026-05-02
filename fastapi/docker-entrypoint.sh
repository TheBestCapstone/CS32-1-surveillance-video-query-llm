#!/usr/bin/env bash
set -euo pipefail

cd /app

exec uvicorn main:app --app-dir /app/fastapi --host "${HOST:-0.0.0.0}" --port "${PORT:-8001}"
