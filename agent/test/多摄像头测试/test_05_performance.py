"""test_05_performance.py — 性能基准测试。

测试分类层、Chroma 搜索、SQLite 展开、融合层的耗时。
输出: output/05_performance.json, output/05_performance.md
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "lib"))

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


def _load_classifier():
    spec = importlib.util.spec_from_file_location(
        "query_classifier",
        str(ROOT_DIR / "agent" / "agents" / "shared" / "query_classifier.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    setup_env()

    report = TestReport(
        title="性能基准测试",
        started_at=datetime.now().isoformat(),
    )

    suite = TestSuite(name="性能指标")

    qc = _load_classifier()
    query = "Did a person with light grey hoodie appear in camera G424 and then appear again in camera G339?"

    # 1) fast-path 分类
    with Timer() as t:
        for _ in range(100):
            qc._detect_multi_camera(qc._collect_signals(query))
    suite.cases.append(TestCase(
        name="分类 fast-path 延迟",
        passed=t.elapsed_ms / 100 < 1.0,
        details=f"{t.elapsed_ms / 100:.2f} ms/query (100 runs)",
        metrics={"latency_ms": round(t.elapsed_ms / 100, 2), "target_ms": 1.0},
    ))

    # 2) Chroma search
    from tools.db_access import ChromaGateway
    gateway = ChromaGateway(
        db_path=str(ROOT_DIR / "agent" / "test_mulcamera" / "chroma"),
        collection_name="mul_camera_global_entities",
    )
    with Timer() as t:
        for _ in range(10):
            gateway.search(query=query, metadata_filters=[], limit=5)
    suite.cases.append(TestCase(
        name="Stage1 Chroma global_entity 搜索",
        passed=t.elapsed_ms / 10 < 500,
        details=f"{t.elapsed_ms / 10:.0f} ms/query (10 runs)",
        metrics={"latency_ms": round(t.elapsed_ms / 10, 0), "target_ms": 500},
    ))

    # 3) SQLite expansion
    db_path = str(ROOT_DIR / "agent" / "test_mulcamera" / "episodic_events.sqlite")
    with Timer() as t:
        for _ in range(10):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute(
                    "SELECT * FROM episodic_events WHERE global_entity_id IN (?,?) "
                    "ORDER BY start_time ASC LIMIT 200",
                    ("person_global_4", "person_global_6"),
                ).fetchall()
    suite.cases.append(TestCase(
        name="Stage2 SQLite 展开",
        passed=t.elapsed_ms / 10 < 200,
        details=f"{t.elapsed_ms / 10:.0f} ms/query (10 runs)",
        metrics={"latency_ms": round(t.elapsed_ms / 10, 0), "target_ms": 200},
    ))

    # 4) RRF fusion
    spec = importlib.util.spec_from_file_location(
        "fusion_engine",
        str(ROOT_DIR / "agent" / "agents" / "shared" / "fusion_engine.py"),
    )
    fe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fe)

    sql_rows = [{"event_id": i, "video_id": "v", "start_time": float(i)} for i in range(80)]
    hyb_rows = [{"event_id": 1000 + i, "video_id": "v", "start_time": float(i)} for i in range(50)]
    ge_rows = [
        {"global_entity_id": f"ge{i}", "event_id": 2000 + i, "camera_id": f"G{300+i}", "start_time": float(i), "video_id": "v", "event_summary_en": "ge"}
        for i in range(10)
    ]
    with Timer() as t:
        for _ in range(100):
            fe.weighted_rrf_fuse(sql_rows, hyb_rows, label="mixed", limit=50, global_entity_rows=ge_rows)
    suite.cases.append(TestCase(
        name="三路 RRF 融合",
        passed=t.elapsed_ms / 100 < 10,
        details=f"{t.elapsed_ms / 100:.3f} ms/run (100 runs, 80 sql + 50 hyb + 10 ge)",
        metrics={"latency_ms": round(t.elapsed_ms / 100, 3), "target_ms": 10},
    ))

    report.suites.append(suite)

    json_path = write_json_report(report, "05_performance")
    md_path = write_md_summary(report, "05_performance")
    print(f"Performance report → {json_path}")
    print(f"Performance summary → {md_path}")
    for c in suite.cases:
        print(f"  {'✅' if c.passed else '❌'} {c.name}  — {c.metrics.get('latency_ms')}ms (target {c.metrics.get('target_ms')}ms)")


if __name__ == "__main__":
    main()
