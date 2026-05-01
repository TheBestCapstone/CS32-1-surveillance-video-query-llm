from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI, OpenAI

from ragas.embeddings.base import BaseRagasEmbedding, embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecisionWithReference,
    ContextRecall,
    Faithfulness,
    FactualCorrectness,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT_DIR / "agent"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from agent.core.runtime import load_env  # noqa: E402
from agent.db.chroma_builder import ChromaBuildConfig, ChromaIndexBuilder  # noqa: E402
from agent.db.sqlite_builder import SQLiteBuildConfig, SQLiteDatabaseBuilder  # noqa: E402
from agent_test_importer import AgentTestDatasetImporter, AgentTestImportConfig  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402


DEFAULT_XLSX_PATH = ROOT_DIR / "agent" / "test" / "agent_test.xlsx"
DEFAULT_SEED_DIR = ROOT_DIR / "agent" / "test" / "generated" / "ucfcrime_events_vector_flat"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "agent" / "test" / "generated" / "ragas_eval"
DEFAULT_INCLUDE_SHEETS = ["Part1", "Part4"]
EMBEDDING_BATCH_LIMIT = 10
DEFAULT_RAGAS_MODEL = "gpt-4o"
DEFAULT_RAGAS_EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass
class EvalPaths:
    dataset_dir: Path
    runtime_dir: Path
    sqlite_path: Path
    chroma_path: Path
    retrieval_report_json: Path
    generation_report_json: Path
    e2e_report_json: Path
    summary_report_json: Path
    summary_report_md: Path


