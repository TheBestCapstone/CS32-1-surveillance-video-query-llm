"""跨摄像头人物匹配：时间过滤 → Re-ID embedding 召回 → 匈牙利算法全局分配。"""

from __future__ import annotations

import itertools
import logging
from typing import TYPE_CHECKING, Any, Callable

import numpy as np

from video.core.schema.multi_camera import (
    CameraAppearance,
    CameraResult,
    CrossCameraConfig,
    GlobalEntity,
    MatchVerification,
)

if TYPE_CHECKING:
    from video.core.models.reid_embedder import ReIDEmbedder

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Time constraint helpers
# ------------------------------------------------------------------

def _time_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """两段时间区间的重叠长度（秒），无重叠返回 0。"""
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _time_gap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """两段时间区间之间的间隔（秒），重叠时返回 0。"""
    if _time_overlap(a_start, a_end, b_start, b_end) > 0:
        return 0.0
    return min(abs(b_start - a_end), abs(a_start - b_end))


def passes_time_constraint(
    track_a: dict[str, Any],
    track_b: dict[str, Any],
    config: CrossCameraConfig,
) -> bool:
    """根据 max_transition_sec / min_overlap_sec 判断两条轨迹是否满足时间约束。"""
    a_s, a_e = track_a["start_time"], track_a["end_time"]
    b_s, b_e = track_b["start_time"], track_b["end_time"]

    overlap = _time_overlap(a_s, a_e, b_s, b_e)
    if overlap > 0:
        return overlap >= config.min_overlap_sec

    gap = _time_gap(a_s, a_e, b_s, b_e)
    return gap <= config.max_transition_sec


# ------------------------------------------------------------------
# Candidate pair generation
# ------------------------------------------------------------------

def _person_tracks(cam: CameraResult) -> list[dict[str, Any]]:
    return [t for t in cam.tracks if t.get("class_name") == "person"]


def build_candidate_pairs(
    per_camera: list[CameraResult],
    config: CrossCameraConfig,
) -> list[tuple[CameraResult, dict[str, Any], CameraResult, dict[str, Any]]]:
    """枚举所有通过时间约束的跨摄像头 (person) 轨迹对。"""
    pairs: list[tuple[CameraResult, dict, CameraResult, dict]] = []
    for cam_i, cam_j in itertools.combinations(per_camera, 2):
        tracks_i = _person_tracks(cam_i) if config.person_only else cam_i.tracks
        tracks_j = _person_tracks(cam_j) if config.person_only else cam_j.tracks
        for ti in tracks_i:
            for tj in tracks_j:
                if passes_time_constraint(ti, tj, config):
                    pairs.append((cam_i, ti, cam_j, tj))
    return pairs


# ------------------------------------------------------------------
# Similarity scoring
# ------------------------------------------------------------------

def score_candidate_pairs(
    pairs: list[tuple[CameraResult, dict, CameraResult, dict]],
    embedder: ReIDEmbedder,
    config: CrossCameraConfig,
) -> list[tuple[CameraResult, dict, CameraResult, dict, float]]:
    """跨摄综合评分：0.7*cosine + 0.3*time_window_score。"""
    def _time_window_score(gap_sec: float) -> float:
        if gap_sec <= 30.0:
            return 1.0
        if gap_sec <= 120.0:
            return 0.7
        if gap_sec <= 300.0:
            return 0.3
        return 0.0

    scored: list[tuple[CameraResult, dict, CameraResult, dict, float]] = []
    for cam_i, ti, cam_j, tj in pairs:
        emb_i = cam_i.person_embeddings.get(ti["track_id"])
        emb_j = cam_j.person_embeddings.get(tj["track_id"])
        if emb_i is None or emb_j is None:
            continue
        cosine = float(emb_i @ emb_j)
        gap = _time_gap(float(ti["start_time"]), float(ti["end_time"]), float(tj["start_time"]), float(tj["end_time"]))
        tw = _time_window_score(gap)
        score = 0.7 * cosine + 0.3 * tw
        scored.append((cam_i, ti, cam_j, tj, score))
    scored.sort(key=lambda x: x[4], reverse=True)
    return scored


