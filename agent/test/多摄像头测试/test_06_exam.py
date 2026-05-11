"""test_06_exam.py — 做题式测试：完整 pipeline + 召回/精确/IoU 评估。

对每道 cross_camera 题：
  1. 分类检测 multi_camera 意图
  2. 运行 global_entity 两阶段检索
  3. 从 recall_challenge 中提取期望的摄像头集合
  4. 计算 Recall / Precision / IoU（摄像头级别）

输出: output/06_exam.json, output/06_exam.md
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "lib"))

from utils import (
    ROOT_DIR,
    OUTPUT_DIR,
    TestCase,
    TestSuite,
    TestReport,
    Timer,
    setup_env,
    write_json_report,
    write_md_summary,
)

# Add the agent/ directory to path for db.*, tools.* imports
sys.path.insert(0, str(ROOT_DIR / "agent"))

# ── question loading ──────────────────────────────────────────────────────────

def load_testable_questions() -> dict[str, list[dict[str, Any]]]:
    path = OUTPUT_DIR / "testable_questions.json"
    with open(path) as f:
        return json.load(f)


# ── camera extraction from recall_challenge ───────────────────────────────────

def extract_expected_cameras(recall_text: str) -> set[str]:
    """Extract expected cameras from recall_challenge text.

    Examples:
      'Same person (13-50-P1) first in G329 @ 1:50, then G328 @ 2:02'
        → {'G329', 'G328'}
      'Same person (13-50-P4) first in G329 @ 3:08, then G339 @ 3:36'
        → {'G329', 'G339'}
    """
    cameras: set[str] = set()
    # Match "G\d+" patterns (camera IDs)
    matches = re.findall(r'G\d+', recall_text)
    cameras.update(matches)
    return cameras


# ── GE branch retrieval ───────────────────────────────────────────────────────

def run_ge_branch(query: str) -> tuple[list[dict[str, Any]], str]:
    """Run the global_entity two-stage retrieval."""
    from db.config import get_graph_chroma_global_entity_collection, get_graph_chroma_path
    from tools.db_access import ChromaGateway

    if not query.strip():
        return [], "empty query"

    # Stage 1: Chroma
    try:
        gateway = ChromaGateway(
            db_path=get_graph_chroma_path(),
            collection_name=get_graph_chroma_global_entity_collection(),
        )
        ge_results = gateway.search(query=query, metadata_filters=[], limit=5)
    except Exception as exc:
        return [], f"Chroma error: {exc}"

    if not ge_results:
        return [], "no Chroma matches"

    ge_ids = list(dict.fromkeys(
        str(r.get("event_id") or r.get("id"))
        for r in ge_results
        if r.get("event_id") or r.get("id")
    ))

    if not ge_ids:
        return [], "no valid entity IDs"

    # Stage 2: SQLite
    db_path = str(ROOT_DIR / "agent" / "test_mulcamera" / "episodic_events.sqlite")
    placeholders = ",".join(["?" for _ in ge_ids])

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        sql = (
            "SELECT event_id, video_id, camera_id, track_id, "
            "start_time, end_time, object_type, object_color_en, "
            "scene_zone_en, event_summary_en, global_entity_id "
            "FROM episodic_events "
            f"WHERE global_entity_id IN ({placeholders}) "
            f"ORDER BY global_entity_id, start_time ASC "
            f"LIMIT 200"
        )
        rows = [dict(r) for r in conn.execute(sql, ge_ids).fetchall()]

    for row in rows:
        row["_source_type"] = "global_entity"
        row["_ge_vector_score"] = float(
            next((r.get("_vector_score", 0.0) for r in ge_results if str(r.get("event_id") or r.get("id")) == row.get("global_entity_id")), 0.0)
        )

    n_entities = len(set(r.get("global_entity_id") for r in rows if r.get("global_entity_id")))
    return rows, f"matched={len(ge_ids)} entities={n_entities} rows={len(rows)}"


# ── metrics ───────────────────────────────────────────────────────────────────

def compute_camera_metrics(
    expected: set[str],
    found: set[str],
) -> dict[str, float]:
    """Compute recall, precision, IoU between expected and found camera sets."""
    inter = expected & found
    union = expected | found

    recall = len(inter) / len(expected) if expected else 0.0
    precision = len(inter) / len(found) if found else 0.0
    iou = len(inter) / len(union) if union else 0.0

    return {
        "expected_cameras": sorted(expected),
        "found_cameras": sorted(found),
        "intersection": sorted(inter),
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "iou": round(iou, 4),
    }


# ── relaxed IoU ───────────────────────────────────────────────────────────────
# For multi-camera, finding camA + camB is the key. But we also accept partial
# matches (e.g., found camA but not camB = recall 0.5). We set relaxed thresholds:
#   recall >= 0.5 (at least one of the two expected cameras found)
#   precision >= 0.1 (even if many irrelevant cameras, as long as some match)
#   iou >= 0.1 (very relaxed overlap)

RELAXED_RECALL_THRESHOLD = 0.5
RELAXED_PRECISION_THRESHOLD = 0.1
RELAXED_IOU_THRESHOLD = 0.1


def main() -> None:
    setup_env()

    # Load classifier
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "qc", str(ROOT_DIR / "agent" / "agents" / "shared" / "query_classifier.py"),
    )
    qc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qc)

    questions = load_testable_questions()
    report = TestReport(
        title="做题式测试 — 召回/精确/IoU 评估",
        started_at=datetime.now().isoformat(),
    )

    # ── Suite 1: cross_camera 摄像头匹配 ──
    suite_cc = TestSuite(name="cross_camera 摄像头召回/精确/IoU")

    with Timer() as t_cc:
        for item in questions.get("cross_camera", []):
            query = item["question"]
            recall_text = item.get("recall_challenge", "")
            expected_cameras = extract_expected_cameras(recall_text)

            # Classification
            signals = qc._collect_signals(query)
            mc_detected = qc._detect_multi_camera(signals)

            # Retrieval
            rows, summary = run_ge_branch(query)
            found_cameras = set(r.get("camera_id") for r in rows if r.get("camera_id"))

            # Metrics
            metrics = compute_camera_metrics(expected_cameras, found_cameras)

            # Relaxed pass:
            passed = (
                mc_detected
                and metrics["recall"] >= RELAXED_RECALL_THRESHOLD
                and metrics["iou"] >= RELAXED_IOU_THRESHOLD
            )

            suite_cc.cases.append(TestCase(
                name=f"[{'PASS' if passed else 'FAIL'}] {query[:70]}",
                passed=passed,
                details=f"mc={mc_detected} recall={metrics['recall']:.2f} prec={metrics['precision']:.2f} IoU={metrics['iou']:.2f} | expected={metrics['expected_cameras']} found={metrics['found_cameras']}",
                metrics=metrics,
            ))

    report.suites.append(suite_cc)

    # ── Suite 2: negative 意图检测 ──
    suite_neg = TestSuite(name="negative 多摄意图检测")

    with Timer() as t_neg:
        for item in questions.get("negative", []):
            query = item["question"]
            signals = qc._collect_signals(query)
            mc_detected = qc._detect_multi_camera(signals)
            suite_neg.cases.append(TestCase(
                name=query[:80],
                passed=mc_detected,
                details=f"multi_camera={mc_detected} (expected=True)",
            ))

    report.suites.append(suite_neg)

    # ── Summary stats ──
    stats_cc = TestSuite(name="cross_camera 汇总统计")
    cc_all = suite_cc.cases
    if cc_all:
        avg_recall = sum(c.metrics.get("recall", 0) for c in cc_all) / len(cc_all)
        avg_precision = sum(c.metrics.get("precision", 0) for c in cc_all) / len(cc_all)
        avg_iou = sum(c.metrics.get("iou", 0) for c in cc_all) / len(cc_all)
        n_passed = sum(1 for c in cc_all if c.passed)
        stats_cc.cases.append(TestCase(
            name=f"总体: {n_passed}/{len(cc_all)} 通过 ({n_passed/len(cc_all)*100:.1f}%)",
            passed=n_passed / len(cc_all) >= 0.7,
            metrics={"avg_recall": round(avg_recall, 4), "avg_precision": round(avg_precision, 4), "avg_iou": round(avg_iou, 4), "passed": n_passed, "total": len(cc_all)},
        ))
    report.suites.append(stats_cc)

    report.elapsed_sec = (t_cc.elapsed_ms + t_neg.elapsed_ms) / 1000

    json_path = write_json_report(report, "06_exam")
    md_path = write_md_summary(report, "06_exam")
    print(f"Exam report → {json_path}")
    print(f"Exam summary → {md_path}")
    for s in report.suites:
        for c in s.cases:
            icon = "✅" if c.passed else "❌"
            print(f"  {icon} {c.name}  — {c.details[:100]}")


if __name__ == "__main__":
    main()
