import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage


class ParsedQuestion(TypedDict):
    event: Optional[str]
    color: Optional[str]
    time: Optional[str]
    move: Optional[bool]


class ToolChoice(TypedDict, total=False):
    mode: str
    sql_needed: bool
    hybrid_needed: bool
    video_vect_needed: bool
    sub_queries: Dict[str, Any]


class SearchResult(TypedDict):
    source: str
    rows: List[Dict[str, Any]]
    error: Optional[str]


class ReflectionResult(TypedDict, total=False):
    feedback: Optional[str]
    quality_score: float
    needs_retry: bool
    optimized: bool
    can_continue: bool
    errors: list[Any]


class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    user_query: str
    parsed_question: ParsedQuestion
    tool_choice: ToolChoice
    event_list: List[str]
    meta_list: List[Dict[str, Any]]
    sql_result: List[Dict[str, Any]]
    hybrid_result: List[Dict[str, Any]]
    video_vect_result: List[Dict[str, Any]]
    merged_result: List[Dict[str, Any]]
    rerank_result: List[Dict[str, Any]]
    tool_error: Optional[str]
    route: str
    retry_count: int
    thought: str
    final_answer: str
    is_parallel: bool
    parallel_queries: List[str]
    reflection_result: ReflectionResult
    syntax_valid: bool
    syntax_error: Optional[str]
    current_node: str


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
            elif isinstance(item, str):
                chunks.append(item)
        return "\n".join(chunk for chunk in chunks if chunk).strip()
    return str(content)


def normalize_text_value(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def question_to_meta_and_event(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    meta_list: list[dict[str, Any]] = []
    event_list: list[str] = []
    event = normalize_text_value(payload.get("event"))
    if event and event.lower() != "null":
        event_list.append(event)
    color = normalize_text_value(payload.get("color"))
    if color and color.lower() != "null":
        meta_list.append({"field": "object_color_cn", "op": "contains", "value": color})
    time_text = normalize_text_value(payload.get("time"))
    if time_text and time_text.lower() != "null":
        range_match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*$", time_text)
        if range_match:
            meta_list.append({"field": "start_time", "op": ">=", "value": float(range_match.group(1))})
            meta_list.append({"field": "end_time", "op": "<=", "value": float(range_match.group(2))})
        else:
            point_match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", time_text)
            if point_match:
                meta_list.append({"field": "start_time", "op": ">=", "value": float(point_match.group(1))})
            elif time_text in {"今天", "今日", "当天"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0})
            elif time_text in {"上午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 0.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 43200.0})
            elif time_text in {"下午"}:
                meta_list.append({"field": "start_time", "op": ">=", "value": 43200.0})
                meta_list.append({"field": "end_time", "op": "<=", "value": 86400.0})
            else:
                hm_range_match = re.match(r"^\s*(\d{1,2}):(\d{2})\s*[-~到至]\s*(\d{1,2}):(\d{2})\s*$", time_text)
                if hm_range_match:
                    start_sec = int(hm_range_match.group(1)) * 3600 + int(hm_range_match.group(2)) * 60
                    end_sec = int(hm_range_match.group(3)) * 3600 + int(hm_range_match.group(4)) * 60
                    meta_list.append({"field": "start_time", "op": ">=", "value": float(start_sec)})
                    meta_list.append({"field": "end_time", "op": "<=", "value": float(end_sec)})
    if payload.get("move") is False:
        meta_list.append({"field": "appearance_notes_cn", "op": "contains", "value": "静止"})
    return meta_list, event_list


def default_db_path() -> Path:
    return Path(__file__).resolve().parents[1] / "backup_legacy" / "src" / "agent" / "memory" / "episodic" / "lancedb"


if __name__ == "__main__":
    payload = {"event": "进入", "color": "红色", "time": "今天", "move": None}
    meta_list, event_list = question_to_meta_and_event(payload)
    print("event_list:", event_list)
    print("meta_list:", meta_list)