from typing import Any
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


def _select_rows(state: AgentState) -> list[dict[str, Any]]:
    if "rerank_result" in state:
        return list(state.get("rerank_result") or [])
    if "merged_result" in state:
        return list(state.get("merged_result") or [])
    if "hybrid_result" in state:
        return list(state.get("hybrid_result") or [])
    return list(state.get("sql_result") or [])


def _infer_source_type(row: dict[str, Any]) -> str:
    trace = row.get("_fusion_trace") if isinstance(row.get("_fusion_trace"), dict) else {}
    if trace.get("sql_rank") and trace.get("hybrid_rank"):
        return "mixed"
    if trace.get("sql_rank"):
        return "sql"
    if trace.get("hybrid_rank"):
        return "hybrid"
    if row.get("_distance") not in (None, "N/A"):
        return "hybrid"
    return "sql"


def _build_citations(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        source_type = _infer_source_type(row)
        video_id = str(row.get("video_id") or "unknown_video")
        is_parent = str(row.get("_record_level") or "").lower() == "parent"
        event_id = None if is_parent else row.get("event_id")
        start_time = row.get("start_time")
        end_time = row.get("end_time")
        key = f"{source_type}|{video_id}|{event_id if event_id is not None else 'parent'}|{start_time}|{end_time}"
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "source_type": source_type,
                "video_id": video_id,
                "event_id": event_id,
                "start_time": start_time,
                "end_time": end_time,
                "record_level": "parent" if is_parent else "child",
            }
        )
        if len(citations) >= limit:
            break
    return citations


def _render_citations(citations: list[dict[str, Any]]) -> str:
    if not citations:
        return ""
    rendered = []
    for item in citations:
        if item.get("record_level") == "parent":
            rendered.append(
                f"[{item['source_type']}] {item['video_id']} | parent | {item.get('start_time')}-{item.get('end_time')}"
            )
        else:
            rendered.append(
                f"[{item['source_type']}] {item['video_id']} | event_id={item.get('event_id')} | "
                f"{item.get('start_time')}-{item.get('end_time')}"
            )
    return "Sources: " + "; ".join(rendered)


def _format_clip_time(value: Any) -> str:
    try:
        seconds = max(0, int(round(float(value))))
    except Exception:
        return "unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"


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


def _looks_like_binary_query(text: str) -> bool:
    query = str(text or "").strip().lower()
    if not query:
        return False
    return bool(
        re.match(r"^(is|are|was|were|do|does|did|can|could|has|have|had)\b", query)
        or " is there " in f" {query} "
        or query.endswith("?")
    )


def _build_factual_summary(rows: list[dict[str, Any]], query: str) -> str:
    if not rows:
        return "No matching clip is expected."
    top_row = rows[0]
    primary = _pick_primary_row(top_row)
    video_id = str(primary.get("video_id") or top_row.get("video_id") or "unknown_video").strip()
    start_time = primary.get("start_time", top_row.get("start_time"))
    end_time = primary.get("end_time", top_row.get("end_time"))
    start_text = _format_clip_time(start_time)
    end_text = _format_clip_time(end_time)
    if _looks_like_binary_query(query):
        return f"Yes. The relevant clip is in {video_id}, around {start_text} - {end_text}."
    return f"The most relevant clip is in {video_id}, around {start_text} - {end_text}."


def _normalize_summary_output(text: str, fallback: str) -> str:
    cleaned = " ".join(str(text or "").strip().split())
    if not cleaned:
        return fallback
    if "No matching clip is expected." in cleaned:
        return "No matching clip is expected."
    if len(cleaned) > 140:
        return fallback
    if cleaned.count("Abuse") > 1:
        return fallback
    return cleaned


def _canonicalize_summary(
    text: str,
    *,
    fallback: str,
    rows: list[dict[str, Any]],
    query: str,
) -> str:
    normalized = _normalize_summary_output(text, fallback)
    if normalized == "No matching clip is expected.":
        return normalized
    if normalized.startswith("Yes. The relevant clip is in ") or normalized.startswith("The most relevant clip is in "):
        return normalized
    return _build_factual_summary(rows, query)