class OpenAICompatibleRagasEmbedding(BaseRagasEmbedding):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None,
        model: str = DEFAULT_RAGAS_EMBEDDING_MODEL,
        dimensions: int | None = None,
    ) -> None:
        super().__init__()
        self.model = model
        self.dimensions = dimensions
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.sync_client = OpenAI(**client_kwargs)
        self.async_client = AsyncOpenAI(**client_kwargs)

    def embed_text(self, text: str, **kwargs: Any) -> list[float]:
        request = {
            "input": text,
            "model": self.model,
            "encoding_format": "float",
            **kwargs,
        }
        if self.dimensions is not None:
            request["dimensions"] = self.dimensions
        response = self.sync_client.embeddings.create(**request)
        return response.data[0].embedding

    async def aembed_text(self, text: str, **kwargs: Any) -> list[float]:
        request = {
            "input": text,
            "model": self.model,
            "encoding_format": "float",
            **kwargs,
        }
        if self.dimensions is not None:
            request["dimensions"] = self.dimensions
        response = await self.async_client.embeddings.create(**request)
        return response.data[0].embedding

    async def aembed_texts(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        outputs: list[list[float]] = []
        for start in range(0, len(texts), EMBEDDING_BATCH_LIMIT):
            batch = texts[start : start + EMBEDDING_BATCH_LIMIT]
            request = {
                "input": batch,
                "model": self.model,
                "encoding_format": "float",
                **kwargs,
            }
            if self.dimensions is not None:
                request["dimensions"] = self.dimensions
            response = await self.async_client.embeddings.create(**request)
            sorted_items = sorted(response.data, key=lambda item: item.index)
            outputs.extend(item.embedding for item in sorted_items)
        return outputs


def _default_paths(output_dir: Path) -> EvalPaths:
    dataset_dir = output_dir / "dataset_part1_part4"
    runtime_dir = output_dir / "runtime"
    return EvalPaths(
        dataset_dir=dataset_dir,
        runtime_dir=runtime_dir,
        sqlite_path=runtime_dir / "eval_subset.sqlite",
        chroma_path=runtime_dir / "eval_subset_chroma",
        retrieval_report_json=output_dir / "retrieval_report.json",
        generation_report_json=output_dir / "generation_report.json",
        e2e_report_json=output_dir / "e2e_report.json",
        summary_report_json=output_dir / "summary_report.json",
        summary_report_md=output_dir / "summary_report.md",
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _select_final_rows(final_state: dict[str, Any]) -> list[dict[str, Any]]:
    if "rerank_result" in final_state:
        return list(final_state.get("rerank_result") or [])
    if "merged_result" in final_state:
        return list(final_state.get("merged_result") or [])
    if "hybrid_result" in final_state:
        return list(final_state.get("hybrid_result") or [])
    return list(final_state.get("sql_result") or [])


def _row_context_text(row: dict[str, Any]) -> str:
    return str(
        row.get("event_summary_en")
        or row.get("event_text_en")
        or row.get("event_text_cn")
        or row.get("event_text")
        or ""
    ).strip()


def _strip_sources(text: str | None) -> str:
    body = str(text or "").strip()
    if "\nSources:" in body:
        body = body.split("\nSources:", 1)[0].strip()
    return body


def _mean(values: list[float | None]) -> float | None:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return round(statistics.mean(nums), 4)


def _truncate_text(text: str | None, max_chars: int) -> str:
    value = str(text or "").strip()
    if max_chars <= 0 or len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + " ..."


def _compact_contexts(
    contexts: list[str],
    *,
    max_contexts: int,
    max_chars_per_context: int,
    max_total_chars: int,
) -> list[str]:
    compacted: list[str] = []
    total_chars = 0
    for context in contexts[:max_contexts]:
        item = _truncate_text(context, max_chars_per_context)
        if not item:
            continue
        projected = total_chars + len(item)
        if compacted and projected > max_total_chars:
            break
        compacted.append(item)
        total_chars = projected
    return compacted


def _load_filtered_cases(
    *,
    xlsx_path: Path,
    dataset_dir: Path,
    include_sheets: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    config = AgentTestImportConfig(
        xlsx_path=xlsx_path,
        output_dir=dataset_dir,
        sqlite_path=dataset_dir / "agent_test_eval.sqlite",
        normalized_json_path=dataset_dir / "agent_test_normalized.json",
        report_json_path=dataset_dir / "agent_test_import_report.json",
        retrieval_view_path=dataset_dir / "agent_test_retrieval_eval.json",
        e2e_view_path=dataset_dir / "agent_test_e2e_eval.json",
        generation_view_path=dataset_dir / "agent_test_generation_eval.json",
        reset_existing=True,
        include_sheets=include_sheets,
    )
    report = AgentTestDatasetImporter(config).build()
    cases = json.loads(config.normalized_json_path.read_text(encoding="utf-8"))
    filtered = [case for case in cases if case.get("e2e_ready") == 1]
    return filtered, report


def _resolve_seed_files(seed_dir: Path, cases: list[dict[str, Any]]) -> list[Path]:
    unique_ids = sorted({str(case.get("video_id", "")).strip() for case in cases if str(case.get("video_id", "")).strip()})
    seed_files: list[Path] = []
    missing: list[str] = []
    for video_id in unique_ids:
        seed_file = seed_dir / f"{video_id}_events_vector_flat.json"
        if seed_file.exists():
            seed_files.append(seed_file)
        else:
            missing.append(video_id)
    if missing:
        raise FileNotFoundError(f"Missing seed files for video_ids: {missing[:10]}")
    return seed_files


def _prepare_subset_databases(
    *,
    paths: EvalPaths,
    seed_files: list[Path],
    child_collection: str,
    parent_collection: str,
) -> dict[str, Any]:
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    sqlite_result = SQLiteDatabaseBuilder(
        SQLiteBuildConfig(
            db_path=paths.sqlite_path,
            reset_existing=True,
            generate_init_prompt=False,
        )
    ).build(seed_files=seed_files)
    chroma_result = ChromaIndexBuilder(
        ChromaBuildConfig(
            chroma_path=paths.chroma_path,
            child_collection=child_collection,
            parent_collection=parent_collection,
            reset_existing=True,
        )
    ).build(seed_files=seed_files)
    return {
        "sqlite": sqlite_result,
        "chroma": chroma_result,
    }


def _load_graph_with_runtime_env(
    *,
    sqlite_path: Path,
    chroma_path: Path,
    child_collection: str,
    parent_collection: str,
):
    load_env(ROOT_DIR)
    os.environ["AGENT_SQLITE_DB_PATH"] = str(sqlite_path)
    os.environ["AGENT_CHROMA_PATH"] = str(chroma_path)
    os.environ["AGENT_CHROMA_COLLECTION"] = child_collection
    os.environ["AGENT_CHROMA_CHILD_COLLECTION"] = child_collection
    os.environ["AGENT_CHROMA_PARENT_COLLECTION"] = parent_collection
    if "graph" in sys.modules:
        graph_module = importlib.reload(sys.modules["graph"])
    else:
        graph_module = importlib.import_module("graph")
    return graph_module.create_graph()


def _build_ragas_runtime(args: argparse.Namespace) -> tuple[Any, Any, dict[str, Any]]:
    load_env(ROOT_DIR)
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = args.ragas_openai_base_url.strip() or os.getenv("RAGAS_OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY for RAGAS evaluation")
    openai_async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    ragas_llm = llm_factory(
        args.ragas_model,
        provider="openai",
        client=openai_async_client,
        temperature=0,
    )
    ragas_embeddings = embedding_factory(
        provider="openai",
        model=args.ragas_embedding_model,
        client=openai_async_client,
        **({"dimensions": args.ragas_embedding_dimensions} if args.ragas_embedding_dimensions > 0 else {}),
    )
    runtime_profile = {
        "ragas_model": args.ragas_model,
        "ragas_api_provider": "OpenAI",
        "ragas_api_base_url": base_url,
        "ragas_embedding_model": args.ragas_embedding_model,
        "ragas_embedding_dimensions": args.ragas_embedding_dimensions if args.ragas_embedding_dimensions > 0 else None,
    }
    return ragas_llm, ragas_embeddings, runtime_profile


async def _score_case_with_ragas(
    *,
    question: str,
    response: str,
    reference: str,
    contexts: list[str],
    ragas_llm: Any,
    ragas_embeddings: OpenAICompatibleRagasEmbedding,
    answer_relevancy_strictness: int,
) -> dict[str, Any]:
    retrieval_scores: dict[str, Any] = {}
    generation_scores: dict[str, Any] = {}
    metric_errors: dict[str, str] = {}

    async def _run_metric(metric_name: str, coro) -> float | None:
        try:
            result = await coro
            return round(float(result.value), 4)
        except Exception as exc:
            metric_errors[metric_name] = str(exc)
            return None

    if contexts and reference:
        context_precision = ContextPrecisionWithReference(llm=ragas_llm)
        context_recall = ContextRecall(llm=ragas_llm)
        retrieval_values = await asyncio.gather(
            _run_metric(
                "context_precision",
                context_precision.ascore(user_input=question, reference=reference, retrieved_contexts=contexts),
            ),
            _run_metric(
                "context_recall",
                context_recall.ascore(user_input=question, retrieved_contexts=contexts, reference=reference),
            ),
        )
        retrieval_scores["context_precision"] = retrieval_values[0]
        retrieval_scores["context_recall"] = retrieval_values[1]
    else:
        retrieval_scores["context_precision"] = None
        retrieval_scores["context_recall"] = None

    if response:
        answer_relevancy = AnswerRelevancy(
            llm=ragas_llm,
            embeddings=ragas_embeddings,
            strictness=answer_relevancy_strictness,
        )
        factual_correctness = FactualCorrectness(llm=ragas_llm, mode="precision")
        if contexts:
            faithfulness = Faithfulness(llm=ragas_llm)
            generation_values = await asyncio.gather(
                _run_metric(
                    "answer_relevancy",
                    answer_relevancy.ascore(user_input=question, response=response),
                ),
                _run_metric(
                    "factual_correctness",
                    factual_correctness.ascore(response=response, reference=reference),
                ),
                _run_metric(
                    "faithfulness",
                    faithfulness.ascore(user_input=question, response=response, retrieved_contexts=contexts),
                ),
            )
            generation_scores["answer_relevancy"] = generation_values[0]
            generation_scores["factual_correctness"] = generation_values[1]
            generation_scores["faithfulness"] = generation_values[2]
        else:
            generation_values = await asyncio.gather(
                _run_metric(
                    "answer_relevancy",
                    answer_relevancy.ascore(user_input=question, response=response),
                ),
                _run_metric(
                    "factual_correctness",
                    factual_correctness.ascore(response=response, reference=reference),
                ),
            )
            generation_scores["answer_relevancy"] = generation_values[0]
            generation_scores["factual_correctness"] = generation_values[1]
            generation_scores["faithfulness"] = None
    else:
        generation_scores["answer_relevancy"] = None
        generation_scores["factual_correctness"] = None
        generation_scores["faithfulness"] = None

    e2e_score = _mean(
        [
            retrieval_scores.get("context_precision"),
            retrieval_scores.get("context_recall"),
            generation_scores.get("answer_relevancy"),
            generation_scores.get("factual_correctness"),
            generation_scores.get("faithfulness"),
        ]
    )

    return {
        "retrieval": retrieval_scores,
        "generation": generation_scores,
        "end_to_end": {
            "ragas_e2e_score": e2e_score,
        },
        "metric_errors": metric_errors,
    }


def _run_case(graph: Any, case: dict[str, Any], idx: int, top_k: int) -> dict[str, Any]:
    question = str(case.get("question", "")).strip()
    config = {"configurable": {"thread_id": f"ragas-eval-{idx}", "user_id": "ragas-eval"}}
    last_chunk: dict[str, Any] = {}
    node_trace: list[str] = []
    error = None
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
    rows = _select_final_rows(last_chunk)
    contexts = []
    for row in rows[:top_k]:
        text = _row_context_text(row)
        if text and text not in contexts:
            contexts.append(text)
    top_video_ids = [str(row.get("video_id", "")).strip() for row in rows[:top_k] if str(row.get("video_id", "")).strip()]
    response = _strip_sources(last_chunk.get("final_answer"))
    return {
        "case_id": case.get("case_id"),
        "source_sheet": case.get("source_sheet"),
        "video_id": case.get("video_id"),
        "question": question,
        "reference_answer": case.get("reference_answer"),
        "expected_answer_label": case.get("expected_answer_label"),
        "elapsed_ms": elapsed_ms,
        "route_mode": ((last_chunk.get("tool_choice") or {}).get("mode") if isinstance(last_chunk.get("tool_choice"), dict) else None),
        "error": error,
        "tool_error": last_chunk.get("tool_error"),
        "node_trace": node_trace,
        "response": response,
        "retrieved_contexts": contexts,
        "top_video_ids": top_video_ids,
        "top_hit": str(case.get("video_id", "")).strip() in top_video_ids,
        "raw_summary_result": last_chunk.get("summary_result") if isinstance(last_chunk.get("summary_result"), dict) else {},
    }


def _build_summary(case_results: list[dict[str, Any]], dataset_report: dict[str, Any], bootstrap_result: dict[str, Any] | None) -> dict[str, Any]:
    retrieval_cases = [item["ragas"]["retrieval"] for item in case_results]
    generation_cases = [item["ragas"]["generation"] for item in case_results]
    e2e_cases = [item["ragas"]["end_to_end"] for item in case_results]
    return {
        "dataset": dataset_report,
        "bootstrap": bootstrap_result,
        "case_count": len(case_results),
        "success_count": sum(1 for item in case_results if not item.get("error")),
        "top_hit_rate": round(sum(1 for item in case_results if item.get("top_hit")) / max(len(case_results), 1), 4),
        "avg_latency_ms": round(sum(float(item.get("elapsed_ms", 0.0)) for item in case_results) / max(len(case_results), 1), 2),
        "retrieval_summary": {
            "context_precision_avg": _mean([item.get("context_precision") for item in retrieval_cases]),
            "context_recall_avg": _mean([item.get("context_recall") for item in retrieval_cases]),
        },
        "generation_summary": {
            "faithfulness_avg": _mean([item.get("faithfulness") for item in generation_cases]),
            "answer_relevancy_avg": _mean([item.get("answer_relevancy") for item in generation_cases]),
            "factual_correctness_avg": _mean([item.get("factual_correctness") for item in generation_cases]),
        },
        "end_to_end_summary": {
            "ragas_e2e_score_avg": _mean([item.get("ragas_e2e_score") for item in e2e_cases]),
        },
        "error_summary": {
            "ragas_metric_error_cases": sum(1 for item in case_results if (item.get("ragas") or {}).get("metric_errors")),
            "graph_error_cases": sum(1 for item in case_results if item.get("error")),
        },
    }


def _build_markdown(summary: dict[str, Any], case_results: list[dict[str, Any]]) -> str:
    lines = [
        "# RAGAS Eval Report",
        "",
        "## Summary",
        f"- Case count: `{summary['case_count']}`",
        f"- Success count: `{summary['success_count']}`",
        f"- Top hit rate: `{summary['top_hit_rate']}`",
        f"- Avg latency ms: `{summary['avg_latency_ms']}`",
        "",
        "## Retrieval",
        f"- Context precision avg: `{summary['retrieval_summary']['context_precision_avg']}`",
        f"- Context recall avg: `{summary['retrieval_summary']['context_recall_avg']}`",
        "",
        "## Generation",
        f"- Faithfulness avg: `{summary['generation_summary']['faithfulness_avg']}`",
        f"- Answer relevancy avg: `{summary['generation_summary']['answer_relevancy_avg']}`",
        f"- Factual correctness avg: `{summary['generation_summary']['factual_correctness_avg']}`",
        "",
        "## End To End",
        f"- RAGAS e2e avg: `{summary['end_to_end_summary']['ragas_e2e_score_avg']}`",
        "",
        "## Cases",
    ]
    for case in case_results:
        lines.extend(
            [
                f"### {case['case_id']}",
                f"- Sheet: `{case['source_sheet']}`",
                f"- Video: `{case['video_id']}`",
                f"- Question: {case['question']}",
                f"- Route mode: `{case['route_mode']}`",
                f"- Top hit: `{case['top_hit']}`",
                f"- Retrieval: `{json.dumps(case['ragas']['retrieval'], ensure_ascii=False)}`",
                f"- Generation: `{json.dumps(case['ragas']['generation'], ensure_ascii=False)}`",
                f"- End-to-end: `{json.dumps(case['ragas']['end_to_end'], ensure_ascii=False)}`",
                f"- Metric errors: `{json.dumps(case['ragas'].get('metric_errors', {}), ensure_ascii=False)}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation for Part1/Part4 agent cases")
    parser.add_argument("--xlsx-path", type=str, default=str(DEFAULT_XLSX_PATH), help="Source xlsx path")
    parser.add_argument("--seed-dir", type=str, default=str(DEFAULT_SEED_DIR), help="events_vector_flat seed directory")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--include-sheets", nargs="*", default=list(DEFAULT_INCLUDE_SHEETS), help="Sheets to include, default Part1 Part4")
    parser.add_argument("--limit", type=int, default=0, help="Limit case count for smoke test")
    parser.add_argument("--top-k", type=int, default=5, help="How many retrieved rows to evaluate")
    parser.add_argument("--prepare-subset-db", action="store_true", help="Build subset sqlite/chroma from selected video ids")
    parser.add_argument("--sqlite-path", type=str, default="", help="Use an existing sqlite db path")
    parser.add_argument("--chroma-path", type=str, default="", help="Use an existing chroma path")
    parser.add_argument("--child-collection", type=str, default="ucfcrime_eval_child", help="Chroma child collection name")
    parser.add_argument("--parent-collection", type=str, default="ucfcrime_eval_parent", help="Chroma parent collection name")
    parser.add_argument("--ragas-model", type=str, default=DEFAULT_RAGAS_MODEL, help="RAGAS evaluation LLM model")
    parser.add_argument("--ragas-openai-base-url", type=str, default="", help="Optional base url for RAGAS OpenAI client")
    parser.add_argument("--ragas-embedding-model", type=str, default=DEFAULT_RAGAS_EMBEDDING_MODEL, help="Embedding model used by RAGAS")
    parser.add_argument("--ragas-embedding-dimensions", type=int, default=0, help="Optional embedding dimensions, 0 means provider default")
    parser.add_argument("--ragas-concurrency", type=int, default=3, help="Parallel RAGAS scoring concurrency")
    parser.add_argument("--ragas-max-contexts", type=int, default=3, help="Max contexts passed into RAGAS")
    parser.add_argument("--ragas-max-context-chars", type=int, default=700, help="Max chars per context for RAGAS")
    parser.add_argument("--ragas-max-total-context-chars", type=int, default=1800, help="Max total context chars for RAGAS")
    parser.add_argument("--ragas-max-response-chars", type=int, default=900, help="Max response chars for RAGAS")
    parser.add_argument("--ragas-max-reference-chars", type=int, default=700, help="Max reference chars for RAGAS")
    parser.add_argument("--answer-relevancy-strictness", type=int, default=2, help="Question generation count for answer relevancy")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = _default_paths(output_dir)
    include_sheets = [str(item) for item in args.include_sheets if str(item).strip()]

    cases, dataset_report = _load_filtered_cases(
        xlsx_path=Path(args.xlsx_path).expanduser().resolve(),
        dataset_dir=paths.dataset_dir,
        include_sheets=include_sheets,
    )
    if args.limit and args.limit > 0:
        cases = cases[: args.limit]
    if not cases:
        raise RuntimeError("No evaluation cases selected")

    bootstrap_result = None
    sqlite_path = Path(args.sqlite_path).expanduser().resolve() if args.sqlite_path else paths.sqlite_path
    chroma_path = Path(args.chroma_path).expanduser().resolve() if args.chroma_path else paths.chroma_path

    if args.prepare_subset_db:
        seed_files = _resolve_seed_files(Path(args.seed_dir).expanduser().resolve(), cases)
        bootstrap_result = _prepare_subset_databases(
            paths=paths,
            seed_files=seed_files,
            child_collection=args.child_collection,
            parent_collection=args.parent_collection,
        )

    wall_t0 = time.perf_counter()
    graph = _load_graph_with_runtime_env(
        sqlite_path=sqlite_path,
        chroma_path=chroma_path,
        child_collection=args.child_collection,
        parent_collection=args.parent_collection,
    )
    ragas_llm, ragas_embeddings, ragas_runtime_profile = _build_ragas_runtime(args)

    case_results: list[dict[str, Any]] = []
    graph_total_ms = 0.0
    for idx, case in enumerate(cases, start=1):
        print(f"Running eval case {idx}/{len(cases)}: {case['case_id']} - {case['question']}")
        result = _run_case(graph, case, idx, args.top_k)
        graph_total_ms += float(result.get("elapsed_ms", 0.0))
        case_results.append(result)

    async def _score_all_cases() -> None:
        semaphore = asyncio.Semaphore(max(1, int(args.ragas_concurrency)))

        async def _score_one(case_result: dict[str, Any]) -> None:
            question = _truncate_text(case_result.get("question"), 500)
            response = _truncate_text(case_result.get("response"), int(args.ragas_max_response_chars))
            reference = _truncate_text(case_result.get("reference_answer"), int(args.ragas_max_reference_chars))
            contexts = _compact_contexts(
                case_result.get("retrieved_contexts") or [],
                max_contexts=int(args.ragas_max_contexts),
                max_chars_per_context=int(args.ragas_max_context_chars),
                max_total_chars=int(args.ragas_max_total_context_chars),
            )
            score_t0 = time.perf_counter()
            async with semaphore:
                ragas_result = await _score_case_with_ragas(
                    question=question,
                    response=response,
                    reference=reference,
                    contexts=contexts,
                    ragas_llm=ragas_llm,
                    ragas_embeddings=ragas_embeddings,
                    answer_relevancy_strictness=max(1, int(args.answer_relevancy_strictness)),
                )
            case_result["ragas_elapsed_ms"] = round((time.perf_counter() - score_t0) * 1000, 2)
            case_result["ragas_input_profile"] = {
                "context_count": len(contexts),
                "context_total_chars": sum(len(item) for item in contexts),
                "response_chars": len(response),
                "reference_chars": len(reference),
                "question_chars": len(question),
            }
            case_result["ragas"] = ragas_result
            case_result["retrieved_contexts_for_ragas"] = contexts

        await asyncio.gather(*[_score_one(item) for item in case_results])

    ragas_t0 = time.perf_counter()
    asyncio.run(_score_all_cases())
    ragas_total_ms = round((time.perf_counter() - ragas_t0) * 1000, 2)

    retrieval_report = {"cases": [{k: v for k, v in item.items() if k in {"case_id", "video_id", "question", "retrieved_contexts", "top_video_ids", "top_hit", "ragas"}} for item in case_results]}
    generation_report = {"cases": [{k: v for k, v in item.items() if k in {"case_id", "video_id", "question", "response", "reference_answer", "ragas"}} for item in case_results]}
    e2e_report = {"cases": case_results}
    summary = _build_summary(case_results, dataset_report, bootstrap_result)
    summary["runtime_profile"] = {
        "ragas_runtime": ragas_runtime_profile,
        "eval_config": {
            "top_k": args.top_k,
            "ragas_concurrency": args.ragas_concurrency,
            "ragas_max_contexts": args.ragas_max_contexts,
            "ragas_max_context_chars": args.ragas_max_context_chars,
            "ragas_max_total_context_chars": args.ragas_max_total_context_chars,
            "ragas_max_response_chars": args.ragas_max_response_chars,
            "ragas_max_reference_chars": args.ragas_max_reference_chars,
            "answer_relevancy_strictness": args.answer_relevancy_strictness,
        },
        "timing": {
            "graph_total_ms": round(graph_total_ms, 2),
            "graph_avg_ms_per_case": round(graph_total_ms / max(len(case_results), 1), 2),
            "ragas_total_ms": ragas_total_ms,
            "ragas_avg_ms_per_case": round(ragas_total_ms / max(len(case_results), 1), 2),
            "wall_total_ms": round((time.perf_counter() - wall_t0) * 1000, 2),
        },
    }

    _write_json(paths.retrieval_report_json, retrieval_report)
    _write_json(paths.generation_report_json, generation_report)
    _write_json(paths.e2e_report_json, e2e_report)
    _write_json(paths.summary_report_json, summary)
    paths.summary_report_md.write_text(_build_markdown(summary, case_results), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
