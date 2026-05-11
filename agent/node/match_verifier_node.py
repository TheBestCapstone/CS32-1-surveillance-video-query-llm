"""Existence-grounder node (P1-7 v2.3).

Only runs when ``state.answer_type == "existence"``. For other question
shapes it is a pass-through so retrieval scores are untouched.

In v2.3 (2026-05-02), the node became a *span re-selector*: instead of
inspecting only the rerank top-1 row, it presents the LLM with multiple
candidates from ``rerank_result`` (same-video chunks plus a few
cross-video top-1s for diversity) and asks it to pick the best matching
chunk together with a verdict. The chosen chunk's ``(video_id,
start_time, end_time, primary_summary)`` is written to
``verifier_result`` and downstream nodes (``summary_node``,
``final_answer_node``) prefer it whenever
``verifier_result.span_source == "rerank_reselected"``.

Why this matters: 56% of 50-case e2e runs had top-K filled by chunks
from a single video, and in 4 of 5 verifier=mismatch existence cases
the genuinely matching chunk was already inside ``rerank_result`` -
just not in the top-1 slot. Re-selecting inside ``rerank_result`` fixes
those without any new chroma fetch.

Compatibility:
- ``AGENT_VERIFIER_RESELECT_SPAN=0``: legacy single-row LLM verdict.
- ``AGENT_VERIFIER_USE_LLM=0`` (env): heuristic only (no LLM call).
- ``answer_type != "existence"``: pass-through, identical to v1 behaviour.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "around",
    "after",
    "any",
    "before",
    "being",
    "by",
    "can",
    "clip",
    "conducting",
    "did",
    "does",
    "for",
    "from",
    "full",
    "have",
    "how",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "one",
    "or",
    "other",
    "over",
    "person",
    "there",
    "their",
    "then",
    "to",
    "two",
    "up",
    "video",
    "was",
    "were",
    "while",
    "with",
}

_SCENE_TERMS = {"road", "room", "sofa", "wall", "wheelchair", "conveyor", "parking", "court", "bleachers"}

_FAST_DECISIONS = {"exact", "partial", "mismatch"}


# ---------------------------------------------------------------------------
# v2.3 env knobs
# ---------------------------------------------------------------------------


def _reselect_span_enabled() -> bool:
    raw = os.getenv("AGENT_VERIFIER_RESELECT_SPAN", "1").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _candidate_limit() -> int:
    raw = os.getenv("AGENT_VERIFIER_CANDIDATE_LIMIT", "8").strip()
    try:
        value = int(raw)
    except Exception:
        return 8
    return max(1, value)


def _cross_video_top_n() -> int:
    raw = os.getenv("AGENT_VERIFIER_CROSS_VIDEO_TOP_N", "2").strip()
    try:
        value = int(raw)
    except Exception:
        return 2
    return max(0, value)


def _llm_disabled() -> bool:
    raw = os.getenv("AGENT_MATCH_VERIFIER_USE_LLM", "1").strip().lower()
    return raw in {"0", "false", "no", "off"}


# ---------------------------------------------------------------------------
# Row helpers (shared with v1)
# ---------------------------------------------------------------------------


def _select_rows(state: AgentState) -> list[dict[str, Any]]:
    if "rerank_result" in state:
        return list(state.get("rerank_result") or [])
    if "hybrid_result" in state:
        return list(state.get("hybrid_result") or [])
    return list(state.get("sql_result") or [])


def _pick_primary_row(row: dict[str, Any]) -> dict[str, Any]:
    child_rows = row.get("_child_rows") if isinstance(row.get("_child_rows"), list) else []
    if not child_rows:
        return row

    def _sort_key(item: dict[str, Any]) -> tuple[float, float]:
        distance = item.get("_distance")
        hybrid = item.get("_hybrid_score")
        safe_distance = float(distance) if isinstance(distance, (int, float)) else 999999.0
        safe_hybrid = -float(hybrid) if isinstance(hybrid, (int, float)) else 0.0
        return (safe_distance, safe_hybrid)

    ranked_children = sorted(
        [item for item in child_rows if isinstance(item, dict)],
        key=_sort_key,
    )
    return ranked_children[0] if ranked_children else row


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _query_terms(query: str) -> set[str]:
    terms: set[str] = set()
    for token in _tokenize(query):
        if len(token) < 3 or token in _STOPWORDS:
            continue
        terms.add(token)
    return terms


def _evidence_text(row: dict[str, Any], primary: dict[str, Any] | None = None) -> str:
    primary = primary or row
    parts = [
        row.get("event_summary_en"),
        row.get("event_text_en"),
        primary.get("event_summary_en"),
        primary.get("event_text_en"),
        row.get("object_type"),
        row.get("object_color_en"),
        row.get("scene_zone_en"),
    ]
    return " ".join(str(item or "") for item in parts if item).lower()


def _row_summary(row: dict[str, Any], max_chars: int = 220) -> str:
    """Compact text used inside the multi-candidate prompt."""
    primary = _pick_primary_row(row)
    text = (
        primary.get("event_summary_en")
        or primary.get("event_text_en")
        or row.get("event_summary_en")
        or row.get("event_text_en")
        or ""
    )
    cleaned = " ".join(str(text).strip().split())
    return cleaned[: max_chars - 1] + "..." if len(cleaned) > max_chars else cleaned


def _row_descriptor(row: dict[str, Any]) -> dict[str, Any]:
    """Extract candidate fields downstream needs (used both in prompt and in verifier_result)."""
    primary = _pick_primary_row(row)
    return {
        "video_id": str(primary.get("video_id") or row.get("video_id") or "").strip(),
        "start_time": primary.get("start_time", row.get("start_time")),
        "end_time": primary.get("end_time", row.get("end_time")),
        "primary_summary": _row_summary(row, max_chars=400),
    }


# ---------------------------------------------------------------------------
# v1 single-row paths (kept as the legacy fallback)
# ---------------------------------------------------------------------------


def _heuristic_verdict_single(query: str, row: dict[str, Any], primary: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_text(row, primary)
    query_terms = _query_terms(query)
    if not query_terms:
        return {"decision": "partial", "confidence": 0.5, "reason": "empty_query_terms", "mode": "heuristic"}

    matched = sorted(term for term in query_terms if term in evidence)
    scene_terms = [term for term in query_terms if term in _SCENE_TERMS]
    scene_conflict = bool(scene_terms) and any(term not in evidence for term in scene_terms)
    coverage = len(matched) / max(len(query_terms), 1)

    if scene_conflict:
        return {"decision": "mismatch", "confidence": 0.85, "reason": "scene_conflict", "mode": "heuristic"}
    if coverage >= 0.58:
        return {
            "decision": "exact",
            "confidence": min(0.95, 0.55 + coverage / 2),
            "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
            "mode": "heuristic",
        }
    if coverage >= 0.34:
        return {
            "decision": "partial",
            "confidence": min(0.8, 0.35 + coverage / 2),
            "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
            "mode": "heuristic",
        }
    return {
        "decision": "mismatch",
        "confidence": max(0.55, 1 - coverage),
        "reason": f"coverage={coverage:.2f}; matched={matched[:6]}",
        "mode": "heuristic",
    }


def _parse_json_object(text: str) -> dict[str, Any] | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None


def _llm_verdict_single(
    llm: Any,
    query: str,
    row: dict[str, Any],
    primary: dict[str, Any],
    config: RunnableConfig,
) -> dict[str, Any] | None:
    if llm is None or _llm_disabled():
        return None
    prompt = (
        "Decide whether the retrieved evidence truly matches the user query.\n"
        "Be strict and conservative.\n"
        "Return JSON only with keys: decision, confidence, reason.\n"
        "decision must be one of: exact, partial, mismatch.\n"
        "- exact: the evidence directly describes the QUERIED action with matching "
        "subject, object, and scene. Synonyms count as match.\n"
        "- partial: core incident matches but details or time boundaries are coarse, "
        "or the subject/object role is slightly different.\n"
        "- mismatch: evidence is only LOOSELY related (same general scene but "
        "different action), mixes different incidents, or requires assumptions "
        "to connect to the query. Thematic similarity without the specific "
        "queried action is NOT a match.\n"
        f"\nUser query: {query}"
        f"\nTop row video: {row.get('video_id')}"
        f"\nTop row time: {row.get('start_time')} - {row.get('end_time')}"
        f"\nTop row summary: {row.get('event_summary_en') or row.get('event_text_en') or ''}"
        f"\nPrimary evidence time: {primary.get('start_time')} - {primary.get('end_time')}"
        f"\nPrimary evidence summary: {primary.get('event_summary_en') or primary.get('event_text_en') or ''}"
    )
    try:
        model = llm.bind(max_tokens=120) if hasattr(llm, "bind") else llm
        raw = model.invoke(
            [
                SystemMessage(content="You are a strict retrieval match verifier. Return JSON only."),
                HumanMessage(content=prompt),
            ],
            config=config,
        )
        content = raw.content if hasattr(raw, "content") else str(raw)
        data = _parse_json_object(str(content))
        if not isinstance(data, dict):
            return None
        decision = str(data.get("decision") or "").strip().lower()
        if decision not in _FAST_DECISIONS:
            return None
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        return {
            "decision": decision,
            "confidence": max(0.0, min(1.0, confidence)),
            "reason": str(data.get("reason") or "").strip()[:200],
            "mode": "llm",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# v2.3 multi-candidate path
# ---------------------------------------------------------------------------


def _collect_candidates(
    rerank_rows: list[dict[str, Any]],
    *,
    candidate_limit: int,
    cross_video_top_n: int,
) -> list[dict[str, Any]]:
    """Pick the candidate set the verifier LLM will inspect.

    Strategy:
      1. Take ``rerank_rows[:candidate_limit]`` as the working pool (already
         distance-/RRF-sorted upstream).
      2. Identify the top video_id (rerank top-1's video_id).
      3. ``same_video`` = all chunks from that video (preserves rerank order).
      4. ``other_video`` = top-N chunks from *other* videos (so the LLM still
         has a way out if retrieval picked the wrong video; usually small).
      5. Final order: same_video first, then other_video. ``index 0`` is the
         current rerank top-1 (used as the reference baseline).
    """
    pool = list(rerank_rows[:candidate_limit])
    if not pool:
        return []
    top_video_id = str(pool[0].get("video_id") or "").strip()
    same_video: list[dict[str, Any]] = []
    other_video: list[dict[str, Any]] = []
    for row in pool:
        if str(row.get("video_id") or "").strip() == top_video_id:
            same_video.append(row)
        else:
            other_video.append(row)
    candidates = same_video + other_video[:cross_video_top_n]
    # always keep at least the rerank top-1 as candidate index 0
    if not candidates:
        candidates = [pool[0]]
    return candidates


def _heuristic_select_best_chunk(
    query: str, candidates: list[dict[str, Any]]
) -> tuple[int, dict[str, Any]]:
    """Token-overlap heuristic: pick the candidate whose evidence covers the
    most query terms. Ties resolved by preferring the earlier (higher-rerank)
    candidate.

    Returns (best_index, verdict_dict).
    """
    query_terms = _query_terms(query)
    if not query_terms or not candidates:
        return 0, {
            "decision": "partial" if candidates else "mismatch",
            "confidence": 0.5 if candidates else 0.95,
            "reason": "empty_query_terms" if not query_terms else "no_candidates",
            "mode": "heuristic",
        }

    best_idx = 0
    best_coverage = -1.0
    best_matched: list[str] = []
    for idx, row in enumerate(candidates):
        primary = _pick_primary_row(row)
        evidence = _evidence_text(row, primary)
        matched = sorted(term for term in query_terms if term in evidence)
        coverage = len(matched) / max(len(query_terms), 1)
        if coverage > best_coverage:
            best_coverage = coverage
            best_idx = idx
            best_matched = matched

    # Decision band uses the *winning* candidate's coverage.
    if best_coverage >= 0.58:
        decision = "exact"
        confidence = min(0.95, 0.55 + best_coverage / 2)
    elif best_coverage >= 0.34:
        decision = "partial"
        confidence = min(0.8, 0.35 + best_coverage / 2)
    else:
        decision = "mismatch"
        confidence = max(0.55, 1.0 - best_coverage)

    return best_idx, {
        "decision": decision,
        "confidence": confidence,
        "reason": f"heuristic best_idx={best_idx} coverage={best_coverage:.2f} matched={best_matched[:6]}",
        "mode": "heuristic",
    }


def _has_attribute_signals(query: str) -> bool:
    """Detect whether the query contains fine-grained attribute signals
    (color, clothing, direction, absence) that event summaries may omit."""
    low = (query or "").strip().lower()
    color_words = {
        "black", "white", "red", "blue", "green", "grey", "gray",
        "brown", "beige", "khaki", "olive", "yellow", "orange", "pink",
        "dark", "light", "bright",
    }
    clothing_words = {
        "jacket", "coat", "hoodie", "shirt", "top", "trousers", "pants",
        "bag", "hat", "hood", "scarf", "jeans", "sweater", "shoes",
        "carrying", "wearing",
    }
    direction_words = {
        "exit from", "enter from", "left side", "right side",
        "up side", "down side", "top side", "bottom side",
        "bottom-left", "bottom-right", "top-left", "top-right",
    }
    absence_words = {"no bag", "not carrying", "without", "no visible"}
    tokens = set(re.findall(r"\b[a-z]+\b", low))
    has_color = bool(tokens & color_words)
    has_clothing = bool(tokens & clothing_words)
    has_direction = any(d in low for d in direction_words)
    has_absence = any(a in low for a in absence_words)
    return has_color or has_clothing or has_direction or has_absence


def _llm_select_best_chunk(
    llm: Any,
    query: str,
    candidates: list[dict[str, Any]],
    config: RunnableConfig,
) -> tuple[int, dict[str, Any]] | None:
    """Single-shot LLM call: pick the best candidate AND a verdict in one go.

    Returns (best_index, verdict_dict) or None on any LLM/parse failure
    (caller falls back to heuristic).
    """
    if llm is None or _llm_disabled() or not candidates:
        return None

    candidate_lines: list[str] = []
    for idx, row in enumerate(candidates):
        primary = _pick_primary_row(row)
        v = str(primary.get("video_id") or row.get("video_id") or "").strip()
        t1 = primary.get("start_time", row.get("start_time"))
        t2 = primary.get("end_time", row.get("end_time"))
        s = _row_summary(row, max_chars=220)
        candidate_lines.append(f"[{idx}] video={v} time={t1}-{t2} summary={s}")

    prompt_lines = [
        "You are an existence-query verifier for a video event database.",
        "",
        f"User query: {query}",
        "",
        "Below are candidate event chunks retrieved for this query (already "
        "ranked by retrieval score; index 0 is rerank top-1).",
        "Pick the SINGLE BEST chunk that most directly matches the query, "
        "and decide whether the picked chunk supports the query.",
        "",
        "Decision guide:",
        "- exact: picked chunk clearly describes the queried action with matching "
        "subject, object, and scene. Synonyms count as match.",
        "- partial: picked chunk is in the right context but details or subject "
        "roles are coarser or slightly different.",
        "- mismatch: NO chunk in the list supports the query. The evidence may "
        "be from the same general scene but describes a different action, or "
        "involves different actors/objects. Thematic similarity without the "
        "specific queried action does NOT count as a match.",
    ]

    # P1/P2: Attribute-heavy query (color/clothing/direction/absence) → relaxed prompt
    if _has_attribute_signals(query):
        prompt_lines.extend([
            "",
            "ATTRIBUTE-AWARE GUIDANCE: The query asks about specific attributes "
            "(color, clothing, spatial direction, or absence of an item). "
            "Event summaries often omit these fine-grained attributes even when "
            "the video contains them — the summary captures the general action, "
            "not every visual detail.",
            "",
            "- If a candidate chunk matches the CORRECT CAMERA and describes the "
            "same TYPE of entity/action (e.g., 'a person walks'), give at least "
            "'partial' even if the exact color/clothing/direction is not mentioned.",
            "- Camera match + entity type + action type is SUFFICIENT for partial.",
            "- If the query mentions ABSENCE ('no bag', 'without', 'not carrying'), "
            "the absence of that attribute in the summary does NOT disqualify "
            "the match — event summaries rarely describe what is NOT present.",
            "- Only choose 'mismatch' when the entity type clearly differs "
            "(e.g., car vs person) or the action contradicts the query.",
            "",
            "Be practical, not perfectionist. Camera + entity match alone is "
            "valuable evidence.",
        ])
    else:
        prompt_lines.extend([
            "",
            "CRITICAL: Be conservative. If the evidence only loosely resembles the "
            "query or requires assumptions to connect, choose mismatch. A false "
            "positive (saying a clip exists when it doesn't) is worse than a false "
            "negative. Verify that the specific action described in the query "
            "appears in the chosen chunk.",
        ])

    prompt_lines.extend([
        "",
        "CANDIDATES:",
    ])
    prompt_lines.extend(candidate_lines)
    prompt_lines.extend(
        [
            "",
            "Return JSON only:",
            "{",
            '  "best_chunk_index": <int, 0-based, in [0..n-1]>,',
            '  "decision": "exact" | "partial" | "mismatch",',
            '  "confidence": <float 0.0-1.0>,',
            '  "reason": "<one-line evidence-based>"',
            "}",
        ]
    )
    prompt = "\n".join(prompt_lines)

    try:
        model = llm.bind(max_tokens=200) if hasattr(llm, "bind") else llm
        raw = model.invoke(
            [
                SystemMessage(content="You are a video event verifier. Return JSON only."),
                HumanMessage(content=prompt),
            ],
            config=config,
        )
        content = raw.content if hasattr(raw, "content") else str(raw)
        data = _parse_json_object(str(content))
        if not isinstance(data, dict):
            return None
        try:
            best_idx = int(data.get("best_chunk_index", 0))
        except Exception:
            return None
        if best_idx < 0 or best_idx >= len(candidates):
            return None
        decision = str(data.get("decision") or "").strip().lower()
        if decision not in _FAST_DECISIONS:
            return None
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        return best_idx, {
            "decision": decision,
            "confidence": max(0.0, min(1.0, confidence)),
            "reason": str(data.get("reason") or "").strip()[:200],
            "mode": "llm",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Multi-camera verdict (v2.4)
# ---------------------------------------------------------------------------


def _detect_multi_camera_context(state: AgentState) -> bool:
    """Check whether the current query is a multi-camera scenario."""
    cr = state.get("classification_result")
    if isinstance(cr, dict):
        if cr.get("multi_camera"):
            return True
        signals = cr.get("signals")
        if isinstance(signals, dict) and signals.get("multi_camera_cues"):
            return True
    return False


def _collect_ge_rows(state: AgentState) -> list[dict[str, Any]]:
    """Gather GE rows from fusion result or global_entity_result."""
    # GE rows may be in rerank_result (post-fusion) or global_entity_result (pre-fusion).
    ge_result = state.get("global_entity_result")
    if isinstance(ge_result, list) and ge_result:
        return ge_result
    # Fallback: check rerank_result for rows with _source_type == "global_entity"
    rerank = state.get("rerank_result")
    if isinstance(rerank, list):
        return [r for r in rerank if isinstance(r, dict) and r.get("_source_type") == "global_entity"]
    return []


def _group_by_global_entity(ge_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group GE rows by global_entity_id, keeping per-camera info."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in ge_rows:
        ge_id = str(row.get("global_entity_id") or "").strip()
        if not ge_id:
            continue
        groups.setdefault(ge_id, []).append(row)
    return groups


def _multi_camera_llm_verdict(
    llm: Any,
    query: str,
    ge_groups: dict[str, list[dict[str, Any]]],
    config: RunnableConfig,
) -> dict[str, Any] | None:
    """LLM-based multi-camera verdict: does the cross-camera evidence support the query?"""
    if llm is None or _llm_disabled() or not ge_groups:
        return None

    # Build a compact summary of the multi-camera evidence
    entity_summaries: list[str] = []
    for ge_id, events in ge_groups.items():
        camera_set = sorted(set(str(e.get("camera_id") or e.get("video_id") or "").strip() for e in events))
        if len(camera_set) < 2:
            continue  # single-camera GE is not "multi-camera"
        time_ranges: list[str] = []
        for e in events[:10]:  # limit per GE
            cam = str(e.get("camera_id") or e.get("video_id") or "").strip()
            st = e.get("start_time")
            et = e.get("end_time")
            summary = (e.get("event_summary_en") or e.get("event_text_en") or "")[:120]
            time_ranges.append(f"  {cam}: {st}-{et}  {summary}")
        entity_summaries.append(
            f"Entity {ge_id} appears in cameras: {', '.join(camera_set)}\n"
            + "\n".join(time_ranges)
        )

    if not entity_summaries:
        return None  # no multi-camera groups with >=2 cameras

    prompt_lines = [
        "You are a multi-camera event verifier. The user is asking about whether a person/object "
        "appeared across multiple surveillance cameras.",
        "",
        f"User query: {query}",
        "",
        "Below is evidence from a cross-camera Global Entity retrieval. Each entity group shows "
        "which cameras captured the same tracked person/object, with time ranges.",
        "",
        "Your task: decide whether the multi-camera evidence SUPPORTS the user's query.",
        "",
        "Decision guide for multi-camera:",
        "- exact: Evidence from TWO OR MORE cameras clearly shows the queried person/object "
        "with matching characteristics (color, type, action). The cameras and times are "
        "consistent with the query intent. Synonym matching is acceptable. If the global "
        "entity appears in the right set of cameras (matching the queried camera IDs), that "
        "alone strongly supports 'exact'.",
        "- partial: Entity appears in at least two of the queried cameras but some details "
        "(color, exact action, time precision) are missing from the event summary. This is "
        "still a positive verdict — the entity IS there across cameras.",
        "- mismatch: The evidence does NOT contain any entity that appears in the queried "
        "cameras, or only one camera appears (not truly cross-camera).",
        "",
        "CRITICAL RULES:",
        "1. If a global entity appears in the same set of cameras the user asks about, "
        "the answer MUST be 'exact' or 'partial' — NOT 'mismatch'. Missing appearance "
        "descriptions do not invalidate the camera match.",
        "2. Cross-camera tracking proves the same entity moved between cameras. That IS "
        "the evidence the user is asking for. Do NOT require a perfect written description "
        "of appearance — camera coverage alone is sufficient.",
        "3. Only return 'mismatch' when NO entity appears in the queried cameras, or "
        "the evidence clearly contradicts the query.",
        "",
        "EVIDENCE:",
    ]
    prompt_lines.extend(entity_summaries)
    prompt_lines.extend(
        [
            "",
            "Return JSON only:",
            "{",
            '  "decision": "exact" | "partial" | "mismatch",',
            '  "confidence": <float 0.0-1.0>,',
            '  "reason": "<one-line evidence-based, mention which cameras and why>",',
            '  "best_global_entity_id": "<the entity id you picked>"',
            "}",
        ]
    )
    prompt = "\n".join(prompt_lines)

    try:
        model = llm.bind(max_tokens=250) if hasattr(llm, "bind") else llm
        raw = model.invoke(
            [
                SystemMessage(content="You are a multi-camera video event verifier. Return JSON only."),
                HumanMessage(content=prompt),
            ],
            config=config,
        )
        content = raw.content if hasattr(raw, "content") else str(raw)
        data = _parse_json_object(str(content))
        if not isinstance(data, dict):
            return None
        decision = str(data.get("decision") or "").strip().lower()
        if decision not in _FAST_DECISIONS:
            return None
        try:
            confidence = float(data.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        return {
            "decision": decision,
            "confidence": max(0.0, min(1.0, confidence)),
            "reason": str(data.get("reason") or "").strip()[:200],
            "mode": "llm_multi_camera",
            "best_global_entity_id": str(data.get("best_global_entity_id") or "").strip(),
        }
    except Exception:
        return None


def _multi_camera_heuristic_verdict(
    query: str,
    ge_groups: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Heuristic multi-camera verdict based on camera count and token coverage."""
    query_terms = _query_terms(query)
    best_ge_id = ""
    best_camera_count = 0
    best_coverage = 0.0
    best_matched: list[str] = []

    for ge_id, events in ge_groups.items():
        camera_set = set(str(e.get("camera_id") or e.get("video_id") or "").strip() for e in events)
        n_cameras = len(camera_set)
        evidence = " ".join(
            (e.get("event_summary_en") or e.get("event_text_en") or "") for e in events
        ).lower()
        matched = sorted(term for term in query_terms if term in evidence)
        coverage = len(matched) / max(len(query_terms), 1)
        # Prefer more cameras, then better coverage
        if n_cameras > best_camera_count or (n_cameras == best_camera_count and coverage > best_coverage):
            best_ge_id = ge_id
            best_camera_count = n_cameras
            best_coverage = coverage
            best_matched = matched

    if best_camera_count >= 2 and best_coverage >= 0.34:
        decision = "exact" if best_coverage >= 0.58 else "partial"
        confidence = min(0.95, 0.55 + best_coverage / 2)
    elif best_camera_count >= 2:
        # At least 2 cameras matched — give partial (not mismatch)
        decision = "partial"
        confidence = 0.55
    else:
        decision = "mismatch"
        confidence = max(0.55, 1.0 - best_coverage)

    return {
        "decision": decision,
        "confidence": confidence,
        "reason": f"multi_camera heuristic: cameras={best_camera_count} coverage={best_coverage:.2f} matched={best_matched[:6]}",
        "mode": "heuristic_multi_camera",
        "best_global_entity_id": best_ge_id,
    }


def _build_multi_camera_descriptor(
    ge_groups: dict[str, list[dict[str, Any]]],
    best_ge_id: str,
) -> dict[str, Any]:
    """Build the multi-camera descriptor (cameras, times, summaries) for downstream nodes."""
    events = ge_groups.get(best_ge_id, [])
    cameras: list[dict[str, Any]] = []
    camera_ids: list[str] = []
    seen_cameras: set[str] = set()
    for e in events:
        cam = str(e.get("camera_id") or e.get("video_id") or "").strip()
        if cam in seen_cameras:
            continue
        seen_cameras.add(cam)
        camera_ids.append(cam)
        cameras.append({
            "camera_id": cam,
            "start_time": e.get("start_time"),
            "end_time": e.get("end_time"),
            "summary": (e.get("event_summary_en") or e.get("event_text_en") or "")[:200],
        })
    return {
        "multi_camera": True,
        "global_entity_id": best_ge_id,
        "cameras": cameras,
        "camera_ids": camera_ids,
        "camera_count": len(camera_ids),
        "span_source": "multi_camera_ge",
    }


# ---------------------------------------------------------------------------
# Verdict shapes
# ---------------------------------------------------------------------------


def _skipped_verdict(reason: str) -> dict[str, Any]:
    return {
        "decision": "skipped",
        "confidence": 0.0,
        "reason": reason,
        "mode": "skipped",
    }


def _no_rows_verdict() -> dict[str, Any]:
    return {
        "decision": "mismatch",
        "confidence": 0.98,
        "reason": "no_rows",
        "mode": "rule",
    }


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------


def create_match_verifier_node(llm: Any = None):
    def match_verifier_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        answer_type = str(state.get("answer_type") or "").strip().lower()
        # P2-3: Run verifier for "existence" AND "unknown" (previously skipped
        # "unknown", causing 8/30 false-positive "yes" answers for queries
        # whose answer should have been "no"). When answer_type is unknown the
        # classifier could not determine the question shape, so it is safer to
        # verify existence than to skip. Only skip for non-existence types
        # where verification would be meaningless (list, count, description).
        _SKIP_ANSWER_TYPES = {"list", "count", "description"}
        if answer_type in _SKIP_ANSWER_TYPES:
            return {
                "verifier_result": _skipped_verdict(f"answer_type={answer_type}"),
                "current_node": "match_verifier_node",
            }

        query = str(state.get("original_user_query") or state.get("user_query") or "").strip()

        # ── v2.4: Multi-camera path ──
        is_multi_camera = _detect_multi_camera_context(state)
        if is_multi_camera:
            ge_rows = _collect_ge_rows(state)
            ge_groups = _group_by_global_entity(ge_rows)
            if ge_groups:
                # Check if any group has >=2 cameras (true multi-camera)
                has_multi = any(
                    len(set(
                        str(e.get("camera_id") or e.get("video_id") or "").strip()
                        for e in events
                    )) >= 2
                    for events in ge_groups.values()
                )
                if has_multi:
                    mc_llm = _multi_camera_llm_verdict(llm, query, ge_groups, config)
                    if mc_llm is not None:
                        verdict = mc_llm
                    else:
                        verdict = _multi_camera_heuristic_verdict(query, ge_groups)
                    best_ge_id = verdict.get("best_global_entity_id", "")
                    mc_descriptor = _build_multi_camera_descriptor(ge_groups, best_ge_id)
                    return {
                        "verifier_result": {
                            **verdict,
                            **mc_descriptor,
                            "best_chunk_index": 0,
                            "candidate_count": sum(len(v) for v in ge_groups.values()),
                        },
                        "current_node": "match_verifier_node",
                    }

        # ── Existing single-camera paths ──
        rows = _select_rows(state)
        if not rows:
            return {
                "verifier_result": _no_rows_verdict(),
                "current_node": "match_verifier_node",
            }

        # Legacy single-row path (escape hatch)
        if not _reselect_span_enabled():
            top_row = rows[0]
            primary = _pick_primary_row(top_row)
            verdict = _llm_verdict_single(llm, query, top_row, primary, config) or _heuristic_verdict_single(
                query, top_row, primary
            )
            descriptor = _row_descriptor(top_row)
            return {
                "verifier_result": {
                    **verdict,
                    **descriptor,
                    "span_source": "candidate_top_row",
                    "best_chunk_index": 0,
                    "candidate_count": 1,
                },
                "current_node": "match_verifier_node",
            }

        # v2.3 multi-candidate path
        candidates = _collect_candidates(
            rows,
            candidate_limit=_candidate_limit(),
            cross_video_top_n=_cross_video_top_n(),
        )
        llm_pick = _llm_select_best_chunk(llm, query, candidates, config)
        if llm_pick is not None:
            best_idx, verdict = llm_pick
        else:
            best_idx, verdict = _heuristic_select_best_chunk(query, candidates)

        # Guard against pathological out-of-range; should never trigger because
        # both helpers clamp inside [0, len(candidates)-1].
        if best_idx < 0 or best_idx >= len(candidates):
            best_idx = 0

        chosen_row = candidates[best_idx]
        descriptor = _row_descriptor(chosen_row)
        # span_source is "rerank_reselected" only when the LLM/heuristic chose
        # something other than the rerank top-1; otherwise the rerank top-1
        # already won, so downstream behaviour is unchanged.
        span_source = "candidate_top_row" if best_idx == 0 else "rerank_reselected"

        return {
            "verifier_result": {
                **verdict,
                **descriptor,
                "span_source": span_source,
                "best_chunk_index": best_idx,
                "candidate_count": len(candidates),
            },
            "current_node": "match_verifier_node",
        }

    return match_verifier_node
