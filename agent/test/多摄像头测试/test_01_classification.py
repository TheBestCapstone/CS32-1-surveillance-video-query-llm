"""test_01_classification.py — 多摄像头意图分类准确率测试。

测试 _detect_multi_camera() fast-path 在 60 道抽样题上的召回率 / 假阳性率。
输出: output/01_classification.json, output/01_classification.md
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
    OUTPUT_DIR,
    TestCase,
    TestSuite,
    TestReport,
    Timer,
    load_questions,
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
    questions = load_questions()
    qc = _load_classifier()

    report = TestReport(
        title="分类层 fast-path 准确率测试",
        started_at=datetime.now().isoformat(),
    )

    suite = TestSuite(name="fast-path 分类准确率")

    expected_map = {
        "cross_camera": True,
        "negative": True,
        "existence": False,
        "appearance": False,
        "event": False,
    }

    with Timer() as t:
        for category, expected_mc in expected_map.items():
            items = questions.get(category, [])
            for item in items:
                query = item["question"]
                signals = qc._collect_signals(query)
                mc = qc._detect_multi_camera(signals)
                passed = mc == expected_mc
                suite.cases.append(
                    TestCase(
                        name=f"[{category}] {query[:70]}",
                        passed=passed,
                        details=f"expected={expected_mc} actual={mc} cues={signals.get('multi_camera_cues', [])}",
                    )
                )

    # Per-category summary
    for category in ("cross_camera", "negative", "existence", "appearance", "event"):
        cat_cases = [c for c in suite.cases if f"[{category}]" in c.name]
        cat_passed = sum(1 for c in cat_cases if c.passed)
        cat_total = len(cat_cases)
        if cat_total:
            pct = cat_passed / cat_total * 100
            target = 95 if expected_map[category] else 90
            suite.cases.append(
                TestCase(
                    name=f"[汇总] {category}",
                    passed=pct >= target,
                    details=f"{cat_passed}/{cat_total} correct ({pct:.1f}%)",
                    metrics={"accuracy_pct": pct, "target_pct": target},
                )
            )

    report.suites.append(suite)
    report.elapsed_sec = t.elapsed_ms / 1000

    json_path = write_json_report(report, "01_classification")
    md_path = write_md_summary(report, "01_classification")
    print(f"Classification report → {json_path}")
    print(f"Classification summary → {md_path}")
    print(f"Passed: {report.passed}/{report.total}")


if __name__ == "__main__":
    main()