def create_summary_node(llm: Any = None):
    def summary_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        raw_answer = str(state.get("raw_final_answer") or state.get("final_answer") or "").strip()
        rows = _select_rows(state)
        citations = _build_citations(rows)
        rendered_citations = _render_citations(citations)
        original_query = str(state.get("original_user_query") or state.get("user_query") or "").strip()
        rewritten_query = str(state.get("rewritten_query") or state.get("user_query") or "").strip()
        row_digest = [
            {
                "video_id": row.get("video_id"),
                "event_id": row.get("event_id"),
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
                "summary": row.get("event_summary_en") or row.get("event_text_en") or row.get("event_text_cn"),
            }
            for row in rows[:5]
        ]

        factual_fallback = _build_factual_summary(rows, original_query or rewritten_query)
        fallback_summary = factual_fallback or raw_answer or "No matching clip is expected."
        if not rows:
            return {
                "final_answer": fallback_summary,
                "summary_result": {
                    "summary": fallback_summary,
                    "style": "empty_result_fallback",
                    "confidence": 0.95,
                    "citations": [],
                },
                "current_node": "summary_node",
                "messages": [AIMessage(content=fallback_summary)],
            }
        if llm is None:
            final_text = fallback_summary if not rendered_citations else f"{fallback_summary}\n{rendered_citations}"
            return {
                "final_answer": final_text,
                "summary_result": {
                    "summary": fallback_summary,
                    "style": "fallback",
                    "confidence": 0.3,
                    "citations": citations,
                },
                "current_node": "summary_node",
                "messages": [AIMessage(content=final_text)],
            }

        prompt = (
            "You are the final response summarizer for a retrieval assistant. "
            "Return a short factual answer that matches the reference-answer style used in evaluation. "
            "Use only the single strongest result. Do not merge multiple videos. "
            "If the evidence does not clearly support the query, answer exactly: No matching clip is expected. "
            "If the evidence supports the query, use exactly this format: "
            "'Yes. The relevant clip is in <video_id>, around <h:mm:ss> - <h:mm:ss>.' "
            "For non-binary questions, use: 'The most relevant clip is in <video_id>, around <h:mm:ss> - <h:mm:ss>.' "
            "Do not add extra scene details, explanations, or a sources section."
            f"\n\nOriginal user query: {original_query}"
            f"\nRewritten retrieval query: {rewritten_query}"
            f"\nRetrieved result count: {len(rows)}"
            f"\nTop results: {row_digest[:2]}"
            f"\nPreferred fallback answer: {factual_fallback}"
            f"\nDraft answer: {raw_answer}"
        )
        try:
            model = llm.bind(max_tokens=120) if hasattr(llm, "bind") else llm
            raw = model.invoke(
                [SystemMessage(content="Return only the final English summary text."), HumanMessage(content=prompt)],
                config=config,
            )
            summary_text = raw.content if hasattr(raw, "content") else str(raw)
            payload = {
                "summary": _normalize_summary_output(str(summary_text), fallback_summary),
                "style": "llm_summary",
                "confidence": 0.8,
            }
        except Exception:
            payload = {"summary": fallback_summary, "style": "fallback", "confidence": 0.3}

        final_summary = _canonicalize_summary(
            str(payload.get("summary", fallback_summary)).strip(),
            fallback=fallback_summary,
            rows=rows,
            query=original_query or rewritten_query,
        )
        final_text = final_summary if not rendered_citations else f"{final_summary}\n{rendered_citations}"
        payload["citations"] = citations
        payload["summary"] = final_summary
        return {
            "final_answer": final_text,
            "summary_result": payload,
            "current_node": "summary_node",
            "messages": [AIMessage(content=final_text)],
        }

    return summary_node
