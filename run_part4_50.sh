#!/bin/bash
# ============================================================
# Part4 全量评测（156 case）
# 输出目录：agent/test/generated/ragas_eval_e2e_p4_full/
# ============================================================
set -euo pipefail

cd "$(dirname "$0")/agent/test"

OUTPUT_DIR="/home/yangxp/Capstone/agent/test/generated/ragas_eval_e2e_p4_full"
SEED_DIR="/home/yangxp/Capstone/agent/test/generated/datasets/ucfcrime_events_vector_flat"

echo "=== Part4 full eval (156 cases) ==="
echo "Output:  $OUTPUT_DIR"
echo "Seeds:   $SEED_DIR"
echo ""

python ragas_eval_runner.py \
    --prepare-subset-db \
    --seed-dir "$SEED_DIR" \
    --output-dir "$OUTPUT_DIR" \
    2>&1 | tee "$OUTPUT_DIR.log"

echo ""
echo "=== Done ==="
echo "Results: $OUTPUT_DIR/"
echo "Log:     $OUTPUT_DIR.log"
