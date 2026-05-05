#!/usr/bin/env python3
"""
UCA Part4 全量打分：Stage 2 UCA 输出 vs UCFCrime_Test.json 地面真值。

评分维度：
  1. Temporal IoU (每条 GT 最佳匹配 Pred)
  2. Temporal Recall (GT 时间段被 Pred 覆盖的比例)
  3. LLM 语义相似度 (gpt-4o 1-10 评分)
  4. Density Ratio (事件数匹配度)
  5. Time Coverage (视频时间覆盖率)

输出：
  - part4_uca_score.json   结构化打分数据
  - part4_uca_score.md     可读报告

用法：
  python scripts/score_uca_part4.py
  python scripts/score_uca_part4.py --skip-llm          # 跳过 LLM 评分
  python scripts/score_uca_part4.py --resume             # 断点续跑
  python scripts/score_uca_part4.py --llm-model gpt-5.4  # 指定 LLM 评分模型
"""

import argparse
import json
import math
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_UCA_DIR = ROOT_DIR / "data" / "part4_pipeline_output"
DEFAULT_GT_PATH = ROOT_DIR / "agent" / "test" / "data" / "UCFCrime_Test.json"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "data" / "part4_pipeline_output" / "part4_uca_score.json"
DEFAULT_OUTPUT_MD = ROOT_DIR / "data" / "part4_pipeline_output" / "part4_uca_score.md"


# ══════════════════════════════════════════════════════════════
# 规则指标
# ══════════════════════════════════════════════════════════════

def temporal_iou(a_s: float, a_e: float, b_s: float, b_e: float) -> float:
    inter = max(0.0, min(a_e, b_e) - max(a_s, b_s))
    union = max(a_e, b_e) - min(a_s, b_s)
    return inter / union if union > 0 else 0.0


def temporal_recall(pred_s: float, pred_e: float, gt_s: float, gt_e: float) -> float:
    inter = max(0.0, min(pred_e, gt_e) - max(pred_s, gt_s))
    return inter / (gt_e - gt_s) if (gt_e - gt_s) > 0 else 0.0


def compute_rule_scores(pred_ts: list, pred_sent: list,
                        gt_ts: list, gt_sent: list,
                        duration: float) -> dict[str, Any]:
    """计算规则指标"""
    n_pred = len(pred_ts)
    n_gt = len(gt_ts)

    # ── Temporal IoU + Recall (GT → best Pred) ──
    per_gt = []
    ious = []
    recalls = []
    for gi, (gs, ge) in enumerate(gt_ts):
        best_iou, best_pi = 0.0, -1
        for pi, (ps, pe) in enumerate(pred_ts):
            iou = temporal_iou(ps, pe, gs, ge)
            if iou > best_iou:
                best_iou, best_pi = iou, pi
        ious.append(best_iou)
        rec = temporal_recall(pred_ts[best_pi][0], pred_ts[best_pi][1], gs, ge) if best_pi >= 0 else 0.0
        recalls.append(rec)
        per_gt.append({
            "gt_idx": gi,
            "gt_range": f"{gs:.1f}-{ge:.1f}s",
            "gt_sentence": gt_sent[gi],
            "best_pred_idx": best_pi,
            "pred_range": f"{pred_ts[best_pi][0]:.1f}-{pred_ts[best_pi][1]:.1f}s" if best_pi >= 0 else "N/A",
            "pred_sentence": pred_sent[best_pi] if best_pi >= 0 else "",
            "iou": round(best_iou, 4),
            "recall": round(rec, 4),
        })

    mean_iou = round(sum(ious) / len(ious), 4) if ious else 0.0
    mean_recall = round(sum(recalls) / len(recalls), 4) if recalls else 0.0

    # ── Density Ratio ──
    density = round(min(n_pred, n_gt) / max(n_pred, n_gt), 4) if n_pred > 0 and n_gt > 0 else 0.0

    # ── Time Coverage ──
    pred_covered = sum(pe - ps for ps, pe in pred_ts)
    gt_covered = sum(ge - gs for gs, ge in gt_ts)
    coverage = round(pred_covered / duration, 4) if duration > 0 else 0.0

    return {
        "temporal_iou_mean": mean_iou,
        "temporal_recall_mean": mean_recall,
        "density_ratio": density,
        "time_coverage": coverage,
        "pred_event_count": n_pred,
        "gt_event_count": n_gt,
        "pred_covered_sec": round(pred_covered, 1),
        "gt_covered_sec": round(gt_covered, 1),
        "per_gt": per_gt,
    }


