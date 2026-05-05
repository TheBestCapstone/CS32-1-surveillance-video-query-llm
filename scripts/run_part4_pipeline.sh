#!/bin/bash
# ============================================================
# Part4 批量视频导入 Pipeline 脚本
# 对 video_data/part4 下所有 .mp4 文件跑完整流水线 (Stage 1 + Stage 2)
#
# Stage 1: YOLO 检测 + BoT-SORT 追踪 + 事件切片 → *_events.json + *_clips.json
# Stage 2: LLM 精炼 (uca 模式, gpt-5.4)     → *_events_uca.json
#
# 用法:
#   bash scripts/run_part4_pipeline.sh                  # 跑全部
#   bash scripts/run_part4_pipeline.sh --first-n 5      # 只跑前 5 个
#   bash scripts/run_part4_pipeline.sh --skip-stage1    # 跳过 Stage 1
#   bash scripts/run_part4_pipeline.sh --skip-stage2    # 跳过 Stage 2
#   bash scripts/run_part4_pipeline.sh --resume         # 断点续跑（跳过已有输出）
#   bash scripts/run_part4_pipeline.sh --dry-run        # 只打印要处理的视频，不实际运行
#   bash scripts/run_part4_pipeline.sh --video-filter "RoadAccidents"  # 只跑匹配名字的视频
# ============================================================
set -euo pipefail

# ── 配置 ──────────────────────────────────────────────────
ROOT_DIR="/home/yangxp/Capstone"
VIDEO_DIR="${ROOT_DIR}/video_data/part4"
OUT_DIR="${ROOT_DIR}/data/part4_pipeline_output"

# Stage 1 参数
MODEL="${MODEL:-11m}"
TRACKER="${TRACKER:-botsort_reid}"
CONF="${CONF:-0.25}"
IOU="${IOU:-0.25}"

# Stage 2 参数
REFINE_MODE="${REFINE_MODE:-uca}"
LLM_MODEL="${LLM_MODEL:-gpt-5.4}"
TEMPERATURE="${TEMPERATURE:-0.1}"
FRAMES_PER_SEC="${FRAMES_PER_SEC:-0.1}"
MIN_FRAMES="${MIN_FRAMES:-6}"
MAX_FRAMES="${MAX_FRAMES:-48}"

# 通用控制
FORCE_RERUN="${FORCE_RERUN:-0}"
CONDA_ENV="${CONDA_ENV:-capstone}"

# ── 参数解析 ──────────────────────────────────────────────
FIRST_N=0           # 0 = 全部
SKIP_STAGE1=0
SKIP_STAGE2=0
RESUME=0
DRY_RUN=0
VIDEO_FILTER=""     # 空串 = 不筛选

while [[ $# -gt 0 ]]; do
  case "$1" in
    --first-n)       FIRST_N="$2"; shift 2 ;;
    --skip-stage1)   SKIP_STAGE1=1; shift ;;
    --skip-stage2)   SKIP_STAGE2=1; shift ;;
    --resume)        RESUME=1; shift ;;
    --dry-run)       DRY_RUN=1; shift ;;
    --video-filter)  VIDEO_FILTER="$2"; shift 2 ;;
    --output-dir)    OUT_DIR="$2"; shift 2 ;;
    -h|--help)
      head -20 "$0" | tail -18
      exit 0
      ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# ── 初始化 ────────────────────────────────────────────────
cd "${ROOT_DIR}"

# 加载 .env（OPENAI_API_KEY 等）
if [ -f .env ]; then
  set -a
  source <(grep -v '^#' .env | grep -v '^\s*$')
  set +a
fi

mkdir -p "${OUT_DIR}"

echo "========================================"
echo " Part4 批量视频导入 Pipeline"
echo "========================================"
echo "视频目录:    ${VIDEO_DIR}"
echo "输出目录:    ${OUT_DIR}"
echo "YOLO 模型:   ${MODEL}  conf=${CONF}  iou=${IOU}"
echo "Tracker:     ${TRACKER}"
echo "LLM 模型:    ${LLM_MODEL}  temp=${TEMPERATURE}  mode=${REFINE_MODE}"
echo "帧采样:      fps=${FRAMES_PER_SEC}  min=${MIN_FRAMES}  max=${MAX_FRAMES}"
echo "取前 N:      $([ ${FIRST_N} -le 0 ] && echo '全部' || echo ${FIRST_N})"
echo "断点续跑:    $([ ${RESUME} -eq 1 ] && echo '是' || echo '否')"
echo "跳过 Stage1: $([ ${SKIP_STAGE1} -eq 1 ] && echo '是' || echo '否')"
echo "跳过 Stage2: $([ ${SKIP_STAGE2} -eq 1 ] && echo '是' || echo '否')"
echo "Dry run:     $([ ${DRY_RUN} -eq 1 ] && echo '是' || echo '否')"
[ -n "${VIDEO_FILTER}" ] && echo "名字过滤:    ${VIDEO_FILTER}"
echo "========================================"
echo ""

