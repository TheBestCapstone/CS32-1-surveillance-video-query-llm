import json
import sys
import time
from dataclasses import asdict, dataclass
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
class IterationEval:
    elapsed_ms: float
    route_mode: str | None
    label: str | None
    llm_final_output: str | None
    raw_final_answer: str | None
    rewritten_query: str | None
    original_user_query: str | None
    self_query_result: dict[str, Any] | None
    summary_result: dict[str, Any] | None
    routing_metrics: dict[str, Any] | None
    search_config: dict[str, Any] | None
    sql_plan: dict[str, Any] | None
    node_trace: list[str]
    final_answer: str | None
    tool_error: str | None
    error: str | None
    current_node: str | None
    top5: list[dict[str, Any]]
    merged_count: int
    sql_rows_count: int
    hybrid_rows_count: int
    degraded: bool | None
    hybrid_summary: str | None
    sql_summary: str | None
    hybrid_error: str | None
    sql_error: str | None
    sql_debug: dict[str, Any] | None


@dataclass
class CaseEval:
    case_id: str
    suite: str
    priority: str
    dimensions: list[str]
    description: str
    query: str
    iterations: list[IterationEval]
    assertions: list[dict[str, Any]]

    @property
    def status(self) -> str:
        hard_failed = any((not item["passed"]) and item.get("severity", "hard") == "hard" for item in self.assertions)
        soft_failed = any((not item["passed"]) and item.get("severity", "hard") == "soft" for item in self.assertions)
        if hard_failed:
            return "FAIL"
        if soft_failed:
            return "SOFT_FAIL"
        return "PASS"

    @property
    def avg_ms(self) -> float:
        return round(sum(item.elapsed_ms for item in self.iterations) / max(len(self.iterations), 1), 2)

    @property
    def p95_ms(self) -> float:
        vals = sorted(item.elapsed_ms for item in self.iterations)
        if not vals:
            return 0.0
        return vals[max(0, int(len(vals) * 0.95) - 1)]

    @property
    def last(self) -> IterationEval:
        return self.iterations[-1]


def _json_block(data: Any) -> str:
    return "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n"


def _select_final_rows(final_state: dict[str, Any]) -> list[dict[str, Any]]:
    if "rerank_result" in final_state:
        return list(final_state.get("rerank_result") or [])
    if "hybrid_result" in final_state:
        return list(final_state.get("hybrid_result") or [])
    return list(final_state.get("sql_result") or [])


