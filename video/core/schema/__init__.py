"""事件 / Clip / LLM 输出等结构化协议。"""

from video.core.schema.refined_event_llm import (
    RefinedAllClipsPayload,
    RefinedEntity,
    RefinedEvent,
    RefinedEventsPayload,
    VectorAllClipsPayload,
    VectorEvent,
    VectorEventsPayload,
)

__all__ = [
    "RefinedEntity",
    "RefinedEvent",
    "RefinedEventsPayload",
    "RefinedAllClipsPayload",
    "VectorEvent",
    "VectorEventsPayload",
    "VectorAllClipsPayload",
]
