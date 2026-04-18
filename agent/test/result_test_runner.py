import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT_DIR / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import graph as graph_module  # noqa: E402


@dataclass
class CaseEval:
    case_id: str
    question: str
    expected_answer: str
    route_mode: str | None
    model_answer: str | None
    elapsed_ms: float
    top5: list[dict[str, Any]]
    assertions: list[dict[str, Any]]
    error: str | None
    tool_error: str | None
    thought: str | None
    current_node: str | None
    sql_debug: dict[str, Any] | None

    @property
    def status(self) -> str:
        hard_failed = any((not item["passed"]) and item.get("severity", "hard") == "hard" for item in self.assertions)
        soft_failed = any((not item["passed"]) and item.get("severity", "hard") == "soft" for item in self.assertions)
        if hard_failed:
            return "FAIL"
        if soft_failed:
            return "SOFT_FAIL"
        return "PASS"


def _json_block(data: Any) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n"


def _top5_view(final_state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = final_state.get("rerank_result") or final_state.get("hybrid_result") or final_state.get("sql_result") or []
    return [
        {
            "video_id": item.get("video_id"),
            "event_text": item.get("event_summary_en") or item.get("event_text_cn"),
        }
        for item in rows[:5]
    ]


def _collect_mock_data_profile() -> dict[str, Any]:
    mock_file = ROOT_DIR / "agent" / "mock_data" / "data" / "video_events_mock_en.json"
    if not mock_file.exists():
        return {"exists": False}
    data = json.loads(mock_file.read_text(encoding="utf-8"))
    videos = data if isinstance(data, list) else [data]
    object_types: set[str] = set()
    colors: set[str] = set()
    zones: set[str] = set()
    event_count = 0
    for video in videos:
        events = video.get("events", []) if isinstance(video, dict) else []
        event_count += len(events)
        for event in events[:1000]:
            object_types.add(str(event.get("object_type", "")).strip())
            colors.add(str(event.get("object_color_en", "")).strip())
            zones.add(str(event.get("scene_zone_en", "")).strip())
    return {
        "exists": True,
        "video_count": len(videos),
        "event_count": event_count,
        "object_types_sample": sorted([x for x in object_types if x])[:20],
        "colors_sample": sorted([x for x in colors if x])[:20],
        "scene_zones_sample": sorted([x for x in zones if x])[:20],
    }


def run_result_tests(
    cases_path: Path | None = None,
    output_md: Path | None = None,
    output_json: Path | None = None,
) -> dict[str, Any]:
    cases_file = cases_path or (ROOT_DIR / "agent" / "test" / "result_cases.json")
    result_md = output_md or (ROOT_DIR / "result.md")
    result_json = output_json or (ROOT_DIR / "result_report.json")

    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    graph = graph_module.create_graph()
    mock_profile = _collect_mock_data_profile()

    evaluations: list[CaseEval] = []
    for idx, case in enumerate(cases, start=1):
        question = str(case.get("question") or case.get("query", ""))
        print(f"Running case {idx}/{len(cases)}: {case.get('case_id')} - {question}")
        expected_answer = str(case.get("expected_answer", ""))
        if "expected_mode" in case:
            expected_routes = [case["expected_mode"]]
        else:
            expected_routes = list(case.get("expected_routes", []))
        min_results = int(case.get("min_results", 0))
        required_top_fields = list(case.get("required_top_fields", []))

        config = {"configurable": {"thread_id": f"result-case-{idx}", "user_id": "tester"}}
        last_chunk: dict[str, Any] = {}
        error = None
        t0 = time.perf_counter()
        try:
            for chunk in graph.stream({"messages": [HumanMessage(content=question)]}, config, stream_mode="values"):
                if "current_node" in chunk:
                    print(f"  -> At node: {chunk['current_node']}")
                last_chunk = chunk
        except Exception as exc:
            error = str(exc)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        route_mode = (last_chunk.get("tool_choice") or {}).get("mode")
        model_answer = last_chunk.get("final_answer")
        top5 = _top5_view(last_chunk) if not error else []
        tool_error = last_chunk.get("tool_error")
        thought = last_chunk.get("thought")
        current_node = last_chunk.get("current_node")
        sql_debug = last_chunk.get("sql_debug")

        assertions: list[dict[str, Any]] = []
        assertions.append({
            "name": "no_runtime_exception",
            "passed": error is None,
            "actual": error,
            "expected": None,
            "severity": "hard",
        })
        assertions.append({
            "name": "route_in_expected",
            "passed": (not expected_routes) or (route_mode in expected_routes),
            "actual": route_mode,
            "expected": expected_routes,
            "severity": "hard",
        })
        assertions.append({
            "name": "no_tool_error",
            "passed": tool_error is None,
            "actual": tool_error,
            "expected": None,
            "severity": "soft",
        })
        assertions.append({
            "name": "min_results",
            "passed": len(top5) >= min_results,
            "actual": len(top5),
            "expected": min_results,
            "severity": "soft",
        })
        for field_name in required_top_fields:
            field_ok = all((item.get(field_name) is not None and str(item.get(field_name)).strip() != "") for item in top5) if top5 else True
            assertions.append({
                "name": f"top_field_{field_name}",
                "passed": field_ok,
                "actual": [item.get(field_name) for item in top5],
                "expected": "non-empty when top rows exist",
                "severity": "soft",
            })

        evaluations.append(
            CaseEval(
                case_id=str(case.get("case_id", f"CASE-{idx}")),
                question=question,
                expected_answer=expected_answer,
                route_mode=route_mode,
                model_answer=model_answer,
                elapsed_ms=elapsed_ms,
                top5=top5,
                assertions=assertions,
                error=error,
                tool_error=tool_error,
                thought=thought,
                current_node=current_node,
                sql_debug=sql_debug,
            )
        )

    pass_count = sum(1 for item in evaluations if item.status == "PASS")
    soft_fail_count = sum(1 for item in evaluations if item.status == "SOFT_FAIL")
    fail_count = sum(1 for item in evaluations if item.status == "FAIL")
    total_count = len(evaluations)
    avg_ms = round(sum(item.elapsed_ms for item in evaluations) / max(total_count, 1), 2)
    p95_ms = sorted([item.elapsed_ms for item in evaluations])[max(0, int(total_count * 0.95) - 1)] if total_count else 0.0
    summary = {
        "total": total_count,
        "passed": pass_count,
        "soft_failed": soft_fail_count,
        "failed": fail_count,
        "pass_rate": round(pass_count / max(total_count, 1), 4),
        "soft_fail_rate": round(soft_fail_count / max(total_count, 1), 4),
        "hard_fail_rate": round(fail_count / max(total_count, 1), 4),
        "avg_ms": avg_ms,
        "p95_ms": p95_ms,
    }
    failure_categories = {
        "runtime_exception": 0,
        "route_mismatch": 0,
        "tool_error": 0,
        "insufficient_results": 0,
        "top_field_missing": 0,
    }
    for item in evaluations:
        for assertion in item.assertions:
            if assertion["passed"]:
                continue
            name = assertion["name"]
            if name == "no_runtime_exception":
                failure_categories["runtime_exception"] += 1
            elif name == "route_in_expected":
                failure_categories["route_mismatch"] += 1
            elif name == "no_tool_error":
                failure_categories["tool_error"] += 1
            elif name == "min_results":
                failure_categories["insufficient_results"] += 1
            elif name.startswith("top_field_"):
                failure_categories["top_field_missing"] += 1
    summary["failure_categories"] = failure_categories

    md_lines: list[str] = []
    md_lines.append("# Graph Result Test Report\n")
    md_lines.append(f"- Generated At: `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")
    md_lines.append(f"- Cases File: `{cases_file}`\n")
    md_lines.append("- Mock Data Profile:\n")
    md_lines.append(_json_block(mock_profile))
    md_lines.append("- Summary:\n")
    md_lines.append(_json_block(summary))

    for item in evaluations:
        md_lines.append(f"\n## {item.case_id}\n")
        md_lines.append(f"- 问题: `{item.question}`\n")
        md_lines.append(f"- 预期答案: {item.expected_answer}\n")
        md_lines.append(f"- 模型返回答案: `{item.model_answer}`\n")
        md_lines.append(f"- 路由模式: `{item.route_mode}`\n")
        md_lines.append(f"- 当前节点: `{item.current_node}`\n")
        md_lines.append(f"- 耗时: `{item.elapsed_ms} ms`\n")
        md_lines.append(f"- 错误: `{item.error}`\n")
        md_lines.append(f"- 工具错误: `{item.tool_error}`\n")
        md_lines.append(f"- 结果: `{item.status}`\n")
        md_lines.append("- 断言明细:\n")
        md_lines.append(_json_block(item.assertions))
        md_lines.append("- Top1-Top5:\n")
        md_lines.append(_json_block(item.top5))
        md_lines.append("- Thought:\n")
        md_lines.append(_json_block({"thought": item.thought}))
        if item.sql_debug:
            md_lines.append("- SQL Debug:\n")
            md_lines.append(_json_block(item.sql_debug))

    result_md.write_text("".join(md_lines), encoding="utf-8")
    result_json.write_text(
        json.dumps(
            {
                "summary": summary,
                "mock_profile": mock_profile,
                "cases": [
                    {
                        "case_id": item.case_id,
                        "question": item.question,
                        "expected_answer": item.expected_answer,
                        "route_mode": item.route_mode,
                        "model_answer": item.model_answer,
                        "elapsed_ms": item.elapsed_ms,
                        "error": item.error,
                        "tool_error": item.tool_error,
                        "assertions": item.assertions,
                        "top5": item.top5,
                        "status": item.status,
                        "thought": item.thought,
                        "sql_debug": item.sql_debug,
                    }
                    for item in evaluations
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {"summary": summary, "result_md": str(result_md), "result_json": str(result_json)}


if __name__ == "__main__":
    out = run_result_tests()
    print(json.dumps(out, ensure_ascii=False, indent=2))