def _top5_view(final_state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _select_final_rows(final_state)
    return [
        {
            "event_id": item.get("event_id"),
            "video_id": item.get("video_id"),
            "event_text": item.get("event_summary_en") or item.get("event_text_en") or item.get("event_text_cn"),
            "distance": item.get("_distance"),
        }
        for item in rows[:5]
    ]


def _collect_basketball_data_profile() -> dict[str, Any]:
    basket_dir = ROOT_DIR / "data" / "basketball"
    basket_output = ROOT_DIR / "data" / "basketball_output"
    files = sorted(p.name for p in basket_output.glob("*.json")) if basket_output.exists() else []
    return {
        "requested_path_exists": basket_dir.exists(),
        "actual_path": str(basket_output),
        "actual_path_exists": basket_output.exists(),
        "files": files,
    }


def _load_perf_baseline() -> dict[str, Any]:
    baseline_path = ROOT_DIR / "agent" / "test" / "perf_baseline.json"
    if not baseline_path.exists():
        return {}
    return json.loads(baseline_path.read_text(encoding="utf-8"))


def _normalize_perf_baseline_units(perf_baseline: dict[str, Any]) -> dict[str, Any]:
    if not perf_baseline:
        return {}
    normalized = dict(perf_baseline)
    time_keys = ["sql_p95_ms", "hybrid_p95_ms"]
    assume_seconds = any(isinstance(normalized.get(key), (int, float)) and 0 < float(normalized[key]) < 100 for key in time_keys)
    if assume_seconds:
        for key in time_keys:
            if isinstance(normalized.get(key), (int, float)):
                normalized[key] = round(float(normalized[key]) * 1000, 3)
        normalized["baseline_time_unit_assumed"] = "seconds_converted_to_ms"
    else:
        normalized["baseline_time_unit_assumed"] = "ms"
    return normalized


def _normalized_dimensions(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if raw is None:
        return []
    return [str(raw)]


def _append_assert(assertions: list[dict[str, Any]], name: str, passed: bool, actual: Any, expected: Any, severity: str = "hard"):
    assertions.append(
        {
            "name": name,
            "passed": passed,
            "actual": actual,
            "expected": expected,
            "severity": severity,
        }
    )


def _safe_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _citations_count(iteration: IterationEval) -> int:
    summary_result = iteration.summary_result if isinstance(iteration.summary_result, dict) else {}
    citations = summary_result.get("citations", [])
    return len(citations) if isinstance(citations, list) else 0


def _run_case_once(graph, question: str, thread_id: str) -> IterationEval:
    config = {"configurable": {"thread_id": thread_id, "user_id": "test-runner"}}
    last_chunk: dict[str, Any] = {}
    error = None
    node_trace: list[str] = []
    t0 = time.perf_counter()
    try:
        for chunk in graph.stream({"messages": [HumanMessage(content=question)]}, config, stream_mode="values"):
            last_chunk = chunk
            current_node = chunk.get("current_node")
            if current_node and (not node_trace or node_trace[-1] != current_node):
                node_trace.append(str(current_node))
    except Exception as exc:
        error = str(exc)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    sql_debug = last_chunk.get("sql_debug") if isinstance(last_chunk.get("sql_debug"), dict) else {}
    rows = _select_final_rows(last_chunk)
    fusion_meta = sql_debug.get("fusion_meta", {}) if isinstance(sql_debug, dict) else {}
    return IterationEval(
        elapsed_ms=elapsed_ms,
        route_mode=((last_chunk.get("tool_choice") or {}).get("mode") if isinstance(last_chunk.get("tool_choice"), dict) else None),
        label=((last_chunk.get("classification_result") or {}).get("label") if isinstance(last_chunk.get("classification_result"), dict) else None),
        llm_final_output=last_chunk.get("final_answer"),
        raw_final_answer=last_chunk.get("raw_final_answer"),
        rewritten_query=last_chunk.get("rewritten_query"),
        original_user_query=last_chunk.get("original_user_query"),
        self_query_result=last_chunk.get("self_query_result") if isinstance(last_chunk.get("self_query_result"), dict) else {},
        summary_result=last_chunk.get("summary_result") if isinstance(last_chunk.get("summary_result"), dict) else {},
        routing_metrics=last_chunk.get("routing_metrics") if isinstance(last_chunk.get("routing_metrics"), dict) else {},
        search_config=last_chunk.get("search_config") if isinstance(last_chunk.get("search_config"), dict) else {},
        sql_plan=last_chunk.get("sql_plan") if isinstance(last_chunk.get("sql_plan"), dict) else {},
        node_trace=node_trace,
        final_answer=last_chunk.get("final_answer"),
        tool_error=last_chunk.get("tool_error"),
        error=error,
        current_node=last_chunk.get("current_node"),
        top5=_top5_view(last_chunk) if not error else [],
        merged_count=len(rows),
        sql_rows_count=len(last_chunk.get("sql_result") or []),
        hybrid_rows_count=len(last_chunk.get("hybrid_result") or []),
        degraded=fusion_meta.get("degraded") if isinstance(fusion_meta, dict) else None,
        hybrid_summary=sql_debug.get("hybrid_summary"),
        sql_summary=sql_debug.get("sql_summary"),
        hybrid_error=sql_debug.get("hybrid_error"),
        sql_error=sql_debug.get("sql_error"),
        sql_debug=sql_debug,
    )


def _evaluate_case(graph, case: dict[str, Any], idx: int) -> CaseEval:
    case_id = str(case.get("case_id", f"CASE-{idx}"))
    query = str(case.get("query", ""))
    repeat = max(1, int(case.get("repeat", 1)))
    print(f"Running case {idx}: {case_id} x{repeat} - {query}")
    iterations: list[IterationEval] = []
    for run_idx in range(repeat):
        iterations.append(_run_case_once(graph, query, thread_id=f"{case_id}-{run_idx+1}"))

    expected_routes = list(case.get("expected_routes", []))
    if not expected_routes and case.get("expected_mode"):
        expected_routes = [str(case["expected_mode"])]

    expected_label = case.get("expected_label")
    min_results = case.get("min_results")
    max_results = case.get("max_results")
    min_sql_rows = case.get("min_sql_rows")
    min_hybrid_rows = case.get("min_hybrid_rows")
    max_avg_ms = case.get("max_avg_ms")
    required_top_fields = list(case.get("required_top_fields", []))
    expected_keywords_any = [str(item).lower() for item in case.get("expected_keywords_any", [])]
    keyword_severity = str(case.get("keyword_severity", "soft"))
    require_final_answer = bool(case.get("require_final_answer", False))
    allow_tool_error = bool(case.get("allow_tool_error", False))
    expect_semantic_backend = bool(case.get("expect_semantic_backend", False))
    check_hybrid_health = bool(case.get("check_hybrid_health", False))

    last = iterations[-1]
    top5 = last.top5
    merged_count = last.merged_count
    assertions: list[dict[str, Any]] = []

    _append_assert(
        assertions,
        "no_runtime_exception",
        all(item.error is None for item in iterations),
        [item.error for item in iterations if item.error],
        None,
        "hard",
    )
    if expected_label is not None:
        _append_assert(assertions, "label_matches", last.label == expected_label, last.label, expected_label, "hard")
    if expected_routes:
        _append_assert(assertions, "route_in_expected", last.route_mode in expected_routes, last.route_mode, expected_routes, "hard")
    if require_final_answer:
        ok = isinstance(last.final_answer, str) and last.final_answer.strip() != ""
        _append_assert(assertions, "final_answer_present", ok, last.final_answer, "non-empty string", "hard")
    if merged_count > 0:
        citation_ok = isinstance(last.final_answer, str) and "Sources:" in last.final_answer
        _append_assert(assertions, "citation_present", citation_ok, last.final_answer, "final answer contains Sources:", "soft")
        grounding_ok = _citations_count(last) > 0
        _append_assert(assertions, "grounding_coverage", grounding_ok, last.summary_result, "summary_result.citations is non-empty", "soft")
    if query.strip():
        rewrite_ok = isinstance(last.rewritten_query, str) and last.rewritten_query.strip() != ""
        _append_assert(assertions, "rewritten_query_present", rewrite_ok, last.rewritten_query, "non-empty rewritten query", "soft")
        need_ok = isinstance(last.self_query_result, dict) and bool(str(last.self_query_result.get("user_need", "")).strip())
        _append_assert(assertions, "user_need_identified", need_ok, last.self_query_result, "structured self-query result with user_need", "soft")
    trace_required_nodes = ["self_query_node", "final_answer_node", "summary_node"]
    trace_ok = all(node in last.node_trace for node in trace_required_nodes)
    _append_assert(assertions, "trace_has_required_nodes", trace_ok, last.node_trace, trace_required_nodes, "soft")
    routing_metrics_ok = isinstance(last.routing_metrics, dict) and bool(last.routing_metrics)
    _append_assert(assertions, "routing_metrics_present", routing_metrics_ok, last.routing_metrics, "non-empty routing_metrics", "soft")
    search_config_ok = isinstance(last.search_config, dict) and bool(last.search_config)
    _append_assert(assertions, "search_config_present", search_config_ok, last.search_config, "non-empty search_config", "soft")
    if last.label == "structured":
        sql_plan_ok = isinstance(last.sql_plan, dict) and bool(last.sql_plan)
        _append_assert(assertions, "sql_plan_present", sql_plan_ok, last.sql_plan, "non-empty sql_plan", "soft")
    if not allow_tool_error:
        _append_assert(assertions, "no_tool_error", last.tool_error is None, last.tool_error, None, "soft")
    if min_results is not None:
        _append_assert(assertions, "min_results", merged_count >= int(min_results), merged_count, min_results, "hard")
    if max_results is not None:
        _append_assert(assertions, "max_results", merged_count <= int(max_results), merged_count, max_results, "hard")
    if min_sql_rows is not None:
        _append_assert(assertions, "min_sql_rows", last.sql_rows_count >= int(min_sql_rows), last.sql_rows_count, min_sql_rows, "hard")
    if min_hybrid_rows is not None:
        _append_assert(assertions, "min_hybrid_rows", last.hybrid_rows_count >= int(min_hybrid_rows), last.hybrid_rows_count, min_hybrid_rows, "hard")
    if max_avg_ms is not None:
        _append_assert(assertions, "avg_latency_budget", sum(item.elapsed_ms for item in iterations) / len(iterations) <= float(max_avg_ms), round(sum(item.elapsed_ms for item in iterations) / len(iterations), 2), max_avg_ms, "soft")

    for field_name in required_top_fields:
        field_ok = all(item.get(field_name) is not None and str(item.get(field_name)).strip() != "" for item in top5) if top5 else False
        _append_assert(assertions, f"top_field_{field_name}", field_ok, [item.get(field_name) for item in top5], "non-empty", "soft")

    if expected_keywords_any:
        haystack = " ".join(str(item.get("event_text", "")) for item in top5).lower()
        matched = any(keyword in haystack for keyword in expected_keywords_any)
        _append_assert(assertions, "expected_keywords_any", matched, haystack, expected_keywords_any, keyword_severity)

    if expect_semantic_backend:
        semantic_backend_ok = last.hybrid_rows_count > 0 or bool(last.hybrid_error) or bool(last.degraded)
        _append_assert(
            assertions,
            "semantic_backend_effective",
            semantic_backend_ok,
            {
                "hybrid_rows_count": last.hybrid_rows_count,
                "hybrid_error": last.hybrid_error,
                "degraded": last.degraded,
            },
            "hybrid rows > 0 or explicit degradation/error",
            "hard",
        )

    if check_hybrid_health:
        summary_text = (last.hybrid_summary or "").lower()
        hidden_failure = "failed" in summary_text or "error" in summary_text
        health_ok = (not hidden_failure) or bool(last.hybrid_error) or bool(last.degraded)
        _append_assert(
            assertions,
            "hybrid_health_consistency",
            health_ok,
            {
                "hybrid_summary": last.hybrid_summary,
                "hybrid_error": last.hybrid_error,
                "degraded": last.degraded,
            },
            "hybrid failure should be reflected by degraded flag or hybrid_error",
            "hard",
        )

    return CaseEval(
        case_id=case_id,
        suite=str(case.get("suite", "default")),
        priority=str(case.get("priority", "P1")),
        dimensions=_normalized_dimensions(case.get("dimension")),
        description=str(case.get("description", "")),
        query=query,
        iterations=iterations,
        assertions=assertions,
    )


def run_comprehensive_tests(
    cases_path: Path | None = None,
    output_md: Path | None = None,
    output_json: Path | None = None,
    output_trends_md: Path | None = None,
) -> dict[str, Any]:
    cases_file = cases_path or (ROOT_DIR / "agent" / "test" / "comprehensive_cases_en.json")
    result_md = output_md or (ROOT_DIR / "agent" / "test" / "comprehensive_test_report.md")
    result_json = output_json or (ROOT_DIR / "agent" / "test" / "comprehensive_test_report.json")
    trends_md = output_trends_md or (ROOT_DIR / "agent" / "test" / "comprehensive_test_trends.md")

    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    graph = graph_module.create_graph()
    data_profile = _collect_basketball_data_profile()
    perf_baseline = _normalize_perf_baseline_units(_load_perf_baseline())

    evaluations = [_evaluate_case(graph, case, idx + 1) for idx, case in enumerate(cases)]

    total_count = len(evaluations)
    pass_count = sum(1 for item in evaluations if item.status == "PASS")
    soft_fail_count = sum(1 for item in evaluations if item.status == "SOFT_FAIL")
    fail_count = sum(1 for item in evaluations if item.status == "FAIL")
    all_iterations = [iteration for item in evaluations for iteration in item.iterations]
    all_elapsed = sorted(iteration.elapsed_ms for iteration in all_iterations)
    overall_avg_ms = round(sum(all_elapsed) / max(len(all_elapsed), 1), 2) if all_elapsed else 0.0
    overall_p95_ms = all_elapsed[max(0, int(len(all_elapsed) * 0.95) - 1)] if all_elapsed else 0.0

    failure_categories = {
        "runtime_exception": 0,
        "route_mismatch": 0,
        "label_mismatch": 0,
        "tool_error": 0,
        "semantic_backend_failure": 0,
        "keyword_mismatch": 0,
        "result_size_violation": 0,
        "hybrid_health_inconsistency": 0,
        "citation_missing": 0,
        "grounding_gap": 0,
        "trace_gap": 0,
        "routing_metrics_missing": 0,
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
            elif name == "label_matches":
                failure_categories["label_mismatch"] += 1
            elif name == "no_tool_error":
                failure_categories["tool_error"] += 1
            elif name == "semantic_backend_effective":
                failure_categories["semantic_backend_failure"] += 1
            elif name == "expected_keywords_any":
                failure_categories["keyword_mismatch"] += 1
            elif name in {"min_results", "max_results"}:
                failure_categories["result_size_violation"] += 1
            elif name == "hybrid_health_consistency":
                failure_categories["hybrid_health_inconsistency"] += 1
            elif name == "citation_present":
                failure_categories["citation_missing"] += 1
            elif name == "grounding_coverage":
                failure_categories["grounding_gap"] += 1
            elif name == "trace_has_required_nodes":
                failure_categories["trace_gap"] += 1
            elif name == "routing_metrics_present":
                failure_categories["routing_metrics_missing"] += 1

    dimension_summary: dict[str, dict[str, int]] = {}
    for item in evaluations:
        for dimension in item.dimensions:
            bucket = dimension_summary.setdefault(dimension, {"PASS": 0, "SOFT_FAIL": 0, "FAIL": 0})
            bucket[item.status] += 1

    priority_summary: dict[str, dict[str, int]] = {}
    for item in evaluations:
        bucket = priority_summary.setdefault(item.priority, {"PASS": 0, "SOFT_FAIL": 0, "FAIL": 0})
        bucket[item.status] += 1

    cases_with_results = [item for item in evaluations if item.last.merged_count > 0]
    metrics_summary = {
        "sql_branch_non_empty_rate": _safe_rate(sum(1 for item in evaluations if item.last.sql_rows_count > 0), total_count),
        "hybrid_branch_non_empty_rate": _safe_rate(sum(1 for item in evaluations if item.last.hybrid_rows_count > 0), total_count),
        "dual_branch_non_empty_rate": _safe_rate(sum(1 for item in evaluations if item.last.sql_rows_count > 0 and item.last.hybrid_rows_count > 0), total_count),
        "degraded_rate": _safe_rate(sum(1 for item in evaluations if item.last.degraded), total_count),
        "sql_error_rate": _safe_rate(sum(1 for item in evaluations if item.last.sql_error), total_count),
        "hybrid_error_rate": _safe_rate(sum(1 for item in evaluations if item.last.hybrid_error), total_count),
        "citation_coverage_rate": _safe_rate(sum(1 for item in cases_with_results if isinstance(item.last.final_answer, str) and "Sources:" in item.last.final_answer), len(cases_with_results)),
        "grounding_coverage_rate": _safe_rate(sum(1 for item in cases_with_results if _citations_count(item.last) > 0), len(cases_with_results)),
        "trace_coverage_rate": _safe_rate(sum(1 for item in evaluations if all(node in item.last.node_trace for node in ["self_query_node", "final_answer_node", "summary_node"])), total_count),
        "routing_metrics_coverage_rate": _safe_rate(sum(1 for item in evaluations if isinstance(item.last.routing_metrics, dict) and bool(item.last.routing_metrics)), total_count),
        "search_config_coverage_rate": _safe_rate(sum(1 for item in evaluations if isinstance(item.last.search_config, dict) and bool(item.last.search_config)), total_count),
        "sql_plan_coverage_rate": _safe_rate(sum(1 for item in evaluations if isinstance(item.last.sql_plan, dict) and bool(item.last.sql_plan)), total_count),
    }

    summary = {
        "total_cases": total_count,
        "passed": pass_count,
        "soft_failed": soft_fail_count,
        "failed": fail_count,
        "pass_rate": round(pass_count / max(total_count, 1), 4),
        "soft_fail_rate": round(soft_fail_count / max(total_count, 1), 4),
        "hard_fail_rate": round(fail_count / max(total_count, 1), 4),
        "iterations_total": len(all_iterations),
        "overall_avg_ms": overall_avg_ms,
        "overall_p95_ms": overall_p95_ms,
        "failure_categories": failure_categories,
        "dimension_summary": dimension_summary,
        "priority_summary": priority_summary,
        "metrics_summary": metrics_summary,
    }

    structured_cases = [item for item in evaluations if item.last.route_mode == "pure_sql"]
    semantic_route_cases = [item for item in evaluations if item.last.route_mode == "hybrid_search"]
    semantic_label_cases = [item for item in evaluations if item.last.label == "semantic"]
    trends = {
        "baseline": perf_baseline,
        "actual": {
            "pure_sql_avg_ms": round(sum(item.avg_ms for item in structured_cases) / max(len(structured_cases), 1), 2) if structured_cases else 0.0,
            "hybrid_search_avg_ms": round(sum(item.avg_ms for item in semantic_route_cases) / max(len(semantic_route_cases), 1), 2) if semantic_route_cases else 0.0,
            "semantic_label_cases_with_zero_hybrid_rows": sum(1 for item in semantic_label_cases if item.last.hybrid_rows_count == 0),
            "semantic_label_cases_total": len(semantic_label_cases),
        },
    }
    if perf_baseline.get("sql_p95_ms"):
        trends["actual"]["pure_sql_vs_baseline_ratio"] = round(trends["actual"]["pure_sql_avg_ms"] / float(perf_baseline["sql_p95_ms"]), 4)
    if perf_baseline.get("hybrid_p95_ms"):
        trends["actual"]["hybrid_vs_baseline_ratio"] = round(trends["actual"]["hybrid_search_avg_ms"] / float(perf_baseline["hybrid_p95_ms"]), 4)

    md_lines: list[str] = []
    md_lines.append("# Comprehensive Agent Test Report\n\n")
    md_lines.append(f"- Generated At: `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n")
    md_lines.append(f"- Cases File: `{cases_file}`\n")
    md_lines.append("- Data Profile:\n")
    md_lines.append(_json_block(data_profile))
    md_lines.append("- Summary:\n")
    md_lines.append(_json_block(summary))
    md_lines.append("- Metrics Summary:\n")
    md_lines.append(_json_block(metrics_summary))
    md_lines.append("- Trends:\n")
    md_lines.append(_json_block(trends))

    for item in evaluations:
        md_lines.append(f"\n## {item.case_id}\n")
        md_lines.append(f"- Suite: `{item.suite}`\n")
        md_lines.append(f"- Priority: `{item.priority}`\n")
        md_lines.append(f"- Dimensions: `{', '.join(item.dimensions)}`\n")
        md_lines.append(f"- Description: {item.description}\n")
        md_lines.append(f"- Query: `{item.query}`\n")
        md_lines.append(f"- Status: `{item.status}`\n")
        md_lines.append(f"- Avg Latency: `{item.avg_ms} ms`\n")
        md_lines.append(f"- P95 Latency: `{item.p95_ms} ms`\n")
        md_lines.append("- Node Trace:\n")
        md_lines.append(_json_block(item.last.node_trace))
        md_lines.append("- Routing Metrics:\n")
        md_lines.append(_json_block(item.last.routing_metrics))
        md_lines.append("- Search Config:\n")
        md_lines.append(_json_block(item.last.search_config))
        md_lines.append("- SQL Plan:\n")
        md_lines.append(_json_block(item.last.sql_plan))
        md_lines.append("- Self Query Result:\n")
        md_lines.append(_json_block(item.last.self_query_result))
        md_lines.append("- Raw Final Answer:\n")
        md_lines.append(_json_block({"raw_final_answer": item.last.raw_final_answer}))
        md_lines.append("- LLM Final Output:\n")
        md_lines.append(_json_block({"llm_final_output": item.last.llm_final_output}))
        md_lines.append("- Assertions:\n")
        md_lines.append(_json_block(item.assertions))
        md_lines.append("- Last Iteration:\n")
        md_lines.append(_json_block(asdict(item.last)))

    result_md.write_text("".join(md_lines), encoding="utf-8")
    result_json.write_text(
        json.dumps(
            {
                "summary": summary,
                "data_profile": data_profile,
                "trends": trends,
                "metrics_summary": metrics_summary,
                "cases": [
                    {
                        "case_id": item.case_id,
                        "suite": item.suite,
                        "priority": item.priority,
                        "dimensions": item.dimensions,
                        "description": item.description,
                        "query": item.query,
                        "status": item.status,
                        "avg_ms": item.avg_ms,
                        "p95_ms": item.p95_ms,
                        "raw_final_answer": item.last.raw_final_answer,
                        "rewritten_query": item.last.rewritten_query,
                        "original_user_query": item.last.original_user_query,
                        "self_query_result": item.last.self_query_result,
                        "summary_result": item.last.summary_result,
                        "routing_metrics": item.last.routing_metrics,
                        "search_config": item.last.search_config,
                        "sql_plan": item.last.sql_plan,
                        "node_trace": item.last.node_trace,
                        "llm_final_output": item.last.llm_final_output,
                        "assertions": item.assertions,
                        "iterations": [asdict(iteration) for iteration in item.iterations],
                    }
                    for item in evaluations
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    trend_lines: list[str] = []
    trend_lines.append("# Comprehensive Test Trends\n\n")
    trend_lines.append("- Baseline:\n")
    trend_lines.append(_json_block(perf_baseline))
    trend_lines.append("- Actual:\n")
    trend_lines.append(_json_block(trends["actual"]))
    trend_lines.append("- Notes:\n")
    trend_lines.append("- `semantic_label_cases_with_zero_hybrid_rows` is the primary indicator for whether semantic retrieval is truly active.\n")
    trend_lines.append("- `llm_final_output` is now emitted per case in both markdown and JSON reports for direct answer-level inspection.\n")
    trends_md.write_text("".join(trend_lines), encoding="utf-8")

    return {
        "summary": summary,
        "report_md": str(result_md),
        "report_json": str(result_json),
        "trends_md": str(trends_md),
    }


if __name__ == "__main__":
    out = run_comprehensive_tests()
    print(json.dumps(out, ensure_ascii=False, indent=2))
