#!/bin/bash
# ============================================================
# Part4 困难 Case 快速测试（63 case）
# 输出目录：agent/test/generated/ragas_eval_e2e_hard63/
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/agent/test"

OUTPUT_DIR="$SCRIPT_DIR/agent/test/generated/ragas_eval_e2e_hard63"
SEED_DIR="$SCRIPT_DIR/agent/test/generated/datasets/ucfcrime_events_vector_flat"
CASE_IDS="$SCRIPT_DIR/agent/test/data/hard_cases_part4.txt"

echo "=== Part4 hard-case eval (63 cases) ==="
echo "Output:    $OUTPUT_DIR"
echo "Seeds:     $SEED_DIR"
echo "Case IDs:  $CASE_IDS"
echo ""

python ragas_eval_runner.py \
    --prepare-subset-db \
    --seed-dir "$SEED_DIR" \
    --case-ids-file "$CASE_IDS" \
    --output-dir "$OUTPUT_DIR" \
    2>&1 | tee "$OUTPUT_DIR.log"

echo ""
echo "=== Done ==="
echo "Results: $OUTPUT_DIR/"
echo "Log:     $OUTPUT_DIR.log"
