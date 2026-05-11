#!/usr/bin/env python3
"""Aggregate video-ID retrieval metrics from chunked e2e_report.json files (no LLM).

- ``chunk_same_video_precision_at_1_avg``: mean binary score — does the **first** retrieved
  chunk's ``video_id`` match GT? (standard IR **precision@1**; usually the highest of the
  chunk-level precision family.)
- ``chunk_same_video_precision_avg``: matching chunk count / total chunks (all ranks).
- ``id_context_recall_avg``: whether GT ``video_id`` appears in any retrieved chunk id.

Example::

    conda activate capstone
    cd agent/test
    python compute_id_based_retrieval_from_e2e.py \\
        --reports-root generated/old/ragas_eval_p4_chunks
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

AGENT_TEST_DIR = Path(__file__).resolve().parent
ROOT_DIR = AGENT_TEST_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(AGENT_TEST_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_TEST_DIR))

from ragas_eval_runner import (  # noqa: E402
    _normalize_video_id,
    _same_video_chunk_precision,
    _same_video_precision_at_1,
    _video_id_from_context_prefix,
)


def _contexts_for_case(case: dict[str, Any]) -> list[str]:
    raw = case.get("retrieved_contexts_for_ragas") or case.get("retrieved_contexts") or []
    return [str(x) for x in raw if x]


def _id_retrieval_recall_case(contexts: list[str], reference_video_id: str) -> float | None:
    """RAGAS-equivalent ID recall for one GT video id (binary 0/1 per case)."""
    exp = _normalize_video_id(str(reference_video_id or "").strip())
    if not exp:
        return None
    seen: set[str] = set()
    for ctx in contexts:
        raw = _video_id_from_context_prefix(ctx)
        if raw:
            seen.add(_normalize_video_id(raw))
    if not seen:
        return 0.0
    return 1.0 if exp in seen else 0.0


def _mean(nums: list[float]) -> float | None:
    return round(statistics.mean(nums), 4) if nums else None


def run_aggregate(reports_root: Path) -> dict[str, Any]:
    chunk_patterns = ["chunk01", "chunk02", "chunk03", "chunk04", "chunk05"]
    per_chunk: list[dict[str, Any]] = []
    all_p1: list[float] = []
    all_cp: list[float] = []
    all_r: list[float] = []
    missing_vid = 0
    empty_ctx = 0

    for cname in chunk_patterns:
        path = reports_root / cname / "e2e_report.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        cases = data.get("cases") or []
        p1_list: list[float] = []
        cp_list: list[float] = []
        cr_list: list[float] = []
        for case in cases:
            ctx = _contexts_for_case(case)
            vid = str(case.get("video_id") or "").strip()
            if not vid:
                missing_vid += 1
            if not ctx:
                empty_ctx += 1
            if ctx and vid:
                v1 = _same_video_precision_at_1(ctx, vid)
                if v1 is not None:
                    p1_list.append(float(v1))
                    all_p1.append(float(v1))
                p_all = _same_video_chunk_precision(ctx, vid)
                if p_all is not None:
                    cp_list.append(p_all)
                    all_cp.append(p_all)
            r = _id_retrieval_recall_case(ctx, vid) if vid else None
            if r is not None:
                cr_list.append(r)
                all_r.append(r)
        per_chunk.append(
            {
                "chunk": cname,
                "case_count": len(cases),
                "chunk_same_video_precision_at_1_avg": _mean(p1_list),
                "chunk_same_video_precision_avg": _mean(cp_list),
                "id_context_recall_avg": _mean(cr_list),
                "scored_precision_at_1_count": len(p1_list),
                "scored_precision_all_chunks_count": len(cp_list),
                "scored_recall_count": len(cr_list),
            }
        )

    return {
        "reports_root": str(reports_root.resolve()),
        "id_retrieval_summary": {
            "note": (
                "chunk_same_video_precision_at_1_avg = precision@1 (first chunk matches GT video); "
                "chunk_same_video_precision_avg = matching_chunks/total_chunks; "
                "id_context_recall_avg = mean binary(GT video appears in any chunk). No LLM."
            ),
            "chunk_same_video_precision_at_1_avg": _mean(all_p1),
            "chunk_same_video_precision_avg": _mean(all_cp),
            "id_context_recall_avg": _mean(all_r),
            "id_metric_null_cases": {
                "missing_or_empty_reference_video_id": missing_vid,
                "empty_retrieved_contexts": empty_ctx,
            },
            "scored_case_count_precision_at_1": len(all_p1),
            "scored_case_count_precision_all_chunks": len(all_cp),
            "scored_case_count_recall": len(all_r),
        },
        "per_chunk": per_chunk,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reports-root",
        type=Path,
        default=AGENT_TEST_DIR / "generated" / "old" / "ragas_eval_p4_chunks",
        help="Folder containing chunk01/e2e_report.json … chunk05/e2e_report.json",
    )
    args = parser.parse_args()
    root = args.reports_root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    result = run_aggregate(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
