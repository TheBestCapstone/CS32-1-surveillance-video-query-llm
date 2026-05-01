import re
from typing import Any

from db.config import get_graph_chroma_parent_collection, get_graph_chroma_path
from tools.db_access import ChromaGateway


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


def _dedupe_texts(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _safe_min_time(rows: list[dict[str, Any]]) -> float | None:
    nums = [float(row["start_time"]) for row in rows if isinstance(row.get("start_time"), (int, float))]
    return min(nums) if nums else None


def _safe_max_time(rows: list[dict[str, Any]]) -> float | None:
    nums = [float(row["end_time"]) for row in rows if isinstance(row.get("end_time"), (int, float))]
    return max(nums) if nums else None


def _aggregate_parent_fallback(video_id: str, child_rows: list[dict[str, Any]]) -> dict[str, Any]:
    start_time = _safe_min_time(child_rows)
    end_time = _safe_max_time(child_rows)
    track_ids = _dedupe_texts([row.get("track_id") for row in child_rows])
    child_event_ids = _dedupe_texts([row.get("event_id") for row in child_rows])
    summaries = _dedupe_texts([row.get("event_summary_en") or row.get("event_text_en") for row in child_rows])
    object_types = _dedupe_texts([row.get("object_type") for row in child_rows])
    object_colors = _dedupe_texts([row.get("object_color_en") for row in child_rows])
    scene_zones = _dedupe_texts([row.get("scene_zone_en") for row in child_rows])
    best_distance = min([float(row["_distance"]) for row in child_rows if isinstance(row.get("_distance"), (int, float))], default=None)
    best_hybrid = max([float(row["_hybrid_score"]) for row in child_rows if isinstance(row.get("_hybrid_score"), (int, float))], default=None)
    summary_parts = [
        f"Video {video_id}.",
        f"This parent view summarizes {len(child_rows)} child results.",
    ]
    if object_types:
        summary_parts.append("Object types: " + ", ".join(object_types) + ".")
    if object_colors:
        summary_parts.append("Object colors: " + ", ".join(object_colors) + ".")
    if scene_zones:
        summary_parts.append("Scene zones: " + ", ".join(scene_zones) + ".")
    if summaries:
        summary_parts.append("Child summaries: " + " ".join(summaries[:5]))
    return {
        "event_id": video_id,
        "record_id": video_id,
        "video_id": video_id,
        "track_id": ",".join(track_ids[:8]) if track_ids else None,
        "start_time": start_time,
        "end_time": end_time,
        "event_summary_en": " ".join(summary_parts),
        "event_text_en": " ".join(summary_parts),
        "_distance": best_distance,
        "_hybrid_score": best_hybrid,
        "_source_type": "parent_projection",
        "_record_level": "parent",
        "_parent_hit_count": len(child_rows),
        "_child_event_ids": child_event_ids,
        "_child_rows": child_rows,
    }


def project_rows_to_parent_context(rows: list[dict[str, Any]] | None, limit: int = 5) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows or []:
        video_id = str(row.get("video_id") or "").strip()
        if not video_id:
            continue
        grouped.setdefault(video_id, []).append(row)
    if not grouped:
        return []

    ordered_videos = sorted(
        grouped.keys(),
        key=lambda video_id: min(
            [
                float(item.get("_distance"))
                for item in grouped[video_id]
                if isinstance(item.get("_distance"), (int, float))
            ]
            or [999999.0]
        ),
    )

    parent_lookup: dict[str, dict[str, Any]] = {}
    try:
        gateway = ChromaGateway(
            db_path=get_graph_chroma_path(),
            collection_name=get_graph_chroma_parent_collection(),
        )
        parent_records = gateway.get_records_by_ids(ordered_videos)
        for item in parent_records:
            parent_lookup[str(item.get("record_id"))] = item
    except Exception:
        parent_lookup = {}

    out: list[dict[str, Any]] = []
    for rank, video_id in enumerate(ordered_videos[:limit], start=1):
        child_rows = grouped[video_id]
        parent_record = parent_lookup.get(video_id)
        if parent_record:
            metadata = parent_record.get("metadata") if isinstance(parent_record.get("metadata"), dict) else {}
            row = _aggregate_parent_fallback(video_id, child_rows)
            parent_doc = str(parent_record.get("document") or "").strip()
            if parent_doc:
                row["event_summary_en"] = parent_doc
                row["event_text_en"] = parent_doc
            row["start_time"] = metadata.get("start_time", row.get("start_time"))
            row["end_time"] = metadata.get("end_time", row.get("end_time"))
            row["_parent_collection_hit"] = True
            row["_parent_child_count"] = metadata.get("child_count")
            row["_parent_scene_zones"] = metadata.get("scene_zones")
            row["_parent_object_types"] = metadata.get("object_types")
            row["_parent_object_colors"] = metadata.get("object_colors")
        else:
            row = _aggregate_parent_fallback(video_id, child_rows)
            row["_parent_collection_hit"] = False
        row["_parent_rank"] = rank
        out.append(row)
    return out


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
