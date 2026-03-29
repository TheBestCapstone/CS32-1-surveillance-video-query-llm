import re
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage


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
    cot_context: List[Dict[str, Any]]  # CoT 中间状态
    force_reset: bool                  # 强制重置状态标志


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


class InputValidator:
    """统一的输入验证和提取器"""
    
    @staticmethod
    def extract_latest_query(state: AgentState) -> str:
        """
        从状态中安全、可靠地提取最新的用户查询。
        规范：
        1. 永远优先从 messages 列表的最后一条 HumanMessage 提取，防止历史 state 污染。
        2. 如果没有 messages，才退退求其次使用 state.get("user_query")。
        3. 进行基本的长度和合法性截断。
        """
        query = ""
        messages = state.get("messages", [])
        
        if messages:
            # 优先倒序寻找最后一条人类消息
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    query = content_to_text(msg.content)
                    break
                # 兼容字典格式的消息
                elif isinstance(msg, dict) and msg.get("type") == "human" and "content" in msg:
                    query = content_to_text(msg["content"])
                    break
                elif isinstance(msg, dict) and "content" in msg and not msg.get("type"):
                    # 极简的回退
                    query = content_to_text(msg["content"])
                    break

        # 如果 messages 提取失败，回退到 user_query 字段
        if not query:
            query = state.get("user_query", "")
            
        return InputValidator.sanitize_query(query)

    @staticmethod
    def sanitize_query(query: Any) -> str:
        """
        安全防护：防止注入，限制长度，清理非法字符
        """
        if not query:
            return ""
            
        # 统一转为字符串
        clean_query = str(query).strip()
        
        # 1. 长度限制 (防止超长文本攻击)
        max_length = 500
        if len(clean_query) > max_length:
            clean_query = clean_query[:max_length]
            
        # 2. 基础安全过滤
        return clean_query.strip()


class StateResetter:
    """状态重置器：用于在开始处理新查询前清理旧的临时状态"""
    
    # 哪些字段是当前查询产生的临时结果，需要在下一次查询时重置
    EPHEMERAL_FIELDS = {
        "parsed_question": {},
        "tool_choice": {},
        "event_list": [],
        "meta_list": [],
        "sql_result": [],
        "hybrid_result": [],
        "video_vect_result": [],
        "merged_result": [],
        "rerank_result": [],
        "tool_error": None,
        "route": "",
        "retry_count": 0,
        "thought": "",
        "final_answer": "",
        "is_parallel": False,
        "parallel_queries": [],
        "reflection_result": {},
        "syntax_valid": True,
        "syntax_error": None,
        "current_node": "",
        "cot_context": [],
    }

    @staticmethod
    def is_new_query(state: AgentState) -> bool:
        """
        检测是否为全新的用户查询：
        当 messages 列表中最新的一条消息是 HumanMessage，且与当前 state 中缓存的 user_query 不同，说明开启了新的一轮对话。
        或者 state 中设置了明确的 reset 标志。
        """
        if state.get("force_reset", False):
            return True
            
        latest_msg_text = ""
        messages = state.get("messages", [])
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, HumanMessage):
                    latest_msg_text = content_to_text(msg.content)
                    break
                elif isinstance(msg, dict) and msg.get("type") == "human":
                    latest_msg_text = content_to_text(msg.get("content", ""))
                    break
        
        latest_msg_text = InputValidator.sanitize_query(latest_msg_text)
        current_query = state.get("user_query", "")
        
        # 如果最新的人类消息不为空，且与当前存储的 user_query 不同，说明是新查询
        if latest_msg_text and latest_msg_text != current_query:
            return True
            
        return False

    @staticmethod
    def reset_ephemeral_state(state: AgentState, user_query: str) -> dict[str, Any]:
        """
        生成一个重置字典。该字典应被合并到当前的 AgentState 中。
        将所有临时结果恢复为默认值，同时更新 user_query。
        """
        reset_updates = {k: v for k, v in StateResetter.EPHEMERAL_FIELDS.items()}
        reset_updates["user_query"] = user_query
        reset_updates["force_reset"] = False # 清除强制重置标志
        
        return reset_updates


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