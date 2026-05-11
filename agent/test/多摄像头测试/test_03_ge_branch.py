"""test_03_ge_branch.py — global_entity 分支独立测试。

直接实现两阶段检索，不依赖 parallel_retrieval_fusion_node 的 import 链。
Stage1: Chroma semantic search in global_entity collection
Stage2: SQLite expansion via global_entity_id IN (...)

输出: output/03_ge_branch.json, output/03_ge_branch.md
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "agent"))

from utils import (
    ROOT_DIR,
    TestCase,
    TestSuite,
    TestReport,
    Timer,
    setup_env,
    write_json_report,
    write_md_summary,
)


def run_global_entity_branch(
    user_query: str,
    search_config: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    """Two-stage cross-camera global entity retrieval.

    Stage 1: Chroma semantic search in global_entity collection.
    Stage 2: SQLite expansion via global_entity_id IN (...).
    """
    from db.config import get_graph_chroma_global_entity_collection, get_graph_chroma_path
    from tools.db_access import ChromaGateway

    ge_top_k = int(search_config.get("global_entity_top_k", 5))
    ge_sql_limit = int(search_config.get("global_entity_sql_limit", 200))

    if not (user_query or "").strip():
        return "GE skipped: empty query", []

    # Stage 1: Chroma
    try:
        gateway = ChromaGateway(
            db_path=get_graph_chroma_path(),
            collection_name=get_graph_chroma_global_entity_collection(),
        )
        ge_results = gateway.search(
            query=user_query,
            metadata_filters=[],
            limit=ge_top_k,
        )
    except Exception as exc:
        return f"GE Chroma failed: {exc}", []

    if not ge_results:
        return "GE Chroma: no matches", []

    ge_ids: list[str] = []
    ge_scores: dict[str, float] = {}
    for row in ge_results:
        ge_id = row.get("event_id") or row.get("id")
        if ge_id:
            ge_ids.append(str(ge_id))
            ge_scores[str(ge_id)] = float(row.get("_vector_score", 0.0))

    if not ge_ids:
        return "GE Chroma: no valid entity IDs", []

    ge_ids = list(dict.fromkeys(ge_ids))

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
            f"LIMIT {ge_sql_limit}"
        )
        rows = [dict(r) for r in conn.execute(sql, ge_ids).fetchall()]

    for row in rows:
        row["_source_type"] = "global_entity"
        row["_ge_vector_score"] = ge_scores.get(str(row.get("global_entity_id", "")), 0.0)

    n_entities = len(set(r.get("global_entity_id") for r in rows if r.get("global_entity_id")))
    return f"GE matched={len(ge_ids)} entities={n_entities} rows={len(rows)}", rows


# Cross-camera questions from 13-50-13-55 data range (our imported data)
# question → expected cameras to find
TEST_CASES_1350 = [
    (
        "Did a person with light grey hoodie appear in camera G424 and then appear again in camera G339?",
        ["G424", "G339"],
        "light grey hoodie → person_global_4 (5 cameras)",
    ),
    (
        "Did a person with black coat with fur-trimmed hood appear in camera G329 and then appear again in camera G339?",
        ["G329", "G339"],
        "black coat fur hood → match dark entity across G329+G339",
    ),
    (
        "Did a person with white shirt appear in camera G328 and then appear again in camera G424?",
        ["G328", "G424"],
        "white shirt → person_global_2 (3 cameras)",
    ),
    (
        "Did a person with dark jacket hood up appear in camera G329 and then appear again in camera G328?",
        ["G329", "G328"],
        "dark jacket hood up → match dark entity",
    ),
    (
        "Did a person with brown jacket with dark hood appear in camera G424 and then appear again in camera G339?",
        ["G424", "G339"],
        "brown jacket → match dark entity across G424+G339",
    ),
]


def main() -> None:
    setup_env()

    report = TestReport(
        title="global_entity 分支独立测试",
        started_at=datetime.now().isoformat(),
    )

    suite = TestSuite(name="GE 分支两阶段检索")

    search_config = {"global_entity_top_k": 5, "global_entity_sql_limit": 200}

    with Timer() as t:
        for query, expected_cameras, note in TEST_CASES_1350:
            summary, rows = run_global_entity_branch(query, search_config)
            # Extract cameras from results
            found_cameras = list(dict.fromkeys(
                r.get("camera_id") for r in rows if r.get("camera_id")
            ))
            found_entities = list(dict.fromkeys(
                r.get("global_entity_id") for r in rows if r.get("global_entity_id")
            ))
            all_expected = all(cam in found_cameras for cam in expected_cameras)

            suite.cases.append(TestCase(
                name=query[:80],
                passed=len(rows) > 0 and all_expected,
                details=f"rows={len(rows)} entities={found_entities} cameras={found_cameras}",
                metrics={
                    "row_count": len(rows),
                    "entity_count": len(found_entities),
                    "camera_count": len(found_cameras),
                    "expected_cameras": expected_cameras,
                    "found_cameras": found_cameras,
                },
            ))

    report.suites.append(suite)
    report.elapsed_sec = t.elapsed_ms / 1000

    json_path = write_json_report(report, "03_ge_branch")
    md_path = write_md_summary(report, "03_ge_branch")
    print(f"GE branch report → {json_path}")
    print(f"GE branch summary → {md_path}")
    for c in suite.cases:
        print(f"  {'✅' if c.passed else '❌'} {c.name}")


if __name__ == "__main__":
    main()