# ══════════════════════════════════════════════════════════════
# LLM 语义相似度评分
# ══════════════════════════════════════════════════════════════

LLM_SCORE_PROMPT = """Rate the semantic similarity between two surveillance video event descriptions on a scale of 1-10:
- 1-2: Completely different subjects, actions, or locations
- 3-4: Same general domain but different specifics
- 5-6: Partial overlap — some shared elements but missing key details
- 7-8: Good match — captures the main action/subject, minor differences
- 9-10: Excellent match — nearly identical in subject, action, and key details

Output ONLY a JSON: {{"score": <int 1-10>, "reason": "<one sentence>"}}

Pred: {pred}
GT: {gt}"""


def score_text_similarity(pred_text: str, gt_text: str,
                          model: str = "gpt-4o") -> dict[str, Any]:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")

    client = OpenAI()
    prompt = LLM_SCORE_PROMPT.format(pred=pred_text, gt=gt_text)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=150,
        )
        content = resp.choices[0].message.content or "{}"
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            result = json.loads(content[start:end + 1])
            return {"score": int(result.get("score", 0)), "reason": str(result.get("reason", ""))}
        return {"score": 0, "reason": f"parse_error: {content[:80]}"}
    except Exception as e:
        return {"score": 0, "reason": f"api_error: {str(e)[:80]}"}


def score_video_with_llm(pred_ts: list, pred_sent: list,
                         gt_ts: list, gt_sent: list,
                         model: str = "gpt-4o") -> dict[str, Any]:
    """对单个视频的所有 GT vs 最佳时间匹配 Pred 做 LLM 打分"""
    per_gt_scores = []
    all_scores = []

    for gi, (gs, ge) in enumerate(gt_ts):
        best_iou, best_pi = 0.0, -1
        for pi, (ps, pe) in enumerate(pred_ts):
            iou = temporal_iou(ps, pe, gs, ge)
            if iou > best_iou:
                best_iou, best_pi = iou, pi

        if best_pi >= 0:
            result = score_text_similarity(pred_sent[best_pi], gt_sent[gi], model=model)
        else:
            result = {"score": 0, "reason": "no matching pred event"}

        all_scores.append(result["score"])
        per_gt_scores.append({
            "gt_idx": gi,
            "best_pred_idx": best_pi,
            "temporal_iou": round(best_iou, 4),
            "llm_score": result["score"],
            "llm_reason": result["reason"],
            "gt_sentence": gt_sent[gi][:120],
            "pred_sentence": pred_sent[best_pi][:120] if best_pi >= 0 else "",
        })

    mean_llm = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    return {
        "llm_score_mean": mean_llm,
        "llm_score_per_gt": per_gt_scores,
        "llm_model": model,
    }


# ══════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════

def discover_uca_files(uca_dir: Path, gt_data: dict[str, Any]) -> list[dict[str, Any]]:
    """发现所有 UCA 输出并匹配 GT"""
    uca_files = sorted(uca_dir.glob("*_events_uca.json"))
    if not uca_files:
        raise FileNotFoundError(f"未找到 *_events_uca.json 文件于 {uca_dir}")

    items = []
    for uf in uca_files:
        video_id = uf.stem.replace("_events_uca", "")
        if video_id not in gt_data:
            print(f"  ⚠ {video_id}: 在 GT 中未找到，跳过")
            continue
        items.append({
            "video_id": video_id,
            "uca_path": uf,
            "gt": gt_data[video_id],
        })

    print(f"找到 {len(items)} 个 UCA-GT 配对")
    return items


