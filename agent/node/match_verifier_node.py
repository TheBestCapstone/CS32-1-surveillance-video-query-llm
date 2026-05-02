"""Existence-grounder node (P1-7).

Only runs when ``state.answer_type == "existence"``. For other question
shapes it is a pass-through so retrieval scores are untouched. The node
inspects the top rerank row and emits a verdict describing whether the
evidence actually supports the query. Downstream ``final_answer_node`` uses
this verdict to return a structured Yes/No response for existence questions.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "around",
    "after",
    "any",
    "before",
    "being",
    "by",
    "can",
    "clip",
    "conducting",
    "did",
    "does",
    "for",
    "from",
    "full",
    "have",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "one",
    "or",
    "other",
    "over",
    "person",
    "there",
    "their",
    "then",
    "to",
    "two",
    "up",
    "video",
    "was",
    "were",
    "while",
    "with",
}

_SCENE_TERMS = {"road", "room", "sofa", "wall", "wheelchair", "conveyor", "parking", "court", "bleachers"}

_FAST_DECISIONS = {"exact", "partial", "mismatch"}


def _select_rows(state: AgentState) -> list[dict[str, Any]]:
    if "rerank_result" in state:
        return list(state.get("rerank_result") or [])
    if "hybrid_result" in state:
        return list(state.get("hybrid_result") or [])
    return list(state.get("sql_result") or [])


def _pick_primary_row(row: dict[str, Any]) -> dict[str, Any]:
    child_rows = row.get("_child_rows") if isinstance(row.get("_child_rows"), list) else []
    if not child_rows:
        return row

    def _sort_key(item: dict[str, Any]) -> tuple[float, float]:
        distance = item.get("_distance")
        hybrid = item.get("_hybrid_score")
        safe_distance = float(distance) if isinstance(distance, (int, float)) else 999999.0
        safe_hybrid = -float(hybrid) if isinstance(hybrid, (int, float)) else 0.0
        return (safe_distance, safe_hybrid)

    ranked_children = sorted(
        [item for item in child_rows if isinstance(item, dict)],
        key=_sort_key,
    )
    return ranked_children[0] if ranked_children else row


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _query_terms(query: str) -> set[str]:
    terms: set[str] = set()
    for token in _tokenize(query):
        if len(token) < 3 or token in _STOPWORDS:
            continue
        terms.add(token)
    return terms


def _evidence_text(row: dict[str, Any], primary: dict[str, Any]) -> str:
    parts = [
        row.get("event_summary_en"),
        row.get("event_text_en"),
        primary.get("event_summary_en"),
        primary.get("event_text_en"),
        row.get("object_type"),
        row.get("object_color_en"),
        row.get("scene_zone_en"),
    ]
    return " ".join(str(item or "") for item in parts if item).lower()


def _heuristic_verdict(query: str, row: dict[str, Any], primary: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_text(row, primary)
    query_terms = _query_terms(query)
    if not query_terms:
        return {"decision": "partial", "confidence": 0.5, "reason": "empty_query_terms", "mode": "heuristic"}

    matched = sorted(term for term in query_terms if term in evidence)
    scene_terms = [term for term in query_terms if term in _SCENE_TERMS]
    scene_conflict = bool(scene_terms) and any(term not in evidence for term in scene_terms)
    coverage = len(matched) / max(len(query_terms), 1)

    if scene_conflict:
        return {"decision": "mismatch", "confidence": 0.85, "reason": "scene_conflict", "mode": "heuristic"}
    if coverage >= 0.58:
        return {
            "decision": "exact",
            "confidence": min(0.95, 0.55 + coverage / 2),
            "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
            "mode": "heuristic",
        }
    if coverage >= 0.34:
        return {
            "decision": "partial",
            "confidence": min(0.8, 0.35 + coverage / 2),
            "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
            "mode": "heuristic",
        }
    return {
        "decision": "mismatch",
        "confidence": max(0.55, 1 - coverage),
        "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
        "mode": "heuristic",
    }


def _parse_json_object(text: str) -> dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None


def _llm_verdict(
    llm: Any,
    query: str,
    row: dict[str, Any],
    primary: dict[str, Any],
    config: RunnableConfig,
) -> dict[str, Any] | None:
    if llm is None or os.getenv("AGENT_MATCH_VERIFIER_USE_LLM", "1").strip() in {"0", "false", "False"}:
        return None
    prompt = (
        "Decide whether the retrieved evidence truly matches the user query.\n"
        "Be strict and conservative.\n"
        "Return JSON only with keys decision, confidence, reason.\n"
        "decision must be one of: exact, partial, mismatch.\n"
        "Use mismatch when the evidence is only loosely related, mixes different incidents, or requires assumptions.\n"
        "Use exact only when the evidence directly supports the asked clip.\n"
        "Use partial only when the core incident matches but details or time boundaries are coarse.\n"
        f"\nUser query: {query}"
        f"\nTop row video: {row.get('video_id')}"
        f"\nTop row time: {row.get('start_time')} - {row.get('end_time')}"
        f"\nTop row summary: {row.get('event_summary_en') or row.get('event_text_en') or ''}"
        f"\nPrimary evidence time: {primary.get('start_time')} - {primary.get('end_time')}"
        f"\nPrimary evidence summary: {primary.get('event_summary_en') or primary.get('event_text_en') or ''}"
    )
    try:
        model = llm.bind(max_tokens=120) if hasattr(llm, "bind") else llm
        raw = model.invoke(
            [
                SystemMessage(content="You are a strict retrieval match verifier. Return JSON only."),
                HumanMessage(content=prompt),
            ],
            config=config,
        )
        content = raw.content if hasattr(raw, "content") else str(raw)
        data = _parse_json_object(str(content))
        if not isinstance(data, dict):
            return None
        decision = str(data.get("decision") or "").strip().lower()
        if decision not in _FAST_DECISIONS:
            return None
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        return {
            "decision": decision,
            "confidence": max(0.0, min(1.0, confidence)),
            "reason": str(data.get("reason") or "").strip()[:200],
            "mode": "llm",
        }
    except Exception:
        return None


def _skipped_verdict(reason: str) -> dict[str, Any]:
    return {
        "decision": "skipped",
        "confidence": 0.0,
        "reason": reason,
        "mode": "skipped",
    }


def create_match_verifier_node(llm: Any = None):
    def match_verifier_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        answer_type = str(state.get("answer_type") or "").strip().lower()
        if answer_type != "existence":
            return {
                "verifier_result": _skipped_verdict(f"answer_type={answer_type or 'unknown'}"),
                "current_node": "match_verifier_node",
            }

        query = str(state.get("original_user_query") or state.get("user_query") or "").strip()
        rows = _select_rows(state)
        if not rows:
            return {
                "verifier_result": {
                    "decision": "mismatch",
                    "confidence": 0.98,
                    "reason": "no_rows",
                    "mode": "rule",
                },
                "current_node": "match_verifier_node",
            }

        top_row = rows[0]
        primary = _pick_primary_row(top_row)
        verdict = _llm_verdict(llm, query, top_row, primary, config) or _heuristic_verdict(query, top_row, primary)
        return {
            "verifier_result": {
                **verdict,
                "video_id": str(primary.get("video_id") or top_row.get("video_id") or "").strip(),
                "start_time": primary.get("start_time", top_row.get("start_time")),
                "end_time": primary.get("end_time", top_row.get("end_time")),
                "primary_summary": str(primary.get("event_summary_en") or primary.get("event_text_en") or "")[:400],
            },
            "current_node": "match_verifier_node",
        }

    return match_verifier_node
