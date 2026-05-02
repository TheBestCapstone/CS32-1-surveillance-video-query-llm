import os
import threading
from typing import Any


_MODEL_LOCK = threading.Lock()
_CROSS_ENCODER = None
_LOAD_ERROR: str | None = None


def rerank_enabled() -> bool:
    raw = os.getenv("AGENT_ENABLE_RERANK", "1").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def get_rerank_model_name() -> str:
    return os.getenv("AGENT_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")


def _build_pair_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    if row.get("video_id"):
        parts.append(f"video {row.get('video_id')}")
    if row.get("object_type"):
        parts.append(f"type {row.get('object_type')}")
    if row.get("object_color_en"):
        parts.append(f"color {row.get('object_color_en')}")
    if row.get("scene_zone_en"):
        parts.append(f"zone {row.get('scene_zone_en')}")
    summary = row.get("event_summary_en") or row.get("event_text_en") or row.get("event_text") or ""
    if summary:
        parts.append(str(summary))
    return ". ".join(str(part).strip() for part in parts if str(part).strip())


def _get_cross_encoder():
    global _CROSS_ENCODER, _LOAD_ERROR
    if _CROSS_ENCODER is not None:
        return _CROSS_ENCODER
    if _LOAD_ERROR is not None:
        raise RuntimeError(_LOAD_ERROR)
    with _MODEL_LOCK:
        if _CROSS_ENCODER is not None:
            return _CROSS_ENCODER
        if _LOAD_ERROR is not None:
            raise RuntimeError(_LOAD_ERROR)
        try:
            from sentence_transformers import CrossEncoder
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            _CROSS_ENCODER = CrossEncoder(get_rerank_model_name(), device=device)
            return _CROSS_ENCODER
        except Exception as exc:
            _LOAD_ERROR = f"rerank model load failed: {exc}"
            raise RuntimeError(_LOAD_ERROR) from exc


def rerank_rows(
    query: str,
    rows: list[dict[str, Any]] | None,
    *,
    top_k: int,
    candidate_limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_rows = list(rows or [])
    if not source_rows:
        return [], {"enabled": False, "reason": "empty_input"}
    if not rerank_enabled():
        return source_rows[:top_k], {"enabled": False, "reason": "disabled"}

    candidates = source_rows[: max(1, int(candidate_limit))]
    pairs = [(query, _build_pair_text(row)) for row in candidates]
    try:
        model = _get_cross_encoder()
        scores = model.predict(pairs, batch_size=min(16, len(pairs)), show_progress_bar=False)
    except Exception as exc:
        return source_rows[:top_k], {"enabled": False, "reason": "load_or_predict_failed", "error": str(exc)}

    rescored: list[dict[str, Any]] = []
    for row, score in zip(candidates, scores):
        updated = dict(row)
        updated["_rerank_score"] = float(score)
        rescored.append(updated)
    rescored.sort(
        key=lambda item: (
            float(item.get("_rerank_score", 0.0)),
            float(item.get("_hybrid_score", 0.0) or 0.0),
            -float(item.get("_distance", 1.0) or 1.0),
        ),
        reverse=True,
    )
    tail = source_rows[len(candidates) :]
    return rescored[:top_k] + tail, {
        "enabled": True,
        "model": get_rerank_model_name(),
        "input_count": len(source_rows),
        "candidate_count": len(candidates),
        "output_count": min(len(source_rows), top_k + len(tail)),
    }
