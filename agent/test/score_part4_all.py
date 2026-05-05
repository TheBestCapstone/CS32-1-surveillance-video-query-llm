#!/usr/bin/env python3
"""
Part4 全量打分：流水线输出 vs 地面真值，含 LLM 文字相似度评分。

评分维度：
  1. 规则指标：Temporal IoU, Object Match, Zone Match, Time Coverage, Density
  2. LLM 文字相似度（gpt-4o）：逐条 Pred vs GT 对比

输出：
  - part4_video_result.json   （结构化打分数据）
  - part4_video_result.md     （可读报告）

支持断点续跑：已打分的视频自动跳过。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ── 默认路径 ─────────────────────────────────────────────
DEFAULT_PIPELINE_DIR = ROOT_DIR / "agent" / "test" / "generated" / "pipeline_eval_part4_full"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "agent" / "test" / "generated" / "part4_video_result.json"
DEFAULT_OUTPUT_MD = ROOT_DIR / "agent" / "test" / "generated" / "part4_video_result.md"


# ══════════════════════════════════════════════════════════════
# 规则指标计算
# ══════════════════════════════════════════════════════════════

def compute_temporal_iou(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
    intersection = max(0.0, min(end_a, end_b) - max(start_a, start_b))
    union = max(end_a, end_b) - min(start_a, start_b)
    return intersection / union if union > 0 else 0.0


def compute_temporal_recall(pred_start: float, pred_end: float, gt_start: float, gt_end: float) -> float:
    intersection = max(0.0, min(pred_end, gt_end) - max(pred_start, gt_start))
    gt_len = gt_end - gt_start
    return intersection / gt_len if gt_len > 0 else 0.0


def extract_entities_from_text(text: str) -> dict[str, set[str]]:
    low = text.lower()
    entities: dict[str, set[str]] = {"objects": set(), "colors": set(), "zones": set()}

    object_patterns = {
        "person": ["man", "woman", "person", "people", "passers-by", "pedestrian", "driver", "adult", "staff", "lady"],
        "car": ["car", "vehicle", "truck", "bus", "suv", "van", "mini"],
        "motorcycle": ["motorcycle", "bike", "bicycle", "tricycle"],
        "dog": ["dog", "puppy"],
        "child": ["baby", "child", "kid"],
    }
    for obj_type, patterns in object_patterns.items():
        if any(p in low for p in patterns):
            entities["objects"].add(obj_type)

    colors = ["black", "white", "red", "blue", "green", "yellow", "gray", "silver", "purple", "pink", "brown", "orange"]
    for c in colors:
        if c in low:
            entities["colors"].add(c)

    zone_patterns = {
        "road": ["road", "street", "highway", "intersection"],
        "parking": ["parking", "gas station", "forecourt", "pump", "refueling"],
        "room": ["room", "office", "building", "door", "counter", "workstation"],
        "store": ["store", "shop", "supermarket", "toy store"],
        "sidewalk": ["sidewalk", "walkway"],
        "yard": ["yard"],
    }
    for zone, patterns in zone_patterns.items():
        if any(p in low for p in patterns):
            entities["zones"].add(zone)

    return entities


def compute_rule_based_scores(pipeline: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, Any]:
    """计算所有规则指标"""
    gt_duration = ground_truth.get("duration", 0) or 0
    pipeline_events = pipeline.get("events", [])
    gt_sentences = ground_truth.get("sentences", [])
    gt_timestamps = ground_truth.get("timestamps", [])

    n_pred = len(pipeline_events)
    n_gt = len(gt_sentences)

    # ── Temporal IoU ──
    best_ious = []
    per_gt = []
    for gt_idx, (ts, sent) in enumerate(zip(gt_timestamps, gt_sentences)):
        gs, ge = float(ts[0]), float(ts[1])
        best_iou, best_idx = 0.0, -1
        for pi, pe in enumerate(pipeline_events):
            ps, pe_t = float(pe.get("start_time", 0)), float(pe.get("end_time", 0))
            iou = compute_temporal_iou(ps, pe_t, gs, ge)
            if iou > best_iou:
                best_iou, best_idx = iou, pi
        best_ious.append(best_iou)
        recall = compute_temporal_recall(
            float(pipeline_events[best_idx].get("start_time", 0)) if best_idx >= 0 else 0,
            float(pipeline_events[best_idx].get("end_time", 0)) if best_idx >= 0 else 0,
            gs, ge,
        ) if best_idx >= 0 else 0.0
        per_gt.append({"gt_idx": gt_idx, "best_pred_idx": best_idx, "iou": round(best_iou, 4), "recall": round(recall, 4)})

    mean_temporal_iou = round(sum(best_ious) / len(best_ious), 4) if best_ious else 0.0

    # ── Object Match ──
    object_jaccards = []
    for gt_idx, sent in enumerate(gt_sentences):
        gt_objs = extract_entities_from_text(sent)["objects"]
        best_jac, best_idx = 0.0, -1
        for pi, pe in enumerate(pipeline_events):
            pred_type = pe.get("object_type", "unknown").lower()
            pred_objs = extract_entities_from_text(pe.get("event_text", ""))["objects"] or {pred_type}
            union = len(gt_objs | pred_objs)
            jac = len(gt_objs & pred_objs) / union if union > 0 else 0.0
            if jac > best_jac:
                best_jac, best_idx = jac, pi
        object_jaccards.append(best_jac)

    mean_object_jaccard = round(sum(object_jaccards) / len(object_jaccards), 4) if object_jaccards else 0.0

    # ── Zone Match ──
    gt_zones, pred_zones = set(), set()
    for sent in gt_sentences:
        gt_zones |= extract_entities_from_text(sent)["zones"]
    for pe in pipeline_events:
        scene = pe.get("scene_zone", "unknown").lower()
        if scene and scene != "unknown":
            pred_zones.add(scene)
        pred_zones |= extract_entities_from_text(pe.get("event_text", ""))["zones"]
    zone_union = gt_zones | pred_zones
    zone_jaccard = round(len(gt_zones & pred_zones) / len(zone_union), 4) if zone_union else 0.0

    # ── Time Coverage ──
    covered = []
    for pe in pipeline_events:
        covered.append((float(pe.get("start_time", 0)), float(pe.get("end_time", 0))))
    covered.sort()
    merged = []
    for s, e in covered:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    pred_time = sum(e - s for s, e in merged)
    gt_time = sum(float(ts[1]) - float(ts[0]) for ts in gt_timestamps)
    pred_coverage = round(pred_time / gt_duration, 4) if gt_duration > 0 else 0.0
    gt_coverage = round(gt_time / gt_duration, 4) if gt_duration > 0 else 0.0

    # ── Density ──
    density = round(min(n_pred / n_gt, n_gt / n_pred), 4) if n_pred > 0 and n_gt > 0 else 0.0

    # ── Composite ──
    composite = round(
        0.30 * mean_temporal_iou
        + 0.25 * mean_object_jaccard
        + 0.15 * zone_jaccard
        + 0.10 * pred_coverage
        + 0.10 * density
        + 0.10 * 0.0,  # llm_score placeholder, filled separately
        4,
    )

    return {
        "temporal_iou": mean_temporal_iou,
        "object_jaccard": mean_object_jaccard,
        "zone_jaccard": zone_jaccard,
        "time_coverage": pred_coverage,
        "gt_time_coverage": gt_coverage,
        "density_ratio": density,
        "composite_rule_only": composite,
        "pred_event_count": n_pred,
        "gt_event_count": n_gt,
    }


# ══════════════════════════════════════════════════════════════
# LLM 文字相似度评分
# ══════════════════════════════════════════════════════════════

LLM_SCORE_PROMPT = """You are evaluating a video surveillance event extraction pipeline.
Compare the pipeline's extracted event description (Pred) against the ground truth human description (GT).