# ------------------------------------------------------------------
# Global assignment (greedy or Hungarian)
# ------------------------------------------------------------------

def _greedy_assign(
    scored: list[tuple[CameraResult, dict, CameraResult, dict, float]],
    threshold: float,
) -> list[tuple[str, int, str, int, float]]:
    """多路合并分配：收集所有超过阈值的配对，送入后续 Union-Find 合并。

    与原贪心方式的区别：不再限制每条轨迹只能配一次。
    这样当同一人同时出现在 3 个（或更多）摄像头时，
    cam1↔cam2、cam1↔cam3、cam2↔cam3 三对都会被保留，
    Union-Find 会把它们合并为同一个 GlobalEntity。

    同一摄像头对（cam_a, cam_b）内，同一条轨迹仍只取最高分的那一对，
    避免在同一组摄像头内产生一对多的错误匹配。

    返回 list of (cam_id_a, track_id_a, cam_id_b, track_id_b, score)。
    """
    # best_for_cam_pair[(cam_a, tid_a, cam_b)] = 当前最优 (tid_b, score)
    # 保证同一摄像头对内每条轨迹只配最佳对手
    best: dict[tuple[str, int, str], tuple[int, float]] = {}
    for cam_i, ti, cam_j, tj, score in scored:
        if score < threshold:
            break
        cid_i, tid_i = cam_i.camera_id, ti["track_id"]
        cid_j, tid_j = cam_j.camera_id, tj["track_id"]
        key_ij = (cid_i, tid_i, cid_j)
        key_ji = (cid_j, tid_j, cid_i)
        prev_ij = best.get(key_ij)
        if prev_ij is None or score > prev_ij[1]:
            best[key_ij] = (tid_j, score)
        prev_ji = best.get(key_ji)
        if prev_ji is None or score > prev_ji[1]:
            best[key_ji] = (tid_i, score)

    # 去重：(cam_a, tid_a, cam_b, tid_b) 与 (cam_b, tid_b, cam_a, tid_a) 是同一对
    seen: set[frozenset[tuple[str, int]]] = set()
    assignments: list[tuple[str, int, str, int, float]] = []
    for (cid_a, tid_a, cid_b), (tid_b, score) in best.items():
        pair_key = frozenset([(cid_a, tid_a), (cid_b, tid_b)])
        if pair_key in seen:
            continue
        seen.add(pair_key)
        assignments.append((cid_a, tid_a, cid_b, tid_b, score))
    return assignments