def score_all(items: list[dict[str, Any]], output_json: Path, *,
              skip_llm: bool = False, llm_model: str = "gpt-4o",
              resume: bool = False) -> dict[str, Any]:
    """对所有视频打分"""
    existing: dict[str, dict[str, Any]] = {}
    if resume and output_json.exists():
        old = json.loads(output_json.read_text(encoding="utf-8"))
        for v in old.get("videos", []):
            existing[v["video_id"]] = v
        print(f"断点续跑：已有 {len(existing)} 个结果")

    results: list[dict[str, Any]] = []
    total = len(items)

    for idx, item in enumerate(items, 1):
        vid = item["video_id"]
        print(f"\n[{idx}/{total}] {vid}", end="", flush=True)

        if vid in existing and existing[vid].get("llm_score_mean") is not None:
            results.append(existing[vid])
            print(" → 跳过（已有结果）")
            continue
        if vid in existing and skip_llm and existing[vid].get("rule_scores") is not None:
            results.append(existing[vid])
            print(" → 跳过（已有规则指标）")
            continue

        uca = json.loads(item["uca_path"].read_text(encoding="utf-8"))
        gt = item["gt"]
        duration = gt.get("duration", 0) or 0

        pred_ts = uca.get("timestamps", [])
        pred_sent = uca.get("sentences", [])
        gt_ts = gt.get("timestamps", [])
        gt_sent = gt.get("sentences", [])

        # 规则指标
        rule = compute_rule_scores(pred_ts, pred_sent, gt_ts, gt_sent, duration)
        print(f" | IoU={rule['temporal_iou_mean']:.3f} Recall={rule['temporal_recall_mean']:.3f} Density={rule['density_ratio']:.3f}", end="", flush=True)

        # LLM 评分
        llm_result = None
        if not skip_llm:
            try:
                llm_result = score_video_with_llm(pred_ts, pred_sent, gt_ts, gt_sent, model=llm_model)
                print(f" | LLM={llm_result['llm_score_mean']}", end="", flush=True)
            except Exception as e:
                print(f" | LLM error: {e}", end="", flush=True)
                llm_result = {"llm_score_mean": None, "llm_score_per_gt": [], "llm_model": llm_model}

        # 综合分
        llm_norm = llm_result["llm_score_mean"] / 10.0 if llm_result and llm_result["llm_score_mean"] is not None else 0.0
        composite = round(
            0.30 * rule["temporal_iou_mean"]
            + 0.15 * rule["temporal_recall_mean"]
            + 0.15 * rule["density_ratio"]
            + 0.10 * rule["time_coverage"]
            + 0.30 * llm_norm,
            4,
        )

        result = {
            "video_id": vid,
            "duration_sec": duration,
            "pred_event_count": rule["pred_event_count"],
            "gt_event_count": rule["gt_event_count"],
            "rule_scores": {k: v for k, v in rule.items() if k != "per_gt"},
            "llm_scores": llm_result,
            "composite_score": composite,
        }
        results.append(result)

        # 每 5 个保存
        if idx % 5 == 0 or idx == total:
            _save_results(output_json, results)

    print(f"\n完成 {len(results)} 个视频打分")
    return _save_results(output_json, results)


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


