#!/usr/bin/env python3
"""
单视频直接评估：将流水线精炼输出与 UCFCrime_Test.json 地面真值对比。

评估维度：
  1. 时间对齐 (Temporal IoU)
  2. 对象类型匹配
  3. 场景区域匹配
  4. 事件描述语义相似度

输出：评估报告 JSON + 可读摘要

用法：
  python agent/test/eval_single_video.py \
    --vector-flat agent/test/generated/pipeline_eval_part4_single/stage1/Normal_Videos594_x264_events_vector_flat.json \
    --ground-truth agent/test/generated/pipeline_eval_part4_single/ground_truth/Normal_Videos594_x264_ground_truth.json
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_VECTOR_FLAT = (
    ROOT_DIR / "agent" / "test" / "generated" / "pipeline_eval_part4_single"
    / "stage1" / "Normal_Videos594_x264_events_vector_flat.json"
)
DEFAULT_GROUND_TRUTH = (
    ROOT_DIR / "agent" / "test" / "generated" / "pipeline_eval_part4_single"
    / "ground_truth" / "Normal_Videos594_x264_ground_truth.json"
)
DEFAULT_OUTPUT_DIR = ROOT_DIR / "agent" / "test" / "generated" / "eval_reports"


def compute_temporal_iou(
    start_a: float, end_a: float,
    start_b: float, end_b: float,
) -> float:
    """计算两个时间段的时间 IoU"""
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    if union <= 0:
        return 0.0
    return intersection / union


def compute_temporal_recall(
    pred_start: float, pred_end: float,
    gt_start: float, gt_end: float,
) -> float:
    """预测段对 GT 段的时间覆盖率（pred ∩ gt / gt 长度）"""
    intersection = max(0.0, min(pred_end, gt_end) - max(pred_start, gt_start))
    gt_len = gt_end - gt_start
    if gt_len <= 0:
        return 0.0
    return intersection / gt_len


def normalize_text(text: str) -> str:
    """简单文本归一化"""
    return text.lower().strip()


def extract_entities_from_text(text: str) -> dict[str, set[str]]:
    """从文本中提取关键实体（对象类型、颜色、区域）的启发式方法"""
    low = text.lower()
    entities: dict[str, set[str]] = {
        "objects": set(),
        "colors": set(),
        "zones": set(),
    }

    object_patterns = {
        "person": ["man", "woman", "person", "people", "passers-by", "pedestrian", "driver"],
        "car": ["car", "vehicle", "truck", "bus", "suv", "van"],
        "motorcycle": ["motorcycle", "bike", "bicycle"],
        "dog": ["dog", "puppy"],
    }
    for obj_type, patterns in object_patterns.items():
        if any(p in low for p in patterns):
            entities["objects"].add(obj_type)

    color_patterns = [
        "black", "white", "red", "blue", "green", "yellow",
        "gray", "silver", "purple", "pink", "brown", "orange",
    ]
    for c in color_patterns:
        if c in low:
            entities["colors"].add(c)

    zone_patterns = {
        "road": ["road", "street", "highway", "intersection"],
        "parking": ["parking", "gas station", "forecourt", "pump"],
        "room": ["room", "office", "building", "door", "counter"],
        "store": ["store", "shop", "supermarket", "toy store"],
        "sidewalk": ["sidewalk", "walkway"],
    }
    for zone, patterns in zone_patterns.items():
        if any(p in low for p in patterns):
            entities["zones"].add(zone)

    return entities


def load_data(
    vector_flat_path: Path,
    ground_truth_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """加载流水线输出和地面真值"""
    if not vector_flat_path.exists():
        raise FileNotFoundError(f"流水线输出不存在: {vector_flat_path}")
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"地面真值不存在: {ground_truth_path}")

    pipeline = json.loads(vector_flat_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(ground_truth_path.read_text(encoding="utf-8"))
    return pipeline, ground_truth


def evaluate(
    pipeline: dict[str, Any],
    ground_truth: dict[str, Any],
) -> dict[str, Any]:
    """运行全部评估维度"""
    video_id = pipeline.get("video_id", "unknown")
    gt_duration = ground_truth.get("duration", 0) or 0
    pipeline_events = pipeline.get("events", [])
    gt_sentences = ground_truth.get("sentences", [])
    gt_timestamps = ground_truth.get("timestamps", [])

    n_pred = len(pipeline_events)
    n_gt = len(gt_sentences)

    # ── 1. 时间对齐 ─────────────────────────────────
    best_ious: list[float] = []
    per_gt_temporal_recall: list[dict[str, Any]] = []
    per_pred_temporal_recall: list[dict[str, Any]] = []
    matched_pairs: list[dict[str, Any]] = []

    # 对每个 GT，找最佳匹配的预测事件
    for gt_idx, (ts, sent) in enumerate(zip(gt_timestamps, gt_sentences)):
        gt_start = float(ts[0]) if len(ts) >= 2 else 0.0
        gt_end = float(ts[1]) if len(ts) >= 2 else 0.0

        best_iou = 0.0
        best_pred_idx = -1
        for pred_idx, pe in enumerate(pipeline_events):
            ps = float(pe.get("start_time", 0))
            pe_t = float(pe.get("end_time", 0))
            iou = compute_temporal_iou(ps, pe_t, gt_start, gt_end)
            if iou > best_iou:
                best_iou = iou
                best_pred_idx = pred_idx

        best_ious.append(best_iou)
        recall = compute_temporal_recall(
            float(pipeline_events[best_pred_idx].get("start_time", 0)) if best_pred_idx >= 0 else 0,
            float(pipeline_events[best_pred_idx].get("end_time", 0)) if best_pred_idx >= 0 else 0,
            gt_start, gt_end,
        ) if best_pred_idx >= 0 else 0.0

        per_gt_temporal_recall.append({
            "gt_idx": gt_idx,
            "gt_range": f"{gt_start:.1f}s-{gt_end:.1f}s",
            "gt_sentence": sent,
            "best_pred_idx": best_pred_idx,
            "best_iou": round(best_iou, 4),
            "temporal_recall": round(recall, 4),
            "pred_range": (
                f"{pipeline_events[best_pred_idx].get('start_time', 0):.1f}s-"
                f"{pipeline_events[best_pred_idx].get('end_time', 0):.1f}s"
                if best_pred_idx >= 0 else "N/A"
            ),
        })

    # 对每个预测，找最佳匹配的 GT
    for pred_idx, pe in enumerate(pipeline_events):
        ps = float(pe.get("start_time", 0))
        pe_t = float(pe.get("end_time", 0))
        best_iou = 0.0
        best_gt_idx = -1
        for gt_idx, ts in enumerate(gt_timestamps):
            gs = float(ts[0]) if len(ts) >= 2 else 0.0
            ge = float(ts[1]) if len(ts) >= 2 else 0.0
            iou = compute_temporal_iou(ps, pe_t, gs, ge)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        per_pred_temporal_recall.append({
            "pred_idx": pred_idx,
            "pred_range": f"{ps:.1f}s-{pe_t:.1f}s",
            "pred_event": pe.get("event_text", "")[:120],
            "best_gt_idx": best_gt_idx,
            "best_iou": round(best_iou, 4),
        })

    mean_temporal_iou = round(sum(best_ious) / len(best_ious), 4) if best_ious else 0.0

    # ── 2. 对象类型匹配 ─────────────────────────────
    object_matches = []
    for gt_idx, sent in enumerate(gt_sentences):
        gt_entities = extract_entities_from_text(sent)
        matched_pred_idx = -1
        best_match_score = 0.0
        for pred_idx, pe in enumerate(pipeline_events):
            pred_type = pe.get("object_type", "unknown").lower()
            pred_entities = extract_entities_from_text(pe.get("event_text", ""))
            # 简单 Jaccard on object types
            gt_objs = gt_entities["objects"] or {pred_type}  # fallback
            pred_objs = pred_entities["objects"] or {pred_type}
            objs_union = len(gt_objs | pred_objs)
            if objs_union == 0:
                continue
            score = len(gt_objs & pred_objs) / objs_union
            if score > best_match_score:
                best_match_score = score
                matched_pred_idx = pred_idx

        object_matches.append({
            "gt_idx": gt_idx,
            "gt_sentence": sent[:80],
            "gt_objects": list(gt_entities["objects"]),
            "best_pred_idx": matched_pred_idx,
            "pred_object_type": (
                pipeline_events[matched_pred_idx].get("object_type", "unknown")
                if matched_pred_idx >= 0 else "N/A"
            ),
            "jaccard_score": round(best_match_score, 4),
        })

    mean_object_jaccard = round(
        sum(m["jaccard_score"] for m in object_matches) / len(object_matches), 4,
    ) if object_matches else 0.0

    # ── 3. 场景区域匹配 ─────────────────────────────
    gt_zones_all: set[str] = set()
    pred_zones_all: set[str] = set()
    for sent in gt_sentences:
        gt_zones_all |= extract_entities_from_text(sent)["zones"]
    for pe in pipeline_events:
        scene = pe.get("scene_zone", "unknown").lower()
        if scene and scene != "unknown":
            pred_zones_all.add(scene)
        pred_zones_all |= extract_entities_from_text(pe.get("event_text", ""))["zones"]

    zone_intersection = gt_zones_all & pred_zones_all
    zone_union = gt_zones_all | pred_zones_all
    zone_jaccard = round(
        len(zone_intersection) / len(zone_union), 4,
    ) if zone_union else 0.0

    # ── 4. 覆盖率 ──────────────────────────────────
    # Time coverage: what fraction of video duration has at least one event?
    total_pred_time = 0.0
    covered_segments: list[tuple[float, float]] = []
    for pe in pipeline_events:
        ps = float(pe.get("start_time", 0))
        pe_t = float(pe.get("end_time", 0))
        covered_segments.append((ps, pe_t))
    # Merge overlapping
    covered_segments.sort()
    merged: list[tuple[float, float]] = []
    for s, e in covered_segments:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    for s, e in merged:
        total_pred_time += (e - s)

    gt_total_time = 0.0
    for ts in gt_timestamps:
        gt_total_time += float(ts[1]) - float(ts[0])

    pred_time_coverage = round(total_pred_time / gt_duration, 4) if gt_duration > 0 else 0.0
    gt_time_coverage = round(gt_total_time / gt_duration, 4) if gt_duration > 0 else 0.0

    # ── 5. 汇总评分 ─────────────────────────────────
    # 综合分 = 加权组合
    temporal_weight = 0.35
    object_weight = 0.25
    zone_weight = 0.15
    coverage_weight = 0.10
    density_weight = 0.15  # event density match

    # Event density match (GT sentences / pred events ratio)
    density_ratio = min(n_pred / n_gt, n_gt / n_pred) if n_pred > 0 and n_gt > 0 else 0.0

    composite_score = (
        temporal_weight * mean_temporal_iou
        + object_weight * mean_object_jaccard
        + zone_weight * zone_jaccard
        + coverage_weight * pred_time_coverage
        + density_weight * density_ratio
    )

    return {
        "video_id": video_id,
        "video_duration_sec": gt_duration,
        "pipeline": {
            "event_count": n_pred,
            "time_coverage": pred_time_coverage,
            "events": [
                {
                    "start": float(e.get("start_time", 0)),
                    "end": float(e.get("end_time", 0)),
                    "object_type": e.get("object_type", "unknown"),
                    "object_color": e.get("object_color", "unknown"),
                    "scene_zone": e.get("scene_zone", "unknown"),
                    "event_text": e.get("event_text", "")[:150],
                }
                for e in pipeline_events
            ],
        },
        "ground_truth": {
            "event_count": n_gt,
            "time_coverage": gt_time_coverage,
            "events": [
                {
                    "start": float(ts[0]) if len(ts) >= 2 else 0.0,
                    "end": float(ts[1]) if len(ts) >= 2 else 0.0,
                    "sentence": sent,
                }
                for ts, sent in zip(gt_timestamps, gt_sentences)
            ],
        },
        "metrics": {
            "temporal_iou": {
                "mean": mean_temporal_iou,
                "per_gt": per_gt_temporal_recall,
                "per_pred": per_pred_temporal_recall,
            },
            "object_match": {
                "mean_jaccard": mean_object_jaccard,
                "per_gt": object_matches,
            },
            "zone_match": {
                "gt_zones": sorted(gt_zones_all),
                "pred_zones": sorted(pred_zones_all),
                "intersection": sorted(zone_intersection),
                "jaccard": zone_jaccard,
            },
            "coverage": {
                "pred_time_coverage": pred_time_coverage,
                "gt_time_coverage": gt_time_coverage,
                "pred_covered_sec": round(total_pred_time, 1),
                "gt_covered_sec": round(gt_total_time, 1),
            },
            "density": {
                "pred_event_count": n_pred,
                "gt_event_count": n_gt,
                "ratio": round(density_ratio, 4),
            },
        },
        "composite_score": round(composite_score, 4),
        "scores_breakdown": {
            "temporal_iou": round(mean_temporal_iou, 4),
            "object_jaccard": round(mean_object_jaccard, 4),
            "zone_jaccard": round(zone_jaccard, 4),
            "time_coverage": round(pred_time_coverage, 4),
            "density_ratio": round(density_ratio, 4),
        },
    }


def print_summary(result: dict[str, Any]) -> None:
    """打印可读的评估摘要"""
    m = result["metrics"]
    p = result["pipeline"]
    g = result["ground_truth"]
    sb = result["scores_breakdown"]

    print("=" * 72)
    print(f"  评估报告: {result['video_id']}")
    print("=" * 72)
    print(f"  视频时长: {result['video_duration_sec']:.1f}s")
    print(f"  流水线事件: {p['event_count']}   地面真值: {g['event_count']}")
    print()

    print("  ── 综合评分 ──")
    print(f"  Composite Score:        {result['composite_score']:.4f}")
    print()

    print("  ── 分项得分 ──")
    print(f"  时间 IoU (Temporal):    {sb['temporal_iou']:.4f}  (权重 0.35)")
    print(f"  对象匹配 (Object):      {sb['object_jaccard']:.4f}  (权重 0.25)")
    print(f"  场景匹配 (Zone):        {sb['zone_jaccard']:.4f}  (权重 0.15)")
    print(f"  时间覆盖 (Coverage):    {sb['time_coverage']:.4f}  (权重 0.10)")
    print(f"  密度比例 (Density):     {sb['density_ratio']:.4f}  (权重 0.15)")
    print()

    print("  ── 时间对齐详情 (GT → 最佳 Pred) ──")
    for item in m["temporal_iou"]["per_gt"]:
        status = "✓" if item["best_iou"] > 0.1 else "✗"
        print(f"  {status} GT[{item['gt_idx']}] {item['gt_range']:>16s} → "
              f"Pred[{item['best_pred_idx']}] {item['pred_range']:>16s}  "
              f"(IoU={item['best_iou']:.3f}, Recall={item['temporal_recall']:.3f})")
        if item["gt_sentence"]:
            s = item["gt_sentence"][:100]
            print(f"     GT: {s}")

    print()
    print("  ── 对象匹配详情 ──")
    for item in m["object_match"]["per_gt"]:
        print(f"  GT[{item['gt_idx']}]: gt_objects={item['gt_objects']} → "
              f"pred_type={item['pred_object_type']} (Jaccard={item['jaccard_score']:.3f})")

    print()
    print("  ── 场景区域 ──")
    print(f"  GT zones:   {m['zone_match']['gt_zones']}")
    print(f"  Pred zones: {m['zone_match']['pred_zones']}")
    print(f"  交集:        {m['zone_match']['intersection']}")
    print(f"  Zone Jaccard: {m['zone_match']['jaccard']:.4f}")

    print()
    print("  ── 覆盖情况 ──")
    print(f"  Pred 覆盖时长: {m['coverage']['pred_covered_sec']:.1f}s / {result['video_duration_sec']:.1f}s "
          f"({p['time_coverage']:.1%})")
    print(f"  GT 覆盖时长:   {m['coverage']['gt_covered_sec']:.1f}s / {result['video_duration_sec']:.1f}s "
          f"({g['time_coverage']:.1%})")

    print()
    print("  ── 事件密度 ──")
    print(f"  Pred: {m['density']['pred_event_count']} events  vs  "
          f"GT: {m['density']['gt_event_count']} events  "
          f"(ratio={m['density']['ratio']:.3f})")

    print()
    print("=" * 72)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="单视频管道评估：流水线输出 vs 地面真值",
    )
    p.add_argument("--vector-flat", type=str, default=str(DEFAULT_VECTOR_FLAT),
                   help="流水线 vector_flat JSON 路径")
    p.add_argument("--ground-truth", type=str, default=str(DEFAULT_GROUND_TRUTH),
                   help="地面真值 JSON 路径")
    p.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
                   help="评估报告输出目录")
    return p


def main() -> None:
    args = build_parser().parse_args()
    vector_flat_path = Path(args.vector_flat).resolve()
    ground_truth_path = Path(args.ground_truth).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    pipeline, ground_truth = load_data(vector_flat_path, ground_truth_path)
    video_id = pipeline.get("video_id", "unknown")

    result = evaluate(pipeline, ground_truth)

    # 保存报告
    report_path = output_dir / f"{video_id}_eval_report.json"
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print_summary(result)
    print(f"\n详细报告已保存: {report_path}")


if __name__ == "__main__":
    main()
