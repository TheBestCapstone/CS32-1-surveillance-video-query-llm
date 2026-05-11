import os
from typing import Any, Dict, List, Optional, Tuple


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
        "multi_hop": {
            "sql": _safe_float(os.getenv("AGENT_FUSION_MULTIHOP_SQL_WEIGHT", "0.3"), 0.3),
            "hybrid": _safe_float(os.getenv("AGENT_FUSION_MULTIHOP_HYBRID_WEIGHT", "0.7"), 0.7),
        },
        # Multi-camera mode: three-way fusion with global_entity dominating
        "multi_camera": {
            "global_entity": _safe_float(
                os.getenv("AGENT_FUSION_MULTICAM_GE_WEIGHT", "0.65"), 0.65
            ),
            "sql": _safe_float(
                os.getenv("AGENT_FUSION_MULTICAM_SQL_WEIGHT", "0.15"), 0.15
            ),
            "hybrid": _safe_float(
                os.getenv("AGENT_FUSION_MULTICAM_HYBRID_WEIGHT", "0.20"), 0.20
            ),
        },
        "rrf_k": {
            "k": _safe_float(os.getenv("AGENT_FUSION_RRF_K", "60"), 60.0),
        },
    }


# P1-6: structured signals can soft-bias the {sql, hybrid} weights. Evidence
# is additive but bounded so the classifier label remains the primary driver.
_SIGNAL_BIAS_PER_HIT = _safe_float(os.getenv("AGENT_FUSION_SIGNAL_BIAS_PER_HIT", "0.05"), 0.05)
_SIGNAL_BIAS_CAP = _safe_float(os.getenv("AGENT_FUSION_SIGNAL_BIAS_CAP", "0.2"), 0.2)


def _apply_signal_bias(
    base_sql: float,
    base_hybrid: float,
    signals: Optional[Dict[str, Any]],
) -> Tuple[float, float, Dict[str, Any]]:
    if not isinstance(signals, dict):
        return base_sql, base_hybrid, {"applied": False, "reason": "no_signals"}

    def _hits(key: str) -> int:
        value = signals.get(key)
        if isinstance(value, (list, tuple, set)):
            return len(value)
        if isinstance(value, int):
            return max(0, value)
        return 0

    metadata_n = _hits("metadata_hits")
    relation_n = _hits("relation_cues")
    multi_step_n = _hits("multi_step_cues")

    sql_bias = min(_SIGNAL_BIAS_CAP, metadata_n * _SIGNAL_BIAS_PER_HIT)
    hybrid_bias = min(_SIGNAL_BIAS_CAP, (relation_n + multi_step_n) * _SIGNAL_BIAS_PER_HIT)

    sql_adj = max(0.0, base_sql + sql_bias - hybrid_bias)
    hybrid_adj = max(0.0, base_hybrid + hybrid_bias - sql_bias)
    total = sql_adj + hybrid_adj
    if total <= 0.0:
        return base_sql, base_hybrid, {"applied": False, "reason": "degenerate_after_bias"}
    sql_norm = sql_adj / total
    hybrid_norm = hybrid_adj / total
    return sql_norm, hybrid_norm, {
        "applied": True,
        "metadata_hits": metadata_n,
        "relation_cues": relation_n,
        "multi_step_cues": multi_step_n,
        "sql_bias": sql_bias,
        "hybrid_bias": hybrid_bias,
        "base_sql": base_sql,
        "base_hybrid": base_hybrid,
    }


def _normalize_event_id(event_id: Any) -> str | None:
    """Normalize event_id to a canonical string for cross-branch matching.

    SQL branch returns ``int`` (e.g. 42), Chroma branch may return ``str``
    (e.g. "42") or ``None``.  This function coerces numeric event_ids to
    ``str(int(...))`` so that ``_row_key`` generates the same key regardless
    of source branch, fixing the RRF overlap bug (P0-1).
    """
    if event_id is None:
        return None
    try:
        # Try int conversion: 42 → "42", "42" → "42", 42.0 → "42"
        return str(int(float(event_id)))
    except (ValueError, TypeError):
        # Non-numeric event_id (e.g. Chroma record ID): use as-is
        return str(event_id).strip()


