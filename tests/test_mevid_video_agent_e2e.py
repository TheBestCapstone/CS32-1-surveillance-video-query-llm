"""
MEVID video -> agent end-to-end smoke/evaluation runner.

This script stitches together the existing project pieces:

1. MEVID multi-camera pipeline cache
2. vector-flat seed generation for agent indexing
3. temporary SQLite + Chroma build
4. LangGraph agent query run
5. compact JSON/Markdown report

Default mode is cache-first and safe:
    python tests/test_mevid_video_agent_e2e.py --slot 13-50 --limit 8

To generate missing pipeline cache from videos, opt in explicitly:
    python tests/test_mevid_video_agent_e2e.py --slot 13-50 --run-pipeline --reid-device cuda
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
AGENT_TEST_DIR = AGENT_DIR / "test"

for p in (ROOT, AGENT_DIR, AGENT_TEST_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scripts.generate_mevid_vector_flat import SLOT_CAMERAS  # noqa: E402


DEFAULT_XLSX = ROOT / "agent" / "test" / "data" / "agent_test_mevid.xlsx"
DEFAULT_SEED_DIR = ROOT / "agent" / "test" / "data" / "events_vector_flat"
DEFAULT_VIDEO_DIR = ROOT / "_data" / "mevid_slots"
DEFAULT_OUTPUT_ROOT = ROOT / "results" / "mevid_agent_e2e"


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _check_environment(run_pipeline: bool) -> dict[str, Any]:
    try:
        from agent.core.runtime import load_env

        load_env(ROOT)
    except Exception as exc:
        # Keep the check readable even when the active Python environment is wrong.
        env_file = ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        runtime_import_error = str(exc)
    else:
        runtime_import_error = ""
    imports: dict[str, str] = {}
    for mod in ["openpyxl", "chromadb", "langgraph", "langchain_openai"]:
        try:
            importlib.import_module(mod)
            imports[mod] = "ok"
        except Exception as exc:
            imports[mod] = f"missing/error: {exc}"

    if run_pipeline:
        for mod in ["cv2", "torch", "ultralytics", "torchreid"]:
            try:
                importlib.import_module(mod)
                imports[mod] = "ok"
            except Exception as exc:
                imports[mod] = f"missing/error: {exc}"

    env = {
        "DASHSCOPE_API_KEY": bool(os.getenv("DASHSCOPE_API_KEY")),
        "DASHSCOPE_URL": bool(os.getenv("DASHSCOPE_URL")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "OPENAI_BASE_URL": bool(os.getenv("OPENAI_BASE_URL")),
        "AGENT_EMBEDDING_PROVIDER": os.getenv("AGENT_EMBEDDING_PROVIDER", ""),
        "AGENT_LLAMAINDEX_LLM_PROVIDER": os.getenv("AGENT_LLAMAINDEX_LLM_PROVIDER", ""),
    }
    return {"imports": imports, "env": env, "runtime_import_error": runtime_import_error}


def _assert_environment_ready(env_report: dict[str, Any], *, run_pipeline: bool, skip_agent: bool) -> None:
    required = ["openpyxl", "chromadb"]
    if not skip_agent:
        required.extend(["langgraph", "langchain_openai"])
    if run_pipeline:
        required.extend(["cv2", "torch", "ultralytics", "torchreid"])

    imports = env_report.get("imports", {})
    missing = [name for name in required if str(imports.get(name, "")).lower() != "ok"]
    env = env_report.get("env", {})
    key_missing: list[str] = []
    if not env.get("DASHSCOPE_API_KEY") and not env.get("OPENAI_API_KEY"):
        key_missing.append("DASHSCOPE_API_KEY or OPENAI_API_KEY")
    if not skip_agent and (not env.get("DASHSCOPE_API_KEY") or not env.get("DASHSCOPE_URL")):
        key_missing.append("DASHSCOPE_API_KEY and DASHSCOPE_URL for the agent LLM")

    if missing or key_missing:
        details = {
            "missing_imports": missing,
            "missing_env": key_missing,
            "imports": imports,
            "env": env,
            "runtime_import_error": env_report.get("runtime_import_error", ""),
        }
        raise RuntimeError(
            "Environment is not ready for MEVID video+agent e2e. "
            "Use the capstone conda environment and install missing packages if needed.\n"
            + json.dumps(details, ensure_ascii=False, indent=2)
        )


def _slot_video_ids(slot: str) -> set[str]:
    if slot not in SLOT_CAMERAS:
        raise ValueError(f"Unknown slot {slot!r}. Available: {', '.join(SLOT_CAMERAS)}")
    return set(SLOT_CAMERAS[slot].values())


def _infer_category(question: str, expected_label: str = "") -> str:
    q = question.lower()
    label = expected_label.lower()
    if label == "no":
        return "negative"
    if any(token in q for token in ["then appear", "also appear", "same person", "again in camera", "another camera"]):
        return "cross_camera"
    if any(token in q for token in ["exit", "enter", "walk", "move", "appear in camera", "leave"]):
        return "event"
    if any(token in q for token in [
        "wearing", "visible", "with ", "hoodie", "jacket", "coat", "shirt",
        "hat", "bag", "backpack", "color", "colour", "appearance",
    ]):
        return "appearance"
    return "unknown"


def _parse_yes_no(answer: Any) -> str:
    text = str(answer or "").strip().lower()
    text = re.sub(r"^[\s`*_>-]+", "", text)
    if text.startswith("yes") or text.startswith("是") or text.startswith("有"):
        return "yes"
    if text.startswith("no") or text.startswith("否") or text.startswith("没有") or text.startswith("无"):
        return "no"
    return "unknown"


def _stratified_sample(cases: list[dict[str, Any]], limit: int, seed: int) -> list[dict[str, Any]]:
    if limit <= 0 or len(cases) <= limit:
        return cases
    rng = random.Random(seed)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for case in cases:
        key = (str(case.get("_category") or "unknown"), str(case.get("expected_answer_label") or "unknown"))
        groups.setdefault(key, []).append(case)

    selected: list[dict[str, Any]] = []
    total = len(cases)
    for _key, items in sorted(groups.items()):
        k = max(1, round(limit * len(items) / total))
        selected.extend(rng.sample(items, min(k, len(items))))

    if len(selected) > limit:
        rng.shuffle(selected)
        selected = selected[:limit]
    elif len(selected) < limit:
        used = {id(c) for c in selected}
        remainder = [c for c in cases if id(c) not in used]
        rng.shuffle(remainder)
        selected.extend(remainder[: limit - len(selected)])

    selected.sort(key=lambda c: str(c.get("case_id") or ""))
    return selected


def _balanced_category_sample(cases: list[dict[str, Any]], limit: int, seed: int) -> list[dict[str, Any]]:
    if limit <= 0 or len(cases) <= limit:
        return cases
    rng = random.Random(seed)
    preferred = ["appearance", "cross_camera", "event", "negative", "unknown"]
    by_category: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_category.setdefault(str(case.get("_category") or "unknown"), []).append(case)
    categories = [cat for cat in preferred if by_category.get(cat)]
    categories.extend(sorted(cat for cat in by_category if cat not in categories))
    if not categories:
        return []

    base = max(1, limit // len(categories))
    selected: list[dict[str, Any]] = []
    for cat in categories:
        items = by_category[cat]
        selected.extend(rng.sample(items, min(base, len(items))))

    if len(selected) < limit:
        used = {id(c) for c in selected}
        remainder = [c for c in cases if id(c) not in used]
        rng.shuffle(remainder)
        selected.extend(remainder[: limit - len(selected)])
    elif len(selected) > limit:
        rng.shuffle(selected)
        selected = selected[:limit]

    selected.sort(key=lambda c: str(c.get("case_id") or ""))
    return selected


def _import_cases(xlsx_path: Path, output_dir: Path, include_sheets: list[str]) -> list[dict[str, Any]]:
    from agent_test_importer import AgentTestDatasetImporter, AgentTestImportConfig

    dataset_dir = output_dir / "dataset"
    report = AgentTestDatasetImporter(
        AgentTestImportConfig(
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
    ).build()
    cases_path = dataset_dir / "agent_test_normalized.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    print(f"[mevid-agent] Imported {len(cases)} cases from {xlsx_path.name}: {report}")
    return cases


def _select_cases(
    cases: list[dict[str, Any]],
    slot: str,
    categories: set[str],
    limit: int,
    sample_mode: str,
    seed: int,
) -> list[dict[str, Any]]:
    slot_ids = _slot_video_ids(slot)
    eligible: list[dict[str, Any]] = []
    for case in cases:
        video_id = str(case.get("video_id") or "").strip()
        if video_id not in slot_ids:
            continue
        metadata = case.get("metadata") if isinstance(case.get("metadata"), dict) else {}
        raw_row = metadata.get("raw_row") if isinstance(metadata.get("raw_row"), list) else []
        category = str(metadata.get("category") or (raw_row[7] if len(raw_row) > 7 else "") or "").strip()
        if not category:
            category = _infer_category(
                str(case.get("question") or ""),
                str(case.get("expected_answer_label") or ""),
            )
        case["_category"] = category or "unknown"
        if categories and case["_category"] not in categories:
            continue
        eligible.append(case)
    if sample_mode == "stratified":
        return _stratified_sample(eligible, limit=limit, seed=seed)
    if sample_mode == "balanced":
        return _balanced_category_sample(eligible, limit=limit, seed=seed)
    if limit > 0:
        return eligible[:limit]
    return eligible


def _ensure_vector_seeds(
    *,
    slot: str,
    seed_dir: Path,
    video_dir: Path,
    run_pipeline: bool,
    reid_device: str,
    force_seed: bool,
) -> None:
    missing = [
        stem
        for stem in sorted(_slot_video_ids(slot))
        if not (seed_dir / f"{stem}_events_vector_flat.json").exists()
    ]
    if not missing and not force_seed:
        print(f"[mevid-agent] Vector seeds already exist for slot {slot}: {seed_dir}")
        return

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "generate_mevid_vector_flat.py"),
        "--slot",
        slot,
        "--out-dir",
        str(seed_dir),
        "--video-dir",
        str(video_dir.relative_to(ROOT) if video_dir.is_relative_to(ROOT) else video_dir),
    ]
    if run_pipeline:
        cmd.extend(["--run-pipeline", "--reid-device", reid_device])
    if force_seed:
        cmd.append("--force")

    print("[mevid-agent] Generating vector-flat seeds ...")
    print("[mevid-agent] " + " ".join(cmd))
    child_env = os.environ.copy()
    child_env.setdefault("PYTHONIOENCODING", "utf-8")
    subprocess.run(cmd, cwd=str(ROOT), check=True, env=child_env)


def _resolve_seed_files(seed_dir: Path, cases: list[dict[str, Any]]) -> list[Path]:
    video_ids = sorted({str(c.get("video_id") or "").strip() for c in cases if c.get("video_id")})
    missing: list[str] = []
    seed_files: list[Path] = []
    for video_id in video_ids:
        seed_file = seed_dir / f"{video_id}_events_vector_flat.json"
        if seed_file.exists():
            seed_files.append(seed_file)
        else:
            missing.append(video_id)
    if missing:
        raise FileNotFoundError(
            "Missing vector-flat seed files. Run with --run-pipeline if pipeline cache is missing. "
            f"Missing examples: {missing[:8]}"
        )
    return seed_files


def _prepare_databases(
    *,
    output_dir: Path,
    seed_files: list[Path],
    namespace: str,
) -> dict[str, Any]:
    from agent.core.runtime import load_env
    from agent.db.chroma_builder import ChromaBuildConfig, ChromaIndexBuilder
    from agent.db.sqlite_builder import SQLiteBuildConfig, SQLiteDatabaseBuilder
    from langchain_openai import ChatOpenAI

    load_env(ROOT)
    discriminator_llm = ChatOpenAI(
        model_name=os.getenv("MEVID_VIDEO_DISCRIMINATOR_MODEL", "qwen3.5-plus"),
        temperature=0.0,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_URL"),
    )
    runtime_dir = output_dir / "runtime"
    sqlite_path = runtime_dir / "mevid_agent_e2e.sqlite"
    chroma_path = runtime_dir / "mevid_agent_e2e_chroma"
    child_collection = f"{namespace}_tracks"
    parent_collection = f"{namespace}_tracks_parent"
    event_collection = f"{namespace}_events"
    video_collection = f"{namespace}_video"

    sqlite_result = SQLiteDatabaseBuilder(
        SQLiteBuildConfig(
            db_path=sqlite_path,
            reset_existing=True,
            generate_init_prompt=False,
        )
    ).build(seed_files=seed_files)

    chroma_result = ChromaIndexBuilder(
        ChromaBuildConfig(
            chroma_path=chroma_path,
            child_collection=child_collection,
            parent_collection=parent_collection,
            event_collection=event_collection,
            video_collection=video_collection,
            reset_existing=True,
        )
    ).build(seed_files=seed_files, llm=discriminator_llm)

    return {
        "sqlite": sqlite_result,
        "chroma": chroma_result,
        "sqlite_path": str(sqlite_path),
        "chroma_path": str(chroma_path),
        "child_collection": child_collection,
        "parent_collection": parent_collection,
        "event_collection": event_collection,
        "video_collection": video_collection,
    }


def _load_agent_graph(db_info: dict[str, Any]):
    from agent.core.runtime import load_env

    load_env(ROOT)
    os.environ["AGENT_SQLITE_DB_PATH"] = str(db_info["sqlite_path"])
    os.environ["AGENT_CHROMA_PATH"] = str(db_info["chroma_path"])
    os.environ["AGENT_CHROMA_COLLECTION"] = str(db_info["child_collection"])
    os.environ["AGENT_CHROMA_CHILD_COLLECTION"] = str(db_info["child_collection"])
    os.environ["AGENT_CHROMA_PARENT_COLLECTION"] = str(db_info["parent_collection"])
    os.environ["AGENT_CHROMA_EVENT_COLLECTION"] = str(db_info["event_collection"])
    os.environ["AGENT_CHROMA_VIDEO_COLLECTION"] = str(db_info["video_collection"])
    os.environ.setdefault("AGENT_CHROMA_RETRIEVAL_LEVEL", "child")

    if "graph" in sys.modules:
        graph_module = importlib.reload(sys.modules["graph"])
    else:
        graph_module = importlib.import_module("graph")
    return graph_module.create_graph()


def _final_rows(state: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("rerank_result", "merged_result", "hybrid_result", "sql_result"):
        rows = state.get(key)
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    return []


def _run_agent_cases(graph: Any, cases: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    from langchain_core.messages import HumanMessage

    results: list[dict[str, Any]] = []
    for idx, case in enumerate(cases, start=1):
        question = str(case.get("question") or "").strip()
        print(f"[mevid-agent] Case {idx}/{len(cases)} {case.get('case_id')}: {question}")
        config = {"configurable": {"thread_id": f"mevid-agent-e2e-{idx}", "user_id": "mevid-agent-e2e"}}
        last_state: dict[str, Any] = {}
        node_trace: list[str] = []
        error = None
        t0 = time.perf_counter()
        try:
            for chunk in graph.stream({"messages": [HumanMessage(content=question)]}, config, stream_mode="values"):
                last_state = chunk
                current_node = chunk.get("current_node")
                if current_node and (not node_trace or node_trace[-1] != current_node):
                    node_trace.append(str(current_node))
        except Exception as exc:
            error = str(exc)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        rows = _final_rows(last_state)
        top_rows = rows[:top_k]
        top_video_ids = [str(r.get("video_id") or "").strip() for r in top_rows if r.get("video_id")]
        expected_video_id = str(case.get("video_id") or "").strip()
        expected_label = str(case.get("expected_answer_label") or "").strip().lower()
        predicted_label = _parse_yes_no(last_state.get("final_answer"))
        answer_correct = expected_label in {"yes", "no"} and predicted_label == expected_label
        result = {
            "case_id": case.get("case_id"),
            "category": case.get("_category"),
            "video_id": expected_video_id,
            "question": question,
            "expected_answer_label": expected_label,
            "predicted_answer_label": predicted_label,
            "answer_correct": answer_correct,
            "expected_time_raw": case.get("expected_time_raw"),
            "elapsed_ms": elapsed_ms,
            "error": error,
            "node_trace": node_trace,
            "route_mode": ((last_state.get("tool_choice") or {}).get("mode") if isinstance(last_state.get("tool_choice"), dict) else None),
            "answer_type": last_state.get("answer_type"),
            "final_answer": last_state.get("final_answer"),
            "top_video_ids": top_video_ids,
            "top_hit": expected_video_id in top_video_ids,
            "top_rows": [
                {
                    "video_id": r.get("video_id"),
                    "start_time": r.get("start_time"),
                    "end_time": r.get("end_time"),
                    "event_text": r.get("event_text") or r.get("event_text_en") or r.get("event_summary_en"),
                    "object_type": r.get("object_type"),
                    "object_color": r.get("object_color"),
                    "scene_zone": r.get("scene_zone"),
                    "entity_hint": r.get("entity_hint"),
                }
                for r in top_rows
            ],
        }
        results.append(result)
    return results


def _build_summary(
    *,
    args: argparse.Namespace,
    env_report: dict[str, Any],
    db_info: dict[str, Any] | None,
    selected_cases: list[dict[str, Any]],
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    success = [r for r in case_results if not r.get("error")]
    answer_scored = [r for r in case_results if str(r.get("expected_answer_label") or "") in {"yes", "no"}]
    answer_correct = [r for r in answer_scored if r.get("answer_correct")]
    by_category: dict[str, dict[str, Any]] = {}
    for category in sorted({str(r.get("category") or "unknown") for r in case_results}):
        items = [r for r in case_results if str(r.get("category") or "unknown") == category]
        scored_items = [r for r in items if str(r.get("expected_answer_label") or "") in {"yes", "no"}]
        by_category[category] = {
            "count": len(items),
            "answer_accuracy": round(
                sum(1 for r in scored_items if r.get("answer_correct")) / max(len(scored_items), 1),
                4,
            ),
            "top_hit_rate": round(
                sum(1 for r in items if r.get("top_hit")) / max(len(items), 1),
                4,
            ),
        }
    return {
        "timestamp": _now_stamp(),
        "slot": args.slot,
        "case_count": len(selected_cases),
        "run_count": len(case_results),
        "success_count": len(success),
        "error_count": len(case_results) - len(success),
        "top_hit_rate": round(
            sum(1 for r in case_results if r.get("top_hit")) / max(len(case_results), 1),
            4,
        ),
        "answer_accuracy": round(len(answer_correct) / max(len(answer_scored), 1), 4),
        "answer_correct_count": len(answer_correct),
        "answer_scored_count": len(answer_scored),
        "category_breakdown": by_category,
        "environment": env_report,
        "database": db_info,
        "args": vars(args),
    }


def _write_markdown(path: Path, summary: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    lines = [
        "# MEVID Video + Agent E2E Report",
        "",
        f"- Slot: `{summary['slot']}`",
        f"- Cases: `{summary['run_count']}`",
        f"- Success: `{summary['success_count']}`",
        f"- Errors: `{summary['error_count']}`",
        f"- Top-hit rate: `{summary['top_hit_rate']}`",
        f"- Answer accuracy: `{summary.get('answer_accuracy')}` "
        f"({summary.get('answer_correct_count')}/{summary.get('answer_scored_count')})",
        "",
        "## Category Breakdown",
        "",
    ]
    for category, stats in (summary.get("category_breakdown") or {}).items():
        lines.append(
            f"- `{category}`: count={stats.get('count')}, "
            f"answer_accuracy={stats.get('answer_accuracy')}, "
            f"top_hit_rate={stats.get('top_hit_rate')}"
        )
    lines.extend([
        "",
        "## Cases",
    ])
    for case in cases:
        lines.extend(
            [
                f"### {case.get('case_id')}",
                f"- Category: `{case.get('category')}`",
                f"- Video: `{case.get('video_id')}`",
                f"- Question: {case.get('question')}",
                f"- Error: `{case.get('error')}`",
                f"- Route: `{case.get('route_mode')}`",
                f"- Top hit: `{case.get('top_hit')}`",
                f"- Expected/Predicted: `{case.get('expected_answer_label')}` / "
                f"`{case.get('predicted_answer_label')}` "
                f"(correct={case.get('answer_correct')})",
                f"- Top videos: `{case.get('top_video_ids')}`",
                f"- Answer: {case.get('final_answer')}",
                "",
            ]
        )
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MEVID video-cache + agent end-to-end test")
    parser.add_argument("--slot", default="13-50", choices=sorted(SLOT_CAMERAS), help="MEVID slot to test")
    parser.add_argument("--limit", type=int, default=8, help="Max cases to run; 0 = all selected")
    parser.add_argument("--sample-mode", choices=["balanced", "stratified", "first"], default="balanced",
                        help="Case selection mode. balanced gives each inferred category similar weight")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified sampling")
    parser.add_argument("--top-k", type=int, default=5, help="Top retrieved rows to inspect")
    parser.add_argument("--xlsx-path", default=str(DEFAULT_XLSX), help="MEVID agent test xlsx")
    parser.add_argument("--seed-dir", default=str(DEFAULT_SEED_DIR), help="Directory for *_events_vector_flat.json")
    parser.add_argument("--video-dir", default=str(DEFAULT_VIDEO_DIR), help="MEVID video directory")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Report/output root")
    parser.add_argument("--include-sheets", nargs="*", default=["Part1", "Part4"], help="XLSX sheets to import")
    parser.add_argument("--categories", nargs="*", default=[], help="Optional categories to include")
    parser.add_argument("--run-pipeline", action="store_true", help="Run YOLO+ReID if pipeline cache is missing")
    parser.add_argument("--reid-device", default="cpu", help="cpu | cuda when --run-pipeline is used")
    parser.add_argument("--force-seed", action="store_true", help="Regenerate vector-flat seed files")
    parser.add_argument("--skip-agent", action="store_true", help="Only check env, import cases, generate seeds, build DB")
    parser.add_argument("--namespace", default="", help="Chroma namespace; default mevid_e2e_<timestamp>")
    parser.add_argument(
        "--embedding-provider",
        default="dashscope",
        choices=["dashscope", "openai"],
        help="Embedding provider for Chroma build; MEVID default is dashscope",
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-v3",
        help="Embedding model for Chroma build",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.embedding_provider:
        os.environ["AGENT_EMBEDDING_PROVIDER"] = args.embedding_provider
    if args.embedding_model:
        os.environ["AGENT_EMBEDDING_MODEL"] = args.embedding_model
    stamp = _now_stamp()
    output_dir = Path(args.output_root).expanduser().resolve() / f"{args.slot}_{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = Path(args.xlsx_path).expanduser().resolve()
    seed_dir = Path(args.seed_dir).expanduser().resolve()
    video_dir = Path(args.video_dir).expanduser().resolve()
    namespace = args.namespace.strip() or f"mevid_e2e_{stamp}"

    env_report = _check_environment(run_pipeline=args.run_pipeline)
    _assert_environment_ready(env_report, run_pipeline=args.run_pipeline, skip_agent=args.skip_agent)
    cases = _import_cases(xlsx_path, output_dir, include_sheets=args.include_sheets)
    selected = _select_cases(
        cases,
        slot=args.slot,
        categories=set(args.categories),
        limit=args.limit,
        sample_mode=args.sample_mode,
        seed=args.seed,
    )
    if not selected:
        raise RuntimeError(f"No cases selected for slot={args.slot}, categories={args.categories}")
    print(f"[mevid-agent] Selected {len(selected)} cases for slot {args.slot}")

    _ensure_vector_seeds(
        slot=args.slot,
        seed_dir=seed_dir,
        video_dir=video_dir,
        run_pipeline=args.run_pipeline,
        reid_device=args.reid_device,
        force_seed=args.force_seed,
    )
    seed_files = _resolve_seed_files(seed_dir, selected)
    db_info = _prepare_databases(output_dir=output_dir, seed_files=seed_files, namespace=namespace)

    case_results: list[dict[str, Any]] = []
    if not args.skip_agent:
        graph = _load_agent_graph(db_info)
        case_results = _run_agent_cases(graph, selected, top_k=args.top_k)

    summary = _build_summary(
        args=args,
        env_report=env_report,
        db_info=db_info,
        selected_cases=selected,
        case_results=case_results,
    )
    _write_json(output_dir / "selected_cases.json", selected)
    _write_json(output_dir / "case_results.json", case_results)
    _write_json(output_dir / "summary.json", summary)
    _write_markdown(output_dir / "summary.md", summary, case_results)
    print(f"[mevid-agent] Done. Report: {output_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
