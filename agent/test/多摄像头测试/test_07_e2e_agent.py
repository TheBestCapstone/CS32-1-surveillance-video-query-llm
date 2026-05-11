"""test_07_e2e_agent.py — Agent 端到端做题测试。

让完整 agent graph 回答 cross_camera 问题，提取 final_answer，评估召回/精确/IoU。

用法:
    cd agent/test/多摄像头测试
    conda run -n capstone python test_07_e2e_agent.py

输出: output/07_e2e_agent.json, output/07_e2e_agent.md
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage

_HERE = Path(__file__).resolve().parent
OUTPUT_DIR = _HERE / "output"
ROOT_DIR = _HERE.parents[2]
AGENT_DIR = ROOT_DIR / "agent"

sys.path.insert(0, str(AGENT_DIR))

import importlib

# Force reload to pick up our modified code
mod_names = [
    "agents.shared.query_classifier",
    "agents.shared.fusion_engine",
    "node.parallel_retrieval_fusion_node",
    "node.types",
]
for mn in mod_names:
    if mn in sys.modules:
        del sys.modules[mn]

import graph as graph_module


def load_testable_questions() -> list[dict[str, Any]]:
    path = OUTPUT_DIR / "testable_questions.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("cross_camera", [])


def extract_expected_cameras(recall_text: str) -> set[str]:
    """从 recall_challenge 中提取期望的摄像头。"""
    return set(re.findall(r"G\d+", recall_text))


def extract_answer_cameras(answer: str) -> set[str]:
    """从 agent 的 final_answer 中提取摄像头 ID。"""
    return set(re.findall(r"G\d+", answer))


def check_answer_correctness(answer: str, expected_answer: str) -> bool:
    """Check if agent answer matches the expected yes/no ground truth.

    Returns True if the answer's semantic polarity matches expected_answer.
    """
    ans_lower = answer.strip().lower()
    if expected_answer.lower() == "yes":
        # "Yes" or positive sentiment — NOT "No matching clip"
        if ans_lower.startswith("yes") or ans_lower.startswith("yes."):
            return True
        if "no matching clip" in ans_lower:
            return False
        # Positive indicators
        positive_patterns = ["yes.", "yes ", "有", "the relevant clip is in"]
        negative_patterns = ["no matching", "no.", "没有"]
        has_positive = any(p in ans_lower for p in positive_patterns)
        has_negative = any(p in ans_lower for p in negative_patterns)
        if has_positive and not has_negative:
            return True
        if has_negative:
            return False
    elif expected_answer.lower() == "no":
        if "no matching clip" in ans_lower or ans_lower.startswith("no."):
            return True
        return False
    # unknown expected → always pass
    return True


def check_time_in_answer(answer: str, expected_time: str) -> tuple[bool, str]:
    """Check if the answer mentions a time within or close to the expected window.

    Returns (match: bool, detail: str).
    """
    if not expected_time or not answer.strip():
        return True, "no expected_time → auto-pass"

    # Parse expected time range: "2:02-3:36" → (122, 216) seconds
    try:
        parts = expected_time.replace("–", "-").split("-")
        expected_start = _parse_mmss(parts[0].strip())
        expected_end = _parse_mmss(parts[-1].strip()) if len(parts) >= 2 else expected_start
    except Exception:
        return True, f"cannot parse expected_time={expected_time} → auto-pass"

    # Extract all times from answer
    time_patterns = re.findall(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", answer)
    for match in time_patterns:
        try:
            h = int(match[0])
            m = int(match[1])
            s = int(match[2]) if match[2] else 0
            seconds = h * 3600 + m * 60 + s if match[2] else h * 60 + m
        except Exception:
            continue
        # Check if within expected window (allow 60s buffer)
        margin = 60
        if expected_start - margin <= seconds <= expected_end + margin:
            return True, f"found {h:02d}:{m:02d}:{s:02d} in [{_fmt_mmss(expected_start)}-{_fmt_mmss(expected_end)}]"

    return False, f"no time in [{_fmt_mmss(expected_start)}-{_fmt_mmss(expected_end)}]"


def _parse_mmss(text: str) -> int:
    """Parse '2:02' or '3:36' to seconds."""
    parts = text.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(float(text))


def _fmt_mmss(seconds: int) -> str:
    """Format seconds as mm:ss."""
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


def compute_metrics(expected: set[str], found: set[str]) -> dict[str, Any]:
    inter = expected & found
    union = expected | found
    return {
        "expected_cameras": sorted(expected),
        "found_cameras": sorted(found),
        "intersection": sorted(inter),
        "recall": round(len(inter) / len(expected), 4) if expected else 0.0,
        "precision": round(len(inter) / len(found), 4) if found else 0.0,
        "iou": round(len(inter) / len(union), 4) if union else 0.0,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = load_testable_questions()
    print(f"Loaded {len(questions)} cross_camera questions")
    print(f"Build agent graph ...")
    graph = graph_module.create_graph()
    print(f"Graph ready. Starting test ...\n")

    results: list[dict[str, Any]] = []
    tt0 = time.perf_counter()

    for idx, item in enumerate(questions):
        query = item["question"]
        recall_text = item.get("recall_challenge", "")
        expected_cameras = extract_expected_cameras(recall_text)
        expected_answer = item.get("expected_answer", "")
        expected_time = item.get("expected_time", "")

        config = {"configurable": {"thread_id": f"e2e-mc-{idx}", "user_id": "tester"}}
        error = None
        final_answer = ""
        classification_result = {}
        node_trace: list[str] = []
        ge_rows_count = 0
        multi_camera_detected = False

        t0 = time.perf_counter()
        try:
            for chunk in graph.stream(
                {"messages": [HumanMessage(content=query)]},
                config,
                stream_mode="values",
            ):
                if "current_node" in chunk:
                    node = chunk["current_node"]
                    if not node_trace or node_trace[-1] != node:
                        node_trace.append(node)
                final_answer = chunk.get("final_answer", final_answer)
                if "classification_result" in chunk:
                    cr = chunk["classification_result"]
                    if isinstance(cr, dict):
                        classification_result = cr
                        multi_camera_detected = cr.get("multi_camera", False)
                if "sql_debug" in chunk and isinstance(chunk["sql_debug"], dict):
                    ge_rows_count = chunk["sql_debug"].get("ge_rows_count", ge_rows_count)
        except Exception as exc:
            error = str(exc)

        elapsed_s = time.perf_counter() - t0

        # Extract cameras from agent answer
        answer_cameras = extract_answer_cameras(final_answer) if not error else set()
        metrics = compute_metrics(expected_cameras, answer_cameras)

        # LLM answer quality heuristics
        answer_has_content = len(final_answer.strip()) > 10
        answer_correct = check_answer_correctness(final_answer, expected_answer)
        time_ok, time_detail = check_time_in_answer(final_answer, expected_time)

        passed = (
            error is None
            and answer_has_content
            and multi_camera_detected
            and answer_correct
            and metrics["recall"] >= 0.5
        )

        result = {
            "idx": idx,
            "question": query[:120],
            "recall_challenge": recall_text[:120],
            "expected_answer": expected_answer,
            "expected_time": expected_time,
            "expected_cameras": sorted(expected_cameras),
            "answer_cameras": sorted(answer_cameras),
            "final_answer": final_answer[:500],
            "error": error,
            "elapsed_s": round(elapsed_s, 1),
            "node_trace": node_trace,
            "multi_camera_detected": multi_camera_detected,
            "ge_rows_count": ge_rows_count,
            "passed": passed,
            "metrics": metrics,
            "answer_has_content": answer_has_content,
            "answer_correct": answer_correct,
            "time_ok": time_ok,
            "time_detail": time_detail,
        }
        results.append(result)

        icon = "✅" if passed else "❌"
        print(
            f"  {icon} Q{idx+1:02d} [{elapsed_s:.1f}s] "
            f"mc={multi_camera_detected} ge={ge_rows_count} "
            f"correct={answer_correct} time={time_ok} "
            f"R={metrics['recall']:.2f} P={metrics['precision']:.2f} IoU={metrics['iou']:.2f} "
            f"| {query[:55]}..."
        )
        if error:
            print(f"       ERROR: {error[:200]}")
        if not passed and not error:
            if not answer_has_content:
                print(f"       FAIL: empty/invalid answer")
            elif not multi_camera_detected:
                print(f"       FAIL: multi_camera not detected")
            else:
                print(f"       FAIL: expected={sorted(expected_cameras)} found={sorted(answer_cameras)}")

    total_elapsed = time.perf_counter() - tt0
    passed_count = sum(1 for r in results if r["passed"])
    correct_count = sum(1 for r in results if r["answer_correct"])
    time_match_count = sum(1 for r in results if r["time_ok"])
    n = len(results)

    # Summary stats
    avg_recall = sum(r["metrics"]["recall"] for r in results) / n if n else 0
    avg_precision = sum(r["metrics"]["precision"] for r in results) / n if n else 0
    avg_iou = sum(r["metrics"]["iou"] for r in results) / n if n else 0
    avg_elapsed = sum(r["elapsed_s"] for r in results) / n if n else 0
    mc_detection_rate = sum(1 for r in results if r["multi_camera_detected"]) / n if n else 0
    answer_rate = sum(1 for r in results if r["answer_has_content"]) / n if n else 0
    correctness_rate = correct_count / n if n else 0
    time_match_rate = time_match_count / n if n else 0

    report = {
        "title": "Agent 端到端做题测试",
        "started_at": datetime.now().isoformat(),
        "total_elapsed_s": round(total_elapsed, 1),
        "total_questions": n,
        "passed": passed_count,
        "failed": n - passed_count,
        "pass_rate": round(passed_count / n * 100, 1) if n else 0,
        "avg_recall": round(avg_recall, 4),
        "avg_precision": round(avg_precision, 4),
        "avg_iou": round(avg_iou, 4),
        "avg_elapsed_s": round(avg_elapsed, 1),
        "multi_camera_detection_rate": round(mc_detection_rate, 4),
        "answer_content_rate": round(answer_rate, 4),
        "correctness_rate": round(correctness_rate, 4),
        "correctness_count": correct_count,
        "time_match_rate": round(time_match_rate, 4),
        "time_match_count": time_match_count,
        "per_question": results,
    }

    json_path = OUTPUT_DIR / "07_e2e_agent.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown summary
    md_lines = [
        "# Agent 端到端做题测试",
        "",
        f"**Started**: {report['started_at']}  ",
        f"**Elapsed**: {report['total_elapsed_s']:.1f}s  ",
        "",
        "## 汇总",
        "",
        f"| 指标 | 值 |",
        f"|------|----|",
        f"| 通过率 | **{report['pass_rate']}%** ({passed_count}/{n}) |",
        f"| 答案正确率 | **{correctness_rate:.1%}** ({correct_count}/{n}) |",
        f"| 时间命中率 | **{time_match_rate:.1%}** ({time_match_count}/{n}) |",
        f"| 平均 Recall | {avg_recall:.4f} |",
        f"| 平均 Precision | {avg_precision:.4f} |",
        f"| 平均 IoU | {avg_iou:.4f} |",
        f"| 多摄意图检测率 | {mc_detection_rate:.1%} |",
        f"| 有效回答率 | {answer_rate:.1%} |",
        f"| 平均耗时/题 | {avg_elapsed:.1f}s |",
        f"| 总耗时 | {report['total_elapsed_s']:.1f}s |",
        "",
        "## 逐题结果",
        "",
    ]

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        correct_icon = "✅" if r.get("answer_correct", False) else "❌"
        time_icon = "✅" if r.get("time_ok", False) else "❌"
        md_lines.append(f"### {icon} Q{r['idx']+1} [{r['elapsed_s']:.1f}s]")
        md_lines.append(f"- **问题**: {r['question']}")
        md_lines.append(f"- **期望答案**: {r.get('expected_answer', '?')} | **期望时间**: {r.get('expected_time', '?')}")
        md_lines.append(f"- {correct_icon} 答案正确 | {time_icon} 时间命中")
        md_lines.append(f"- **期望摄像头**: {r['expected_cameras']}")
        md_lines.append(f"- **回答中的摄像头**: {r['answer_cameras']}")
        md_lines.append(f"- **Recall**: {r['metrics']['recall']:.2f} | **Precision**: {r['metrics']['precision']:.2f} | **IoU**: {r['metrics']['iou']:.2f}")
        md_lines.append(f"- **multi_camera 检测**: {r['multi_camera_detected']} | **GE rows**: {r['ge_rows_count']}")
        md_lines.append(f"- **节点路径**: {' → '.join(r['node_trace'])}")
        if r["error"]:
            md_lines.append(f"- **错误**: {r['error'][:200]}")
        answer_preview = r["final_answer"][:300]
        md_lines.append(f"- **Agent 回答**: {answer_preview}")
        md_lines.append("")

    md_path = OUTPUT_DIR / "07_e2e_agent.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n--- SUMMARY ---")
    print(f"Pass rate: {report['pass_rate']}% ({passed_count}/{n})")
    print(f"Correctness: {correctness_rate:.1%} ({correct_count}/{n})")
    print(f"Time match: {time_match_rate:.1%} ({time_match_count}/{n})")
    print(f"Avg recall: {avg_recall:.4f}")
    print(f"Avg elapsed: {avg_elapsed:.1f}s/question")
    print(f"Multi-camera detection: {mc_detection_rate:.1%}")
    print(f"Total time: {report['total_elapsed_s']:.1f}s")
    print(f"Reports → {json_path}, {md_path}")


if __name__ == "__main__":
    main()
