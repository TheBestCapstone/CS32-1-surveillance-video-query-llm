import os
from typing import Any, Dict, List, Tuple


def _safe_float(v: Any, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return default


def load_fusion_weights() -> Dict[str, Dict[str, float]]:
    return {
        "structured": {
            "sql": _safe_float(os.getenv("AGENT_FUSION_STRUCTURED_SQL_WEIGHT", "0.8"), 0.8),
            "hybrid": _safe_float(os.getenv("AGENT_FUSION_STRUCTURED_HYBRID_WEIGHT", "0.2"), 0.2),
        },
        "semantic": {
            "sql": _safe_float(os.getenv("AGENT_FUSION_SEMANTIC_SQL_WEIGHT", "0.2"), 0.2),
            "hybrid": _safe_float(os.getenv("AGENT_FUSION_SEMANTIC_HYBRID_WEIGHT", "0.8"), 0.8),
        },
        "mixed": {
            "sql": _safe_float(os.getenv("AGENT_FUSION_MIXED_SQL_WEIGHT", "0.5"), 0.5),
            "hybrid": _safe_float(os.getenv("AGENT_FUSION_MIXED_HYBRID_WEIGHT", "0.5"), 0.5),
        },
        "rrf_k": {
            "k": _safe_float(os.getenv("AGENT_FUSION_RRF_K", "60"), 60.0),
        },
    }


def _row_key(row: Dict[str, Any]) -> str:
    event_id = row.get("event_id")
    if event_id is not None:
        return f"event_id:{event_id}"
    return "|".join(
        [
            str(row.get("video_id", "")),
            str(row.get("track_id", "")),
            str(row.get("start_time", "")),
            str(row.get("end_time", "")),
            str(row.get("event_summary_en", row.get("event_text", ""))),
        ]
    )


def weighted_rrf_fuse(
    sql_rows: List[Dict[str, Any]],
    hybrid_rows: List[Dict[str, Any]],
    label: str,
    limit: int = 50,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cfg = load_fusion_weights()
    weights = cfg.get(label, cfg["mixed"])
    w_sql = float(weights["sql"])
    w_hybrid = float(weights["hybrid"])
    rrf_k = float(cfg["rrf_k"]["k"])

    score_map: Dict[str, float] = {}
    row_map: Dict[str, Dict[str, Any]] = {}
    trace: Dict[str, Dict[str, Any]] = {}

    for rank, row in enumerate(sql_rows, start=1):
        key = _row_key(row)
        score = w_sql * (1.0 / (rrf_k + rank))
        score_map[key] = score_map.get(key, 0.0) + score
        row_map[key] = row
        trace.setdefault(key, {}).update({"sql_rank": rank, "sql_rrf": score})

    for rank, row in enumerate(hybrid_rows, start=1):
        key = _row_key(row)
        score = w_hybrid * (1.0 / (rrf_k + rank))
        score_map[key] = score_map.get(key, 0.0) + score
        if key not in row_map:
            row_map[key] = row
        trace.setdefault(key, {}).update({"hybrid_rank": rank, "hybrid_rrf": score})

    ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:limit]
    out: List[Dict[str, Any]] = []
    for key, score in ranked:
        row = dict(row_map[key])
        row["_fusion_score"] = float(score)
        row["_fusion_label"] = label
        row["_fusion_trace"] = trace.get(key, {})
        out.append(row)

    return out, {
        "label": label,
        "weights": {"sql": w_sql, "hybrid": w_hybrid},
        "rrf_k": rrf_k,
        "sql_count": len(sql_rows),
        "hybrid_count": len(hybrid_rows),
        "fused_count": len(out),
        "method": "weighted_rrf",
    }