# ── 发现视频 ──────────────────────────────────────────────
shopt -s nullglob
videos=("${VIDEO_DIR}"/*.mp4)
shopt -u nullglob

if [ ${#videos[@]} -eq 0 ]; then
  echo "错误: 在 ${VIDEO_DIR} 中未找到 .mp4 文件" >&2
  exit 1
fi

# 名字过滤
if [ -n "${VIDEO_FILTER}" ]; then
  filtered=()
  for v in "${videos[@]}"; do
    if [[ "$(basename "${v}")" == *"${VIDEO_FILTER}"* ]]; then
      filtered+=("${v}")
    fi
  done
  videos=("${filtered[@]+${filtered[@]}}")
  if [ ${#videos[@]} -eq 0 ]; then
    echo "过滤后无匹配视频 (filter: ${VIDEO_FILTER})" >&2
    exit 1
  fi
  echo "名字过滤 '${VIDEO_FILTER}': ${#videos[@]} 个视频匹配"
fi

# 取前 N
if [ ${FIRST_N} -gt 0 ] && [ ${FIRST_N} -lt ${#videos[@]} ]; then
  videos=("${videos[@]:0:${FIRST_N}}")
fi

# ── 过滤时长 >10min 的视频 ──────────────────────────────────
MAX_DURATION_SEC="${MAX_DURATION_SEC:-600}"  # 默认 10 分钟
filtered=()
skipped_long=()
for v in "${videos[@]}"; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "${v}" 2>/dev/null || echo "0")
  dur_int=${dur%%.*}
  if [ "${dur_int:-0}" -gt "${MAX_DURATION_SEC}" ]; then
    skipped_long+=("$(basename "${v}") (${dur%%.*}s)")
  else
    filtered+=("${v}")
  fi
done
if [ ${#skipped_long[@]} -gt 0 ]; then
  echo "跳过 ${#skipped_long[@]} 个超长视频 (>${MAX_DURATION_SEC}s):"
  for s in "${skipped_long[@]}"; do
    echo "  - ${s}"
  done
fi
videos=("${filtered[@]}")

echo "共 ${#videos[@]} 个视频待处理"
echo ""

# Dry run: 只列出视频
if [ ${DRY_RUN} -eq 1 ]; then
  echo "--- Dry Run: 视频列表 ---"
  for i in "${!videos[@]}"; do
    base=$(basename "${videos[$i]}" .mp4)
    s1_status=""
    s2_status=""
    ev="${OUT_DIR}/${base}_events.json"
    if [ "${REFINE_MODE}" = "uca" ]; then
      s2f="${OUT_DIR}/${base}_events_uca.json"
    else
      s2f="${OUT_DIR}/${base}_events_vector_flat.json"
    fi
    if [ -f "${ev}" ]; then s1_status="✓ 已有"; else s1_status="✗ 待跑"; fi
    if [ -f "${s2f}" ]; then s2_status="✓ 已有"; else s2_status="✗ 待跑"; fi
    printf "  %3d. %-45s  S1: %-8s  S2: %-8s\n" "$((i+1))" "${base}" "${s1_status}" "${s2_status}"
  done
  echo ""
  echo "Dry run 完成，未实际运行。去掉 --dry-run 以执行。"
  exit 0
fi

# ── 运行 Pipeline ─────────────────────────────────────────
total=${#videos[@]}
s1_ok=0
s1_skip=0
s1_fail=0
s2_ok=0
s2_skip=0
s2_fail=0
start_all=$(date +%s)

for idx in "${!videos[@]}"; do
  video_path="${videos[$idx]}"
  base=$(basename "${video_path}" .mp4)
  num=$((idx + 1))

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "[${num}/${total}] ${base}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  events_json="${OUT_DIR}/${base}_events.json"
  clips_json="${OUT_DIR}/${base}_clips.json"
  # Stage 2 output depends on refine mode
  if [ "${REFINE_MODE}" = "uca" ]; then
    s2_output="${OUT_DIR}/${base}_events_uca.json"
  else
    s2_output="${OUT_DIR}/${base}_events_vector_flat.json"
  fi

  # ── Stage 1 ─────────────────────────────────────────
  if [ ${SKIP_STAGE1} -eq 1 ]; then
    if [ -f "${events_json}" ] && [ -f "${clips_json}" ]; then
      echo "  [Stage 1] 跳过 (已有输出)"
      s1_skip=$((s1_skip + 1))
    else
      echo "  [Stage 1] ✗ 缺少已有输出，但指定了 --skip-stage1"
      s1_skip=$((s1_skip + 1))
    fi
  elif [ ${RESUME} -eq 1 ] && [ -f "${events_json}" ] && [ -f "${clips_json}" ]; then
    echo "  [Stage 1] 断点续跑，跳过 (已有输出)"
    s1_skip=$((s1_skip + 1))
  else
    echo "  [Stage 1] 运行 YOLO + ${TRACKER} 追踪 + 事件切片..."
    s1_start=$(date +%s)
    if conda run -n "${CONDA_ENV}" python -m video.factory.coordinator video \
        "${video_path}" \
        --out-dir "${OUT_DIR}" \
        --model "${MODEL}" \
        --tracker "${TRACKER}" \
        --conf "${CONF}" \
        --iou "${IOU}"; then
      s1_end=$(date +%s)
      s1_ok=$((s1_ok + 1))
      echo "  [Stage 1] ✓ 完成 ($((s1_end - s1_start))s)"
    else
      s1_fail=$((s1_fail + 1))
      echo "  [Stage 1] ✗ 失败"
      # Stage 1 失败则跳过该视频的 Stage 2
      continue
    fi
  fi

  # ── Stage 2 ─────────────────────────────────────────
  if [ ${SKIP_STAGE2} -eq 1 ]; then
    if [ -f "${s2_output}" ]; then
      echo "  [Stage 2] 跳过 (已有输出)"
      s2_skip=$((s2_skip + 1))
    else
      echo "  [Stage 2] ✗ 缺少已有输出，但指定了 --skip-stage2"
      s2_skip=$((s2_skip + 1))
    fi
  elif [ ! -f "${events_json}" ] || [ ! -f "${clips_json}" ]; then
    echo "  [Stage 2] ✗ 跳过 (缺少 Stage 1 输出)"
    s2_skip=$((s2_skip + 1))
  elif [ ${RESUME} -eq 1 ] && [ -f "${s2_output}" ]; then
    echo "  [Stage 2] 断点续跑，跳过 (已有输出)"
    s2_skip=$((s2_skip + 1))
  else
    echo "  [Stage 2] 运行 LLM 精炼 (${REFINE_MODE} 模式, ${LLM_MODEL})..."
    s2_start=$(date +%s)
    if conda run -n "${CONDA_ENV}" python -m video.factory.coordinator refine \
        --events "${events_json}" \
        --clips "${clips_json}" \
        --mode "${REFINE_MODE}" \
        --frames-per-sec "${FRAMES_PER_SEC}" \
        --min-frames "${MIN_FRAMES}" \
        --max-frames "${MAX_FRAMES}" \
        --model "${LLM_MODEL}" \
        --temperature "${TEMPERATURE}"; then
      s2_end=$(date +%s)
      s2_ok=$((s2_ok + 1))
      echo "  [Stage 2] ✓ 完成 ($((s2_end - s2_start))s)"
    else
      s2_fail=$((s2_fail + 1))
      echo "  [Stage 2] ✗ 失败"
    fi
  fi
done

end_all=$(date +%s)
elapsed=$((end_all - start_all))

# ── 汇总 ──────────────────────────────────────────────────
echo ""
echo "========================================"
echo " 完成！总耗时: ${elapsed}s"
echo "========================================"
echo "视频总数:    ${total}"
echo "Stage 1:     ${s1_ok} 成功 / ${s1_skip} 跳过 / ${s1_fail} 失败"
echo "Stage 2:     ${s2_ok} 成功 / ${s2_skip} 跳过 / ${s2_fail} 失败"
echo ""
echo "输出目录: ${OUT_DIR}"
echo "  *_events.json             ← Stage 1 原始事件"
echo "  *_clips.json              ← Stage 1 切片片段"
echo "  *_events_uca.json         ← Stage 2 UCA 稠密描述 (当前模式)"
echo "  *_events_vector_flat.json ← Stage 2 vector 模式 (如果切换)"
echo ""
echo "下一步: 将 *_events_uca.json 用于 UCA 格式评估"

if [ ${s1_fail} -gt 0 ] || [ ${s2_fail} -gt 0 ]; then
  echo ""
  echo "⚠ 有失败的视频，可用 --resume 断点续跑"
  exit 1
fi