Rate the text similarity on a scale of 1 to 10:
- 1-2: Completely different subjects, actions, or locations. Factual error.
- 3-4: Same general domain (e.g., "road scene") but different specifics.
- 5-6: Partial overlap — some shared elements but missing key details or different focus.
- 7-8: Good match — captures the main action/subject, minor differences in detail.
- 9-10: Excellent match — nearly identical in subject, action, and key details.

Output ONLY a JSON object with:
{{
  "score": <integer 1-10>,
  "reason": "<one sentence explaining the score>"
}}

Pred: {pred_text}
GT: {gt_text}"""


def score_text_similarity_llm(
    pred_event: dict[str, Any],
    gt_sentence: str,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """用 LLM 对单条 Pred vs GT 打分"""
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")

    client = OpenAI()
    pred_text = pred_event.get("event_text", "")
    prompt = LLM_SCORE_PROMPT.format(pred_text=pred_text, gt_text=gt_sentence)

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=150,
        )
        content = resp.choices[0].message.content or "{}"
        # 提取 JSON 对象（支持嵌套）
        # 找到第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            json_str = content[start:end + 1]
            result = json.loads(json_str)
            return {
                "score": int(result.get("score", 0)),
                "reason": str(result.get("reason", "")),
            }
        return {"score": 0, "reason": f"parse_error: no_json_found: {content[:80]}"}
    except Exception as e:
        return {"score": 0, "reason": f"api_error: {str(e)[:80]}"}


def score_video_with_llm(
    pipeline: dict[str, Any],
    ground_truth: dict[str, Any],
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """对单个视频的所有 Pred vs GT 组合做 LLM 打分"""
    pipeline_events = pipeline.get("events", [])
    gt_timestamps = ground_truth.get("timestamps", [])
    gt_sentences = ground_truth.get("sentences", [])

    # 对每个 GT，找时间上最匹配的 Pred
    per_gt_scores = []
    all_scores = []

    for gt_idx, (ts, sent) in enumerate(zip(gt_timestamps, gt_sentences)):
        gs, ge = float(ts[0]), float(ts[1])

        # 找最佳时间匹配的 Pred
        best_iou, best_idx = 0.0, -1
        for pi, pe in enumerate(pipeline_events):
            ps, pe_t = float(pe.get("start_time", 0)), float(pe.get("end_time", 0))
            iou = compute_temporal_iou(ps, pe_t, gs, ge)
            if iou > best_iou:
                best_iou, best_idx = iou, pi

        if best_idx >= 0:
            result = score_text_similarity_llm(pipeline_events[best_idx], sent, model=model)
        else:
            result = {"score": 0, "reason": "no matching pred event"}

        all_scores.append(result["score"])
        per_gt_scores.append({
            "gt_idx": gt_idx,
            "best_pred_idx": best_idx,
            "temporal_iou": round(best_iou, 4),
            "llm_score": result["score"],
            "llm_reason": result["reason"],
        })

    mean_llm_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return {
        "llm_score_mean": mean_llm_score,
        "llm_score_per_gt": per_gt_scores,
        "llm_model": model,
    }


# ══════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════

def load_all_data(pipeline_dir: Path) -> list[dict[str, Any]]:
    """加载所有视频的 pipeline 输出和 ground truth"""
    stage2_dir = pipeline_dir / "stage2"
    gt_dir = pipeline_dir / "ground_truth"
    stage1_dir = pipeline_dir / "stage1"

    # vector_flat 可能在 stage2/ 或 stage1/（取决于 pipeline 脚本配置）
    vector_flat_files = []
    for d in [stage2_dir, stage1_dir]:
        if d.is_dir():
            vector_flat_files.extend(sorted(d.glob("*_events_vector_flat.json")))

    if not vector_flat_files:
        raise FileNotFoundError(f"未找到 vector_flat 文件，检查 {stage2_dir} 和 {stage1_dir}")
    print(f"找到 {len(vector_flat_files)} 个 vector_flat 文件")

    items = []
    for vf_path in vector_flat_files:
        video_id = vf_path.stem.replace("_events_vector_flat", "")
        gt_path = gt_dir / f"{video_id}_ground_truth.json"

        if not gt_path.exists():
            print(f"  ⚠ {video_id}: 缺少 ground_truth 文件，跳过")
            continue

        pipeline = json.loads(vf_path.read_text(encoding="utf-8"))
        ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
        items.append({
            "video_id": video_id,
            "pipeline": pipeline,
            "ground_truth": ground_truth,
        })

    print(f"加载 {len(items)} 个完整数据对")
    return items


def score_all_videos(
    items: list[dict[str, Any]],
    output_json: Path,
    *,
    skip_llm: bool = False,
    llm_model: str = "gpt-5.4-mini",
    resume: bool = False,
) -> dict[str, Any]:
    """对所有视频打分，支持断点续跑"""
    # 断点续跑：读取已有结果
    existing: dict[str, dict[str, Any]] = {}
    if resume and output_json.exists():
        old = json.loads(output_json.read_text(encoding="utf-8"))
        for v in old.get("videos", []):
            existing[v["video_id"]] = v
        print(f"断点续跑：已有 {len(existing)} 个结果")

    results: list[dict[str, Any]] = []
    total = len(items)

    for idx, item in enumerate(items, 1):
        video_id = item["video_id"]
        print(f"\n[{idx}/{total}] {video_id}", end="", flush=True)

        # 检查是否已有结果
        if video_id in existing and existing[video_id].get("llm_score_mean") is not None:
            results.append(existing[video_id])
            print(" → 跳过（已有结果）")
            continue

        pipeline = item["pipeline"]
        ground_truth = item["ground_truth"]

        # 规则指标
        rule_scores = compute_rule_based_scores(pipeline, ground_truth)

        # LLM 评分
        llm_result = None
        if not skip_llm:
            try:
                llm_result = score_video_with_llm(pipeline, ground_truth, model=llm_model)
                print(f" | LLM={llm_result['llm_score_mean']}", end="", flush=True)
            except Exception as e:
                print(f" | LLM error: {e}", end="", flush=True)
                llm_result = {"llm_score_mean": None, "llm_score_per_gt": [], "llm_model": llm_model}

        # 综合分（含 LLM）
        llm_mean = llm_result["llm_score_mean"] / 10.0 if llm_result and llm_result["llm_score_mean"] is not None else 0.0
        composite = round(
            0.30 * rule_scores["temporal_iou"]
            + 0.20 * rule_scores["object_jaccard"]
            + 0.10 * rule_scores["zone_jaccard"]
            + 0.10 * rule_scores["time_coverage"]
            + 0.10 * rule_scores["density_ratio"]
            + 0.20 * llm_mean,
            4,
        )

        result = {
            "video_id": video_id,
            "duration_sec": ground_truth.get("duration", 0),
            "rule_scores": rule_scores,
            "llm_scores": llm_result,
            "composite_score": composite,
        }
        results.append(result)

        # 每 5 个视频保存一次中间结果
        if idx % 5 == 0 or idx == total:
            _save_intermediate(output_json, results)

    print(f"\n完成 {len(results)} 个视频打分")
    return _save_intermediate(output_json, results)


def _save_intermediate(output_json: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    """保存中间结果"""
    all_composite = [r["composite_score"] for r in results if r["composite_score"] is not None]
    all_temporal = [r["rule_scores"]["temporal_iou"] for r in results]
    all_object = [r["rule_scores"]["object_jaccard"] for r in results]
    all_zone = [r["rule_scores"]["zone_jaccard"] for r in results]
    all_llm = [
        r["llm_scores"]["llm_score_mean"] / 10.0
        for r in results
        if r.get("llm_scores") and r["llm_scores"].get("llm_score_mean") is not None
    ]

    def _stat(values: list[float]) -> dict[str, float]:
        if not values:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}
        return {
            "mean": round(sum(values) / len(values), 4),
            "std": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "median": round(statistics.median(values), 4),
        }

    # 排序
    sorted_by_composite = sorted(results, key=lambda r: r["composite_score"] or 0, reverse=True)

    output = {
        "meta": {
            "total_videos": len(results),
            "pipeline_version": "yolo11m_botsort_reid_gpt-5.4-mini",
            "llm_scoring_model": "gpt-4o",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "aggregate": {
            "composite": _stat(all_composite),
            "temporal_iou": _stat(all_temporal),
            "object_jaccard": _stat(all_object),
            "zone_jaccard": _stat(all_zone),
            "llm_text_similarity": _stat(all_llm),
            "top5": [r["video_id"] for r in sorted_by_composite[:5]],
            "bottom5": [r["video_id"] for r in sorted_by_composite[-5:]],
        },
        "videos": sorted_by_composite,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def generate_markdown_report(result_json: Path, output_md: Path) -> None:
    """生成 Markdown 可读报告"""
    data = json.loads(result_json.read_text(encoding="utf-8"))
    agg = data["aggregate"]
    videos = data["videos"]

    # 需要额外加载 pipeline/gt 数据来获取详细文本
    pipeline_dir = Path(DEFAULT_PIPELINE_DIR)
    _pipeline_cache: dict[str, dict[str, Any]] = {}

    def _load_video_data(video_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if video_id in _pipeline_cache:
            return _pipeline_cache[video_id]
        vf_path = pipeline_dir / "stage1" / f"{video_id}_events_vector_flat.json"
        gt_path = pipeline_dir / "ground_truth" / f"{video_id}_ground_truth.json"
        if vf_path.exists() and gt_path.exists():
            pl = json.loads(vf_path.read_text(encoding="utf-8"))
            gt = json.loads(gt_path.read_text(encoding="utf-8"))
            _pipeline_cache[video_id] = (pl, gt)
            return pl, gt
        return None

    lines = []
    lines.append("# Part4 管道评估报告")
    lines.append("")
    lines.append(f"**生成时间**: {data['meta']['generated_at']}")
    lines.append(f"**视频总数**: {data['meta']['total_videos']}")
    lines.append(f"**流水线**: {data['meta']['pipeline_version']}")
    lines.append("")

    lines.append("## 综合统计")
    lines.append("")
    lines.append("| 指标 | 均值 | 标准差 | 最低 | 最高 | 中位数 |")
    lines.append("|------|------|--------|------|------|--------|")
    for metric_name, label in [
        ("composite", "综合分"),
        ("temporal_iou", "时间 IoU"),
        ("object_jaccard", "对象匹配"),
        ("zone_jaccard", "场景匹配"),
        ("llm_text_similarity", "LLM 文字相似度"),
    ]:
        s = agg.get(metric_name, {})
        if s.get("mean", 0) > 0:
            lines.append(
                f"| {label} | {s['mean']:.4f} | {s['std']:.4f} | {s['min']:.4f} | {s['max']:.4f} | {s['median']:.4f} |"
            )

    lines.append("")
    lines.append("## Top 5")
    lines.append("")
    lines.append("| 排名 | 视频 | 综合分 | 时间IoU | 对象 | 场景 | LLM相似度 |")
    lines.append("|------|------|--------|--------|------|------|-----------|")
    for i, v in enumerate(videos[:5], 1):
        rs = v["rule_scores"]
        ls = v.get("llm_scores", {}) or {}
        llm_val = f'{ls.get("llm_score_mean", "-")}'
        lines.append(
            f"| {i} | {v['video_id']} | {v['composite_score']:.4f} | "
            f"{rs['temporal_iou']:.4f} | {rs['object_jaccard']:.4f} | "
            f"{rs['zone_jaccard']:.4f} | {llm_val} |"
        )

    lines.append("")
    lines.append("## Bottom 5")
    lines.append("")
    lines.append("| 排名 | 视频 | 综合分 | 时间IoU | 对象 | 场景 | LLM相似度 |")
    lines.append("|------|------|--------|--------|------|------|-----------|")
    for i, v in enumerate(videos[-5:], 1):
        rs = v["rule_scores"]
        ls = v.get("llm_scores", {}) or {}
        llm_val = f'{ls.get("llm_score_mean", "-")}'
        lines.append(
            f"| {i} | {v['video_id']} | {v['composite_score']:.4f} | "
            f"{rs['temporal_iou']:.4f} | {rs['object_jaccard']:.4f} | "
            f"{rs['zone_jaccard']:.4f} | {llm_val} |"
        )

    # ── LLM 文字差异详情 ──
    lines.append("")
    lines.append("## LLM 文字差异详情 (Top 3 & Bottom 3)")
    lines.append("")
    lines.append("> 每条 GT 与其时间最匹配的 Pred 事件对比，由 gpt-4o 评分（1-10）")
    lines.append("")

    highlight_videos = videos[:3] + videos[-3:]
    for v in highlight_videos:
        vid = v["video_id"]
        ls = v.get("llm_scores", {}) or {}
        per_gt = ls.get("llm_score_per_gt", [])
        if not per_gt:
            continue

        data_pair = _load_video_data(vid)
        if data_pair is None:
            continue
        pipeline_data, gt_data = data_pair
        pred_events = pipeline_data.get("events", [])
        gt_sentences = gt_data.get("sentences", [])
        gt_timestamps = gt_data.get("timestamps", [])

        dur = f'{v["duration_sec"]:.0f}s'
        lines.append(f"### {vid}（{dur}，综合分 {v['composite_score']:.4f}，LLM 均分 {ls.get('llm_score_mean', '-')}）")
        lines.append("")
        lines.append("| # | 时间 | GT 描述 | Pred 描述 | LLM | 原因 |")
        lines.append("|---|------|---------|-----------|-----|------|")

        for pg in per_gt[:8]:  # 最多 8 条
            gt_idx = pg["gt_idx"]
            pred_idx = pg["best_pred_idx"]
            score = pg["llm_score"]
            reason = pg["llm_reason"][:100] if pg["llm_reason"] else "-"

            gt_text = gt_sentences[gt_idx][:80] if gt_idx < len(gt_sentences) else "-"
            pred_text = (pred_events[pred_idx].get("event_text", "")[:80]
                         if pred_idx >= 0 and pred_idx < len(pred_events) else "-")

            ts = gt_timestamps[gt_idx] if gt_idx < len(gt_timestamps) else [0, 0]
            time_str = f"{float(ts[0]):.0f}-{float(ts[1]):.0f}s"

            emoji = "🟢" if score >= 6 else ("🟡" if score >= 4 else "🔴")
            lines.append(
                f"| {gt_idx+1} | {time_str} | {gt_text} | {pred_text} | {emoji} {score} | {reason} |"
            )

        lines.append("")

    lines.append("")
    lines.append("## 完整排名")
    lines.append("")
    lines.append("| # | 视频 | 时长 | 综合分 | 时间IoU | 对象 | 场景 | 覆盖 | 密度 | LLM |")
    lines.append("|---|------|------|--------|--------|------|------|------|------|-----|")
    for i, v in enumerate(videos, 1):
        rs = v["rule_scores"]
        ls = v.get("llm_scores", {}) or {}
        llm_val = f'{ls.get("llm_score_mean", "-")}'
        dur = f'{v["duration_sec"]:.0f}s'
        lines.append(
            f"| {i} | {v['video_id']} | {dur} | {v['composite_score']:.4f} | "
            f"{rs['temporal_iou']:.3f} | {rs['object_jaccard']:.3f} | "
            f"{rs['zone_jaccard']:.3f} | {rs['time_coverage']:.3f} | "
            f"{rs['density_ratio']:.3f} | {llm_val} |"
        )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown 报告已保存: {output_md}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Part4 全量打分（含 LLM 文字相似度）")
    p.add_argument("--pipeline-dir", type=str, default=str(DEFAULT_PIPELINE_DIR),
                   help="管道输出目录（含 stage2/ 和 ground_truth/）")
    p.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON),
                   help="输出 JSON 路径")
    p.add_argument("--output-md", type=str, default=str(DEFAULT_OUTPUT_MD),
                   help="输出 Markdown 路径")
    p.add_argument("--skip-llm", action="store_true",
                   help="跳过 LLM 文字相似度评分（仅计算规则指标）")
    p.add_argument("--llm-model", type=str, default="gpt-4o",
                   help="LLM 评分模型")
    p.add_argument("--resume", action="store_true",
                   help="断点续跑")
    return p


def main() -> None:
    args = build_parser().parse_args()
    pipeline_dir = Path(args.pipeline_dir).resolve()
    output_json = Path(args.output_json).resolve()
    output_md = Path(args.output_md).resolve()

    items = load_all_data(pipeline_dir)
    if not items:
        print("没有可评分的数据，退出。")
        sys.exit(1)

    t0 = time.time()
    result = score_all_videos(
        items, output_json,
        skip_llm=args.skip_llm,
        llm_model=args.llm_model,
        resume=args.resume,
    )
    elapsed = time.time() - t0
    print(f"\n总耗时: {elapsed:.1f}s")

    generate_markdown_report(output_json, output_md)


if __name__ == "__main__":
    main()