def _save_results(output_json: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    all_composite = [r["composite_score"] for r in results if r["composite_score"] is not None]
    all_iou = [r["rule_scores"]["temporal_iou_mean"] for r in results]
    all_recall = [r["rule_scores"]["temporal_recall_mean"] for r in results]
    all_density = [r["rule_scores"]["density_ratio"] for r in results]
    all_coverage = [r["rule_scores"]["time_coverage"] for r in results]
    all_llm = [
        r["llm_scores"]["llm_score_mean"] / 10.0
        for r in results
        if r.get("llm_scores") and r["llm_scores"].get("llm_score_mean") is not None
    ]

    sorted_by_composite = sorted(results, key=lambda r: r["composite_score"] or 0, reverse=True)

    output = {
        "meta": {
            "total_videos": len(results),
            "pipeline": "yolo11m_botsort_reid → gpt-5.4 UCA mode",
            "llm_scoring_model": "gpt-4o",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "scoring_weights": "IoU=0.30 Recall=0.15 Density=0.15 Coverage=0.10 LLM=0.30",
        },
        "aggregate": {
            "composite": _stat(all_composite),
            "temporal_iou": _stat(all_iou),
            "temporal_recall": _stat(all_recall),
            "density_ratio": _stat(all_density),
            "time_coverage": _stat(all_coverage),
            "llm_similarity": _stat(all_llm),
            "top5": [r["video_id"] for r in sorted_by_composite[:5]],
            "bottom5": [r["video_id"] for r in sorted_by_composite[-5:]],
        },
        "videos": sorted_by_composite,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def generate_markdown(result_json: Path, output_md: Path) -> None:
    """生成 Markdown 报告"""
    data = json.loads(result_json.read_text(encoding="utf-8"))
    agg = data["aggregate"]
    videos = data["videos"]
    meta = data["meta"]

    lines = []
    lines.append("# Part4 UCA Pipeline 评估报告")
    lines.append("")
    lines.append(f"**生成时间**: {meta['generated_at']}")
    lines.append(f"**视频总数**: {meta['total_videos']}")
    lines.append(f"**Pipeline**: {meta['pipeline']}")
    lines.append(f"**LLM 评分模型**: {meta['llm_scoring_model']}")
    lines.append(f"**评分权重**: {meta['scoring_weights']}")
    lines.append("")

    # ── 综合统计 ──
    lines.append("## 综合统计")
    lines.append("")
    lines.append("| 指标 | 均值 | 标准差 | 最低 | 最高 | 中位数 |")
    lines.append("|------|------|--------|------|------|--------|")
    for key, label in [
        ("composite", "综合分"),
        ("temporal_iou", "时间 IoU"),
        ("temporal_recall", "时间 Recall"),
        ("density_ratio", "密度比"),
        ("time_coverage", "时间覆盖"),
        ("llm_similarity", "LLM 相似度"),
    ]:
        s = agg.get(key, {})
        if s.get("mean", 0) > 0 or key == "composite":
            lines.append(
                f"| {label} | {s.get('mean', 0):.4f} | {s.get('std', 0):.4f} | "
                f"{s.get('min', 0):.4f} | {s.get('max', 0):.4f} | {s.get('median', 0):.4f} |"
            )

    # ── Top 5 / Bottom 5 ──
    for section, vids, indices in [("Top 5", videos[:5], range(5)), ("Bottom 5", videos[-5:], range(5))]:
        lines.append("")
        lines.append(f"## {section}")
        lines.append("")
        lines.append("| # | 视频 | 时长 | 综合分 | IoU | Recall | 密度 | 覆盖 | LLM |")
        lines.append("|---|------|------|--------|-----|--------|------|------|-----|")
        for i, v in enumerate(vids, 1):
            rs = v["rule_scores"]
            ls = v.get("llm_scores", {}) or {}
            llm_val = f'{ls.get("llm_score_mean", "-")}'
            dur = f'{v["duration_sec"]:.0f}s'
            lines.append(
                f"| {i} | {v['video_id']} | {dur} | {v['composite_score']:.4f} | "
                f"{rs['temporal_iou_mean']:.3f} | {rs['temporal_recall_mean']:.3f} | "
                f"{rs['density_ratio']:.3f} | {rs['time_coverage']:.3f} | {llm_val} |"
            )

    # ── LLM 差异详情 (Top 3 & Bottom 3) ──
    lines.append("")
    lines.append("## LLM 语义差异详情 (Top 3 & Bottom 3)")
    lines.append("")
    lines.append("> 每条 GT 与其时间最匹配的 Pred 对比，由 gpt-4o 评分（1-10）")
    lines.append("")

    # Reload UCA + GT data for detailed view
    uca_dir = DEFAULT_UCA_DIR
    gt_data = json.loads(DEFAULT_GT_PATH.read_text(encoding="utf-8"))

    for v in videos[:3] + videos[-3:]:
        vid = v["video_id"]
        ls = v.get("llm_scores", {}) or {}
        per_gt = ls.get("llm_score_per_gt", [])
        if not per_gt:
            continue

        uca_path = uca_dir / f"{vid}_events_uca.json"
        if not uca_path.exists():
            continue
        uca = json.loads(uca_path.read_text(encoding="utf-8"))
        gt = gt_data.get(vid, {})
        pred_sent = uca.get("sentences", [])
        gt_sent = gt.get("sentences", [])
        gt_ts = gt.get("timestamps", [])

        lines.append(f"### {vid}（{v['duration_sec']:.0f}s，综合分 {v['composite_score']:.4f}，LLM {ls.get('llm_score_mean', '-')}）")
        lines.append("")
        lines.append("| # | 时间 | GT | Pred | LLM | 原因 |")
        lines.append("|---|------|----|------|-----|------|")

        for pg in per_gt[:8]:
            gi = pg["gt_idx"]
            pi = pg["best_pred_idx"]
            score = pg["llm_score"]
            reason = pg["llm_reason"][:100] if pg["llm_reason"] else "-"
            gt_text = gt_sent[gi][:80] if gi < len(gt_sent) else "-"
            pred_text = pred_sent[pi][:80] if pi >= 0 and pi < len(pred_sent) else "-"
            ts = gt_ts[gi] if gi < len(gt_ts) else [0, 0]
            time_str = f"{float(ts[0]):.0f}-{float(ts[1]):.0f}s"

            mark = "🟢" if score >= 6 else ("🟡" if score >= 4 else "🔴")
            lines.append(
                f"| {gi+1} | {time_str} | {gt_text} | {pred_text} | {mark} {score} | {reason} |"
            )
        lines.append("")

    # ── 完整排名 ──
    lines.append("")
    lines.append("## 完整排名")
    lines.append("")
    lines.append("| # | 视频 | 时长 | 综合分 | IoU | Recall | 密度 | 覆盖 | LLM |")
    lines.append("|---|------|------|--------|-----|--------|------|------|-----|")
    for i, v in enumerate(videos, 1):
        rs = v["rule_scores"]
        ls = v.get("llm_scores", {}) or {}
        llm_val = f'{ls.get("llm_score_mean", "-")}'
        dur = f'{v["duration_sec"]:.0f}s'
        lines.append(
            f"| {i} | {v['video_id']} | {dur} | {v['composite_score']:.4f} | "
            f"{rs['temporal_iou_mean']:.3f} | {rs['temporal_recall_mean']:.3f} | "
            f"{rs['density_ratio']:.3f} | {rs['time_coverage']:.3f} | {llm_val} |"
        )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown 报告已保存: {output_md}")


def main() -> None:
    args = build_parser().parse_args()
    uca_dir = Path(args.uca_dir).resolve()
    gt_path = Path(args.gt_path).resolve()
    output_json = Path(args.output_json).resolve()
    output_md = Path(args.output_md).resolve()

    gt_data = json.loads(gt_path.read_text(encoding="utf-8"))
    print(f"GT 共 {len(gt_data)} 个视频条目")

    items = discover_uca_files(uca_dir, gt_data)
    if not items:
        print("没有可评分的数据，退出。")
        sys.exit(1)

    t0 = time.time()
    result = score_all(
        items, output_json,
        skip_llm=args.skip_llm,
        llm_model=args.llm_model,
        resume=args.resume,
    )
    elapsed = time.time() - t0
    print(f"\n总耗时: {elapsed:.1f}s")

    generate_markdown(output_json, output_md)

    # 打印汇总
    agg = result["aggregate"]
    print("\n" + "=" * 72)
    print("  评估汇总")
    print("=" * 72)
    for key, label in [
        ("composite", "综合分"),
        ("temporal_iou", "时间 IoU"),
        ("temporal_recall", "时间 Recall"),
        ("density_ratio", "密度比"),
        ("time_coverage", "时间覆盖"),
        ("llm_similarity", "LLM 相似度"),
    ]:
        s = agg.get(key, {})
        print(f"  {label:12s}: {s.get('mean', 0):.4f} (std={s.get('std', 0):.4f})")
    print(f"\n  JSON: {output_json}")
    print(f"  MD:   {output_md}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Part4 UCA 全量打分")
    p.add_argument("--uca-dir", type=str, default=str(DEFAULT_UCA_DIR),
                   help="UCA 输出目录")
    p.add_argument("--gt-path", type=str, default=str(DEFAULT_GT_PATH),
                   help="UCFCrime_Test.json 路径")
    p.add_argument("--output-json", type=str, default=str(DEFAULT_OUTPUT_JSON),
                   help="输出 JSON 路径")
    p.add_argument("--output-md", type=str, default=str(DEFAULT_OUTPUT_MD),
                   help="输出 Markdown 路径")
    p.add_argument("--skip-llm", action="store_true",
                   help="跳过 LLM 语义评分")
    p.add_argument("--llm-model", type=str, default="gpt-4o",
                   help="LLM 评分模型 (default: gpt-4o)")
    p.add_argument("--resume", action="store_true",
                   help="断点续跑")
    return p


if __name__ == "__main__":
    main()
