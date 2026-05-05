#!/bin/bash
# ============================================================
# Part4 Top10 管道评估脚本
# 对 video_data/part4 前 10 个视频跑完整流水线
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CAPSTONE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$CAPSTONE_ROOT"

echo "========================================"
echo " Part4 Top10 管道评估"
echo "========================================"
echo "工作目录: $(pwd)"
echo ""

# 加载 .env（API keys 等）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 运行管道（可以传额外参数，如 --first-n 10）
python agent/test/run_pipeline_on_part4_top10.py \
    --first-n 10 \
    --output-dir agent/test/generated/pipeline_eval_part4_top10 \
    "$@"

echo ""
echo "========================================"
echo " 完成！"
echo " 输出: agent/test/generated/pipeline_eval_part4_top10/"
echo "========================================"