def _build_global_entities(
    assignments: list[tuple[str, int, str, int, float]],
    per_camera: list[CameraResult],
) -> list[GlobalEntity]:
    """将两两配对结果合并成全局实体（Union-Find）。"""
    parent: dict[tuple[str, int], tuple[str, int]] = {}

    def find(x: tuple[str, int]) -> tuple[str, int]:
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a: tuple[str, int], b: tuple[str, int]) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for cam_a, tid_a, cam_b, tid_b, _ in assignments:
        union((cam_a, tid_a), (cam_b, tid_b))

    track_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for cam in per_camera:
        for t in cam.tracks:
            track_lookup[(cam.camera_id, t["track_id"])] = t

    confidence_map: dict[tuple[str, int, str, int], float] = {}
    for cam_a, tid_a, cam_b, tid_b, score in assignments:
        confidence_map[(cam_a, tid_a, cam_b, tid_b)] = score

    groups: dict[tuple[str, int], list[tuple[str, int]]] = {}
    all_keys = set()
    for cam_a, tid_a, cam_b, tid_b, _ in assignments:
        all_keys.add((cam_a, tid_a))
        all_keys.add((cam_b, tid_b))
    for k in all_keys:
        root = find(k)
        groups.setdefault(root, []).append(k)

    entities: list[GlobalEntity] = []
    for idx, (_, members) in enumerate(sorted(groups.items()), start=1):
        appearances: list[CameraAppearance] = []
        for cam_id, tid in members:
            t = track_lookup.get((cam_id, tid))
            if t is None:
                continue
            conf_vals = [
                v for (a, ta, b, tb), v in confidence_map.items()
                if (a == cam_id and ta == tid) or (b == cam_id and tb == tid)
            ]
            appearances.append(CameraAppearance(
                camera_id=cam_id,
                track_id=tid,
                start_time=t["start_time"],
                end_time=t["end_time"],
                confidence=max(conf_vals) if conf_vals else 0.0,
            ))
        appearances.sort(key=lambda a: a.start_time)
        entities.append(GlobalEntity(
            global_entity_id=f"person_global_{idx}",
            appearances=appearances,
        ))
    return entities


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def match_across_cameras(
    per_camera: list[CameraResult],
    config: CrossCameraConfig,
    embedder: ReIDEmbedder,
    llm_verify_fn: Callable[..., MatchVerification] | None = None,
) -> list[GlobalEntity]:
    """跨摄像头匹配主函数。

    1. 枚举通过时间约束的候选对
    2. Re-ID 余弦相似度打分
    3. (可选) top-K 送 LLM 二次确认
    4. 贪心全局分配 → 合并为 GlobalEntity
    """
    pairs = build_candidate_pairs(per_camera, config)
    logger.info("候选对数: %d (时间过滤后)", len(pairs))

    scored = score_candidate_pairs(pairs, embedder, config)
    logger.info("有效得分对数: %d", len(scored))

    if llm_verify_fn is not None and config.llm_verify_top_k > 0:
        # 仅对边界 case 触发 VLM：cosine in [min,max]
        border_cases: list[tuple[CameraResult, dict, CameraResult, dict, float]] = []
        for item in scored:
            cam_i, ti, cam_j, tj, score = item
            emb_i = cam_i.person_embeddings.get(ti["track_id"])
            emb_j = cam_j.person_embeddings.get(tj["track_id"])
            if emb_i is None or emb_j is None:
                continue
            cosine = float(emb_i @ emb_j)
            if config.llm_verify_cosine_min <= cosine <= config.llm_verify_cosine_max:
                border_cases.append(item)
        top_k = border_cases[: config.llm_verify_top_k]
        verified: list[tuple[CameraResult, dict, CameraResult, dict, float]] = []
        for cam_i, ti, cam_j, tj, sim in top_k:
            crops_i = cam_i.person_crops.get(ti["track_id"], [])
            crops_j = cam_j.person_crops.get(tj["track_id"], [])
            if not crops_i or not crops_j:
                verified.append((cam_i, ti, cam_j, tj, sim))
                continue
            result: MatchVerification = llm_verify_fn(crops_i[0], crops_j[0])
            if result.is_match:
                boosted = min(1.0, sim * 0.7 + result.confidence * 0.3)
                verified.append((cam_i, ti, cam_j, tj, boosted))
            else:
                logger.info(
                    "LLM rejected: cam=%s tid=%d ↔ cam=%s tid=%d (%s)",
                    cam_i.camera_id, ti["track_id"],
                    cam_j.camera_id, tj["track_id"],
                    result.reasoning,
                )
        verified_keys = {(c1.camera_id, t1["track_id"], c2.camera_id, t2["track_id"]) for c1, t1, c2, t2, _ in top_k}
        remaining = [
            x for x in scored
            if (x[0].camera_id, x[1]["track_id"], x[2].camera_id, x[3]["track_id"]) not in verified_keys
        ]
        scored = sorted(verified + remaining, key=lambda x: x[4], reverse=True)

    assignments = _greedy_assign(scored, config.cross_camera_min_score)
    logger.info("匹配分配数: %d", len(assignments))

    return _build_global_entities(assignments, per_camera)