def _row_key(row: Dict[str, Any]) -> str:
    # Prefer global_entity_id + start_time for cross-branch matching of
    # multi-camera entities (same entity has different event_id per camera).
    ge_id = row.get("global_entity_id")
    if ge_id:
        st = row.get("start_time", "")
        return f"ge:{ge_id}:{st}"
    event_id = _normalize_event_id(row.get("event_id"))
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
    *,
    signals: Optional[Dict[str, Any]] = None,
    global_entity_rows: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    cfg = load_fusion_weights()
    rrf_k = float(cfg["rrf_k"]["k"])

    # Multi-camera mode: global_entity dominates the fusion
    if global_entity_rows:
        mc_weights = cfg["multi_camera"]
        w_ge = float(mc_weights["global_entity"])
        w_sql = float(mc_weights["sql"])
        w_hybrid = float(mc_weights["hybrid"])
        fusion_mode = "multi_camera"
    else:
        weights = cfg.get(label, cfg["mixed"])
        w_sql = float(weights["sql"])
        w_hybrid = float(weights["hybrid"])
        w_ge = 0.0
        fusion_mode = label

    score_map: Dict[str, float] = {}
    row_map: Dict[str, Dict[str, Any]] = {}
    trace: Dict[str, Dict[str, Any]] = {}

    def _merge_rows(existing: Dict[str, Any] | None, incoming: Dict[str, Any], *, prefer_incoming: bool) -> Dict[str, Any]:
        if existing is None:
            return dict(incoming)
        merged = dict(existing)
        for key, value in incoming.items():
            if key not in merged or merged.get(key) in (None, "", [], {}):
                merged[key] = value
        if prefer_incoming:
            for key, value in incoming.items():
                if value not in (None, "", [], {}):
                    merged[key] = value
        return merged

    for rank, row in enumerate(sql_rows, start=1):
        key = _row_key(row)
        score = w_sql * (1.0 / (rrf_k + rank))
        score_map[key] = score_map.get(key, 0.0) + score
        row_map[key] = _merge_rows(row_map.get(key), row, prefer_incoming=False)
        trace.setdefault(key, {}).update({"sql_rank": rank, "sql_rrf": score, "seen_in_sql": True})

    for rank, row in enumerate(hybrid_rows, start=1):
        key = _row_key(row)
        score = w_hybrid * (1.0 / (rrf_k + rank))
        score_map[key] = score_map.get(key, 0.0) + score
        row_map[key] = _merge_rows(row_map.get(key), row, prefer_incoming=True)
        trace.setdefault(key, {}).update({"hybrid_rank": rank, "hybrid_rrf": score, "seen_in_hybrid": True})

    # GlobalEntity branch — highest weight in multi_camera mode
    for rank, row in enumerate(global_entity_rows or [], start=1):
        key = _row_key(row)
        score = w_ge * (1.0 / (rrf_k + rank))
        score_map[key] = score_map.get(key, 0.0) + score
        row_map[key] = _merge_rows(row_map.get(key), row, prefer_incoming=True)
        trace.setdefault(key, {}).update({"ge_rank": rank, "ge_rrf": score, "seen_in_ge": True})

    ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:limit]
    out: List[Dict[str, Any]] = []
    overlap_count = 0
    for key, score in ranked:
        row = dict(row_map[key])
        row_trace = dict(trace.get(key, {}))
        seen_in = sum(1 for k in ("seen_in_sql", "seen_in_hybrid", "seen_in_ge") if row_trace.get(k))
        if seen_in >= 2:
            overlap_count += 1
            row["_source_type"] = "fused"
        row_trace["total_rrf"] = float(score)
        row["_fusion_score"] = float(score)
        row["_fusion_label"] = fusion_mode
        row["_fusion_trace"] = row_trace
        out.append(row)

    fusion_meta: Dict[str, Any] = {
        "label": fusion_mode,
        "weights": {"sql": w_sql, "hybrid": w_hybrid, "global_entity": w_ge},
        "rrf_k": rrf_k,
        "sql_count": len(sql_rows),
        "hybrid_count": len(hybrid_rows),
        "ge_count": len(global_entity_rows or []),
        "fused_count": len(out),
        "overlap_count": overlap_count,
        "method": "weighted_rrf",
    }
    if fusion_mode != "multi_camera":
        _, _, bias_meta = _apply_signal_bias(w_sql, w_hybrid, signals)
        fusion_meta["signal_bias"] = bias_meta
    return out, fusion_meta

