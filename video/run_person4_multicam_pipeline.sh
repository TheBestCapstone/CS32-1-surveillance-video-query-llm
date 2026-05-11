#!/usr/bin/env bash
# Multi-camera Person4 run — LLM borderline verify ON by default (see Python script).
# Usage:
#   conda activate capstone
#   ./video/run_person4_multicam_pipeline.sh
# Or:
#   bash video/run_person4_multicam_pipeline.sh --no-llm-verify

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -z "${CONDA_DEFAULT_ENV:-}" ]] || [[ "${CONDA_DEFAULT_ENV}" != "capstone" ]]; then
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate capstone
fi

export PYTHONPATH="${ROOT_DIR}"
exec python video/run_person4_multicam_pipeline.py "$@"
