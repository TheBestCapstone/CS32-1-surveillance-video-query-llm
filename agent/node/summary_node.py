from typing import Any

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
        event_id = row.get("event_id")
        start_time = row.get("start_time")
        end_time = row.get("end_time")
        key = f"{source_type}|{video_id}|{event_id}|{start_time}|{end_time}"
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
        rendered.append(
            f"[{item['source_type']}] {item['video_id']} | event_id={item.get('event_id')} | "
            f"{item.get('start_time')}-{item.get('end_time')}"
        )
    return "Sources: " + "; ".join(rendered)


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

        fallback_summary = raw_answer or "No matching results were found."
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
            "You are the final response summarizer for a basketball retrieval assistant. "
            "Write a concise, friendly, natural English summary for a native speaker. "
            "Be accurate, grounded in the provided results, and easy to read. "
            "Do not mention internal routing, SQL, hybrid retrieval, or chain-of-thought. "
            "Keep the answer under 90 words. Do not include a sources section; sources will be appended separately."
            f"\n\nOriginal user query: {original_query}"
            f"\nRewritten retrieval query: {rewritten_query}"
            f"\nRetrieved result count: {len(rows)}"
            f"\nTop results: {row_digest[:3]}"
            f"\nDraft answer: {raw_answer}"
        )
        try:
            model = llm.bind(max_tokens=120) if hasattr(llm, "bind") else llm
            raw = model.invoke(
                [SystemMessage(content="Return only the final English summary text."), HumanMessage(content=prompt)],
                config=config,
            )
            summary_text = raw.content if hasattr(raw, "content") else str(raw)
            payload = {"summary": str(summary_text).strip(), "style": "llm_summary", "confidence": 0.8}
        except Exception:
            payload = {"summary": fallback_summary, "style": "fallback", "confidence": 0.3}

        final_summary = str(payload.get("summary", fallback_summary)).strip() or fallback_summary
        final_text = final_summary if not rendered_citations else f"{final_summary}\n{rendered_citations}"
        payload["citations"] = citations
        return {
            "final_answer": final_text,
            "summary_result": payload,
            "current_node": "summary_node",
            "messages": [AIMessage(content=final_text)],
        }

    return summary_node
