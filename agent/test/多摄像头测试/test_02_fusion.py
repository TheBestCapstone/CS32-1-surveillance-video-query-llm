"""test_02_fusion.py — 融合层三路 RRF 测试。

输出: output/02_fusion.json, output/02_fusion.md
"""

from __future__ import annotations

import importlib.util
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


def _load_fusion_engine():
    spec = importlib.util.spec_from_file_location(
        "fusion_engine",
        str(ROOT_DIR / "agent" / "agents" / "shared" / "fusion_engine.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    setup_env()
    fe = _load_fusion_engine()

    report = TestReport(
        title="融合层三路 RRF 测试",
        started_at=datetime.now().isoformat(),
    )

    suite = TestSuite(name="weighted_rrf_fuse")

    with Timer() as t:
        base_sql = [{"event_id": 1, "video_id": "v1", "start_time": 1.0, "event_summary_en": "sql"}]
        base_hyb = [{"event_id": 2, "video_id": "v2", "start_time": 2.0, "event_summary_en": "hyb"}]

        # 1) 普通模式
        fused, meta = fe.weighted_rrf_fuse(base_sql, base_hyb, label="mixed", limit=10)
        suite.cases.append(TestCase(
            name="普通模式（无 GE rows）→ 二路 RRF",
            passed=(
                meta["label"] == "mixed"
                and meta["weights"]["global_entity"] == 0.0
                and meta["weights"]["sql"] > 0
                and meta["ge_count"] == 0
                and len(fused) == 2
            ),
            details=f"weights={meta['weights']} fused={len(fused)}",
            metrics=meta["weights"],
        ))

        # 2) 三路模式
        ge_rows = [
            {"global_entity_id": "ge1", "event_id": 100, "camera_id": "G329", "start_time": 10.0, "video_id": "v", "event_summary_en": "ge"},
            {"global_entity_id": "ge1", "event_id": 101, "camera_id": "G328", "start_time": 20.0, "video_id": "v", "event_summary_en": "ge2"},
        ]
        fused2, meta2 = fe.weighted_rrf_fuse(base_sql, base_hyb, label="mixed", limit=10, global_entity_rows=ge_rows)
        w = meta2["weights"]
        suite.cases.append(TestCase(
            name="多摄像头模式（GE rows）→ 三路 RRF GE=0.65 主导",
            passed=(
                meta2["label"] == "multi_camera"
                and abs(w["global_entity"] - 0.65) < 0.05
                and meta2["ge_count"] == 2
                and len(fused2) == 4
            ),
            details=f"weights={w} fused={len(fused2)}",
            metrics=w,
        ))

        # 3) GE 空列表退化
        fused3, meta3 = fe.weighted_rrf_fuse(base_sql, base_hyb, label="mixed", limit=10, global_entity_rows=[])
        suite.cases.append(TestCase(
            name="GE rows 为空列表 → 退化为普通模式",
            passed=meta3["label"] == "mixed" and meta3["weights"]["global_entity"] == 0.0,
            details=f"weights={meta3['weights']}",
            metrics=meta3["weights"],
        ))

        # 4) 全空不崩溃
        fused4, meta4 = fe.weighted_rrf_fuse([], [], label="mixed", limit=10)
        suite.cases.append(TestCase(
            name="所有分支为空 → 不报错返回空列表",
            passed=len(fused4) == 0,
            details=f"fused={len(fused4)}",
        ))

        # 5) _row_key
        k1 = fe._row_key({"event_id": 1})
        k2 = fe._row_key({"global_entity_id": "ge1", "start_time": 10.0})
        k3 = fe._row_key({"global_entity_id": "ge1", "start_time": 10.0})
        suite.cases.append(TestCase(
            name="_row_key 适配 global_entity_id",
            passed=(k1 == "event_id:1" and k2 == "ge:ge1:10.0" and k3 == k2),
            details=f"{k1} | {k2} | {k3}",
        ))

    report.suites.append(suite)
    report.elapsed_sec = t.elapsed_ms / 1000

    json_path = write_json_report(report, "02_fusion")
    md_path = write_md_summary(report, "02_fusion")
    print(f"Fusion report → {json_path}")
    print(f"Fusion summary → {md_path}")
    for c in suite.cases:
        print(f"  {'✅' if c.passed else '❌'} {c.name}")


if __name__ == "__main__":
    main()
