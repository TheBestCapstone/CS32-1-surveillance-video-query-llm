#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8001}"
QUERY="${1:-two white police cars flashing roof lights}"
DATABASE_ID="${DATABASE_ID:-configured-default}"

echo "[select-db] POST ${BASE_URL}/api/v1/databases/select"
curl -sS -X POST "${BASE_URL}/api/v1/databases/select" \
  -H "Content-Type: application/json" \
  -d "{\"database_id\":\"${DATABASE_ID}\"}"

echo

echo "[query] POST ${BASE_URL}/api/v1/query"
curl -sS -X POST "${BASE_URL}/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"${QUERY}\",\"include_rows\":false,\"top_k_rows\":3}"

echo
echo "[stream] POST ${BASE_URL}/api/v1/query/stream"
curl -N -sS -X POST "${BASE_URL}/api/v1/query/stream" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"${QUERY}\",\"include_rows\":false,\"top_k_rows\":3}"

echo
