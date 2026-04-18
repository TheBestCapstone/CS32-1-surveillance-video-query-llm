import re
from typing import Any


DEFAULT_SEARCH_CONFIG = {
    "candidate_limit": 80,
    "top_k_per_event": 20,
    "rerank_top_k": 5,
    "distance_threshold": None,
    "hybrid_alpha": 0.7,
    "hybrid_fallback_alpha": 0.9,
    "hybrid_limit": 50,
    "sql_limit": 80,
}


def build_search_config(existing: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(DEFAULT_SEARCH_CONFIG)
    if isinstance(existing, dict):
        cfg.update({k: v for k, v in existing.items() if v is not None})
    return cfg


def extract_structured_filters(user_query: str) -> dict[str, str]:
    q = (user_query or "").lower()
    out: dict[str, str] = {}
    for token in ["person", "car", "truck", "bus", "bike", "motorcycle"]:
        if token in q:
            out["object_type"] = token
            break
    for token in ["dark", "black", "white", "red", "blue", "unknown"]:
        if token in q:
            out["object_color_en"] = token
            break
    zone_aliases = [
        ("left bleachers", "left bleachers"),
        ("bleachers", "bleachers"),
        ("parking area", "parking"),
        ("parking", "parking"),
        ("sidewalk", "sidewalk"),
        ("right side", "road_right"),
        ("right-center", "road_right"),
        ("sideline", "road_right"),
        ("road right", "road_right"),
        ("court center-right", "center-right"),
        ("center-right", "center-right"),
        ("center court", "center"),
        ("court", "court"),
        ("baseline", "baseline"),
        ("center", "center"),
    ]
    for phrase, normalized in zone_aliases:
        if phrase in q:
            out["scene_zone_en"] = normalized
            break
    return out


def infer_sql_plan(user_query: str, search_config: dict[str, Any]) -> dict[str, Any]:
    filters = extract_structured_filters(user_query)
    where = [{"field": k, "op": "contains" if k == "scene_zone_en" else "=", "value": v} for k, v in filters.items()]
    return {
        "table": "episodic_events",
        "fields": [
            "event_id",
            "video_id",
            "track_id",
            "start_time",
            "end_time",
            "object_type",
            "object_color_en",
            "scene_zone_en",
            "appearance_notes_en",
            "event_summary_en",
        ],
        "where": where,
        "order_by": "start_time ASC",
        "limit": int(search_config.get("sql_limit", 80)),
    }


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def normalize_sql_rows(rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows or []:
        normalized.append(
            {
                **row,
                "event_id": row.get("event_id"),
                "video_id": row.get("video_id"),
                "track_id": row.get("track_id"),
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
                "object_type": row.get("object_type"),
                "object_color_en": row.get("object_color_en"),
                "scene_zone_en": row.get("scene_zone_en"),
                "event_summary_en": row.get("event_summary_en") or row.get("event_text_en") or row.get("event_text_cn"),
                "event_text_en": row.get("event_text_en") or row.get("event_summary_en"),
                "_distance": row.get("_distance", 0.0),
                "_source_type": row.get("_source_type", "sql"),
            }
        )
    return normalized


def normalize_hybrid_rows(rows: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows or []:
        normalized.append(
            {
                **row,
                "event_id": row.get("event_id"),
                "video_id": row.get("video_id"),
                "track_id": row.get("track_id"),
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
                "object_type": row.get("object_type"),
                "object_color_en": row.get("object_color_en"),
                "scene_zone_en": row.get("scene_zone_en"),
                "event_summary_en": row.get("event_summary_en") or row.get("event_text") or row.get("event_text_en"),
                "event_text_en": row.get("event_text_en") or row.get("event_text") or row.get("event_summary_en"),
                "_distance": _safe_float(row.get("_distance", row.get("distance"))),
                "_hybrid_score": _safe_float(row.get("_hybrid_score", row.get("hybrid_score"))),
                "_bm25": _safe_float(row.get("_bm25")),
                "_source_type": row.get("_source_type", "hybrid"),
            }
        )
    return normalized


def build_routing_metrics(
    *,
    execution_mode: str,
    label: str,
    query: str,
    sql_rows_count: int,
    hybrid_rows_count: int,
    sql_error: str | None = None,
    hybrid_error: str | None = None,
) -> dict[str, Any]:
    return {
        "execution_mode": execution_mode,
        "label": label,
        "query": query,
        "sql_rows_count": sql_rows_count,
        "hybrid_rows_count": hybrid_rows_count,
        "sql_error": sql_error,
        "hybrid_error": hybrid_error,
    }


def extract_text_tokens_for_sql(user_query: str, filters: dict[str, str]) -> list[str]:
    filter_terms: set[str] = set()
    for value in filters.values():
        filter_terms.update(t for t in re.findall(r"[a-z0-9_]+", str(value).lower()) if t)
    stopwords = {
        "did",
        "you",
        "see",
        "any",
        "the",
        "show",
        "me",
        "are",
        "there",
        "database",
        "look",
        "for",
        "find",
        "near",
        "who",
        "what",
        "where",
        "with",
        "into",
        "from",
        "that",
        "this",
        "persons",
        "person",
        "cars",
        "car",
        "area",
        "moving",
        "clothed",
        "in",
        "on",
    }
    return [
        t
        for t in re.findall(r"[a-z0-9_]+", user_query.lower())
        if len(t) > 2 and t not in stopwords and t not in filter_terms
    ][:4]
