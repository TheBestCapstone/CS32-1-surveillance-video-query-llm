"""test_04_e2e.py — 端到端回归测试。

验证单摄像头查询不误触发 global_entity 分支，及 negative 问题行为。
输出: output/04_e2e.json, output/04_e2e.md
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
    load_questions,
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
    qc = _load_classifier()
    questions = load_questions()

    report = TestReport(
        title="端到端回归测试",
        started_at=datetime.now().isoformat(),
    )

    with Timer() as t:
        # ── Suite: 单摄回归 ──
        suite_regression = TestSuite(name="单摄像头回归（不误触发 GE）")

        single_cam_tests = [
            ("Is there a person with beige jacket visible in camera G328?", "existence"),
            ("Is there a person wearing black jacket in camera G339?", "appearance"),
            ("Is there a person with dark jacket visible in camera G424?", "existence"),
        ]
        for query, typ in single_cam_tests:
            result = qc._fallback_result("test", text=query)
            mc = result["multi_camera"]
            suite_regression.cases.append(TestCase(
                name=f"[{typ}] {query[:70]}",
                passed=not mc,
                details=f"multi_camera={mc} (expected=False)",
            ))

        report.suites.append(suite_regression)

        # ── Suite: negative 行为 ──
        suite_negative = TestSuite(name="negative 问题行为")
        neg_items = questions.get("negative", [])
        for item in neg_items[:5]:
            query = item["question"]
            result = qc._fallback_result("test", text=query)
            mc = result["multi_camera"]
            suite_negative.cases.append(TestCase(
                name=query[:80],
                passed=mc,  # should detect multi_camera intent
                details=f"multi_camera={mc} (expected=True for negative questions)",
            ))

        report.suites.append(suite_negative)

    report.elapsed_sec = t.elapsed_ms / 1000

    json_path = write_json_report(report, "04_e2e")
    md_path = write_md_summary(report, "04_e2e")
    print(f"E2E regression report → {json_path}")
    print(f"E2E regression summary → {md_path}")
    for s in report.suites:
        for c in s.cases:
            print(f"  {'✅' if c.passed else '❌'} {c.name}")


if __name__ == "__main__":
    main()
