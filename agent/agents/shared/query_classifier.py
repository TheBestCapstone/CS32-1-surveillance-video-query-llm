import json
import os
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

QUERY_CLASSIFICATION_OUTPUT_SCHEMA = {
    "title": "query_classification",
    "type": "object",
    "properties": {
        "label": {"type": "string", "enum": ["structured", "semantic", "mixed"]},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["label", "confidence", "reason"],
}


LABEL_STRUCTURED = "structured"
LABEL_SEMANTIC = "semantic"
LABEL_MIXED = "mixed"


def _normalize_label(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {LABEL_STRUCTURED, LABEL_SEMANTIC, LABEL_MIXED}:
        return text
    return LABEL_MIXED


def _normalize_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except Exception:
        conf = 0.5
    return max(0.0, min(1.0, conf))


def _fallback_result(reason: str, label: str = LABEL_MIXED) -> Dict[str, Any]:
    safe_label = _normalize_label(label)
    return {
        "label": safe_label,
        "confidence": 0.35,
        "reason": reason,
        "signals": {"structured": 0, "semantic": 0},
    }


def _fast_path_classification(text: str) -> Dict[str, Any] | None:
    low = (text or "").strip().lower()
    if not low:
        return None

    semantic_cues = [" near ", " around ", " similar ", " moving ", " after ", " before "]
    explicit_location_cues = [
        "parking",
        "sidewalk",
        "baseline",
        "center court",
        "court",
        "bleachers",
        "road right",
        "right side",
    ]
    structured_cues = ["did you see", "are there", "show me", "list", "how many", "person", "car", "dark", "database"]

    padded = f" {low} "
    has_semantic_cue = any(cue in padded for cue in semantic_cues)
    has_explicit_location = any(cue in low for cue in explicit_location_cues)
    has_structured_cue = any(cue in low for cue in structured_cues)

    if has_structured_cue and has_explicit_location and not has_semantic_cue:
        return {
            "label": LABEL_STRUCTURED,
            "confidence": 0.86,
            "reason": "fast-path explicit filter query",
            "signals": {"structured": 1, "semantic": 0},
        }
    return None


def classify_query(query: str, llm: Any = None, config: Any = None) -> Dict[str, Any]:
    text = (query or "").strip()
    if not text:
        return _fallback_result("empty query fallback")
    fast_path = _fast_path_classification(text)
    if fast_path is not None:
        return fast_path

    if llm is None:
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model_name=os.getenv("DASHSCOPE_CHAT_MODEL", "qwen3-max"),
                temperature=0.0,
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url=os.getenv("DASHSCOPE_URL"),
            )
        except Exception:
            return _fallback_result("llm init failed")

    prompt = (
        "你是查询分类器。请判断用户问题属于 structured / semantic / mixed。"
        "structured: 明确字段过滤、存在性/计数/列表查询为主；"
        "semantic: 语义理解、相似检索、关系描述为主；"
        "mixed: 两者都明显存在。"
        "判定优先级：若问题主要是是否存在/列出/查某类目标，即使语句是自然语言，也优先 structured。"
        "只有当问题核心依赖语义关系（near/around/similar/行为过程）时才判 semantic。"
        "示例："
        "1) Did you see any person in the database? -> structured；"
        "2) Show me dark persons. -> structured；"
        "3) Find a person near the left bleachers. -> semantic。"
        "仅输出结构化 JSON。"
        f"\n\n用户问题: {text}"
    )
    try:
        if hasattr(llm, "with_structured_output"):
            model = llm.with_structured_output(QUERY_CLASSIFICATION_OUTPUT_SCHEMA)
            result = model.invoke(
                [SystemMessage(content="严格输出 JSON。"), HumanMessage(content=prompt)],
                config=config,
            )
            payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        else:
            raw = llm.invoke(
                [SystemMessage(content="严格输出 JSON。"), HumanMessage(content=prompt)],
                config=config,
            )
            text_out = raw.content if hasattr(raw, "content") else str(raw)
            text_out = text_out.replace("```json", "").replace("```", "").strip()
            payload = json.loads(text_out)
    except Exception:
        return _fallback_result("llm classify failed")

    label = _normalize_label(payload.get("label"))
    confidence = _normalize_confidence(payload.get("confidence"))
    reason = str(payload.get("reason", "llm classifier")).strip() or "llm classifier"
    signals = {
        "structured": 1 if label in {LABEL_STRUCTURED, LABEL_MIXED} else 0,
        "semantic": 1 if label in {LABEL_SEMANTIC, LABEL_MIXED} else 0,
    }
    return {"label": label, "confidence": confidence, "reason": reason, "signals": signals}


def classify_mode_from_label(label: str) -> str:
    # Keep mode compatibility for existing tests/metrics while execution is parallel.
    if label == LABEL_STRUCTURED:
        return "pure_sql"
    if label == LABEL_SEMANTIC:
        return "hybrid_search"
    return os.getenv("AGENT_MIXED_COMPAT_MODE", "hybrid_search")
