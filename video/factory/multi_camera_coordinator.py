"""Multi-camera cross-view orchestration: per-camera track → crops+Re-ID → match → merge."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from video.common.frames import PersonCrop, extract_person_crops
from video.core.models.reid_embedder import ReIDEmbedder
from video.core.schema.multi_camera import (
    CameraResult,
    CrossCameraConfig,
    GlobalEntity,
    MultiCameraOutput,
)
from video.factory.processors.analyzer import aggregate_tracks, slice_events
from video.factory.processors.cross_camera_matcher import match_across_cameras
from video.factory.processors.vision import resolve_model, run_yolo_track_on_video

logger = logging.getLogger(__name__)


def _should_use_multicam_llm_verify(
    use_llm_verify: bool | None,
    llm_base_url: str | None,
) -> bool:
    """Whether to run borderline cosine VLM checks (``verify_person_match_with_llm``).

    * ``use_llm_verify=True`` / ``False`` — explicit on/off.
    * ``use_llm_verify=None`` — auto: on if ``llm_base_url`` or env
      ``VLLM_OPENAI_BASE_URL`` / ``OPENAI_BASE_URL`` is set, or env
      ``MULTICAM_USE_VLLM_VERIFY`` is truthy (``1``, ``true``, ``yes``, ``on``).
    """
    if use_llm_verify is not None:
        return bool(use_llm_verify)
    base = (
        llm_base_url
        or os.getenv("VLLM_OPENAI_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_URL")
    )
    if base:
        return True
    flag = os.getenv("MULTICAM_USE_VLLM_VERIFY", "").strip().lower()
    return flag in ("1", "true", "yes", "on")


def _same_camera_gap_sec(a: dict[str, Any], b: dict[str, Any]) -> float:
    a_s, a_e = float(a["start_time"]), float(a["end_time"])
    b_s, b_e = float(b["start_time"]), float(b["end_time"])
    if min(a_e, b_e) >= max(a_s, b_s):
        return 0.0
    return min(abs(b_s - a_e), abs(a_s - b_e))


def _stitch_same_camera_fragments(
    camera_result: CameraResult,
    config: CrossCameraConfig,
) -> None:
    """
    Same-camera rules:
    - Same track_id is one target (native tracker semantics).
    - For different person track_ids with small gap, stitch with Re-ID if sim >= threshold.
    """
    person_tracks = [t for t in camera_result.tracks if t.get("class_name") == "person"]
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(len(person_tracks)):
        for j in range(i + 1, len(person_tracks)):
            a, b = person_tracks[i], person_tracks[j]
            a_tid, b_tid = int(a["track_id"]), int(b["track_id"])
            if a_tid == b_tid:
                continue
            gap = _same_camera_gap_sec(a, b)
            if gap > config.same_camera_max_gap_sec:
                continue
            emb_a = camera_result.person_embeddings.get(a_tid)
            emb_b = camera_result.person_embeddings.get(b_tid)
            if emb_a is None or emb_b is None:
                continue
            sim = float(emb_a @ emb_b)
            if sim >= config.same_camera_reid_threshold:
                union(a_tid, b_tid)

    if not parent:
        return

    tid_map: dict[int, int] = {}
    for t in person_tracks:
        tid = int(t["track_id"])
        tid_map[tid] = find(tid) if tid in parent else tid

    # Rewrite track_id in tracks/events to canonical root id.
    for t in camera_result.tracks:
        tid = int(t["track_id"])
        t["track_id"] = tid_map.get(tid, tid)
    for e in camera_result.events:
        tid = e.get("track_id")
        if tid is None:
            continue
        e["track_id"] = tid_map.get(int(tid), int(tid))

    # Merge embeddings and crops by canonical tid.
    merged_emb: dict[int, list[np.ndarray]] = {}
    for tid, emb in camera_result.person_embeddings.items():
        root = tid_map.get(int(tid), int(tid))
        merged_emb.setdefault(root, []).append(emb)
    camera_result.person_embeddings = {}
    for root, embs in merged_emb.items():
        v = np.mean(np.stack(embs, axis=0), axis=0)
        n = np.linalg.norm(v)
        camera_result.person_embeddings[root] = v / n if n > 0 else v

    merged_crops: dict[int, list[PersonCrop]] = {}
    for tid, crops in camera_result.person_crops.items():
        root = tid_map.get(int(tid), int(tid))
        merged_crops.setdefault(root, []).extend(crops)
    camera_result.person_crops = merged_crops


def _load_config_yaml(path: str | Path) -> CrossCameraConfig:
    """Load CrossCameraConfig fields from a YAML file."""
    import yaml

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return CrossCameraConfig(**{
        k: v for k, v in data.items()
        if k in CrossCameraConfig.__dataclass_fields__
    })


def _process_single_camera(
    camera_id: str,
    video_path: str,
    embedder: ReIDEmbedder,
    num_crops: int = 5,
    **pipeline_kwargs: Any,
) -> CameraResult:
    """Stage-1: detect+track one stream, extract person crops and Re-ID embeddings.

    Uses vision/analyzer primitives; one track pass yields tracks and events.
    """
    model_path = pipeline_kwargs.get("model_path", "n")
    model_resolved, _ = resolve_model(model_path)
    fps, total_frames, frame_detections, tracker_label = run_yolo_track_on_video(
        video_path,
        model_path=model_resolved,
        conf=pipeline_kwargs.get("conf", 0.25),
        iou=pipeline_kwargs.get("iou", 0.45),
        tracker=pipeline_kwargs.get("tracker", "botsort_reid"),
    )
    all_tracks = aggregate_tracks(fps, frame_detections)
    events, clips = slice_events(
        all_tracks, fps, frame_detections,
        motion_threshold=pipeline_kwargs.get("motion_threshold", 5.0),
        min_clip_duration=pipeline_kwargs.get("min_clip_duration", 1.0),
        max_static_duration=pipeline_kwargs.get("max_static_duration", 30.0),
    )

    meta: dict[str, Any] = {
        "video_path": str(Path(video_path).resolve()),
        "fps": fps,
        "total_frames": total_frames,
        "num_tracks": len(all_tracks),
        "num_events": len(events),
        "num_clips": len(clips),
        "tracker": tracker_label,
        "model": model_resolved,
        "camera_id": camera_id,
    }
    for ev in events:
        ev["camera_id"] = camera_id

    person_crops: dict[int, list[PersonCrop]] = {}
    person_embeddings: dict[int, np.ndarray] = {}

    for t in all_tracks:
        if t.get("class_name") != "person":
            continue
        tid = t["track_id"]
        crops = extract_person_crops(video_path, t, camera_id=camera_id, num_crops=num_crops)
        if crops:
            person_crops[tid] = crops
            imgs = [c.image_array for c in crops]
            emb = embedder.embed_crops(imgs)
            person_embeddings[tid] = emb.mean(axis=0)
            norm = np.linalg.norm(person_embeddings[tid])
            if norm > 0:
                person_embeddings[tid] /= norm

    result = CameraResult(
        camera_id=camera_id,
        video_path=video_path,
        tracks=all_tracks,
        events=events,
        clips=clips,
        meta=meta,
        person_crops=person_crops,
        person_embeddings=person_embeddings,
    )
    return result


def run_multi_camera_pipeline(
    camera_videos: dict[str, str],
    config: CrossCameraConfig | None = None,
    embedder: ReIDEmbedder | None = None,
    reid_config_file: str | None = None,
    reid_weights: str | None = None,
    reid_device: str = "cpu",
    num_crops: int = 5,
    use_llm_verify: bool | None = None,
    llm_model: str = "gpt-4o-mini",
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
    topology_prior_path: str | None = None,
    seed_topology_campus_guide_v2: bool = False,
    campus_logical_to_physical: dict[str, str] | None = None,
    **pipeline_kwargs: Any,
) -> MultiCameraOutput:
    """Main entry for multi-camera cross-view tracking.

    Args:
        camera_videos: {"cam1": "/path/cam1.mp4", "cam2": "/path/cam2.mp4", ...}
        config: Cross-camera hyperparameters; defaults if None.
        embedder: Re-ID model; created from reid_* if None.
        topology_prior_path: Path to a saved :class:`CameraTopologyPrior` JSON.
            If the file exists it is loaded; if None a fresh prior is initialised
            from the camera list and updated online during this run.
        use_llm_verify: Borderline-pair VLM verification (same person?). ``None``
            (default) enables verification automatically when ``llm_base_url`` or
            ``OPENAI_BASE_URL`` / ``VLLM_OPENAI_BASE_URL`` is set (typical **vLLM**
            deployment); set ``False`` to disable.
        llm_base_url / llm_api_key: Optional overrides for OpenAI-compatible /
            **vLLM** endpoints (else env ``OPENAI_BASE_URL``, keys per
            ``verify_person_match_with_llm``).
        llm_model: VLM name served by vLLM / OpenAI; env ``MULTICAM_VLLM_MODEL``
            overrides when set.
        seed_topology_campus_guide_v2: If True (and no saved prior was loaded),
            initialise the prior from the Campus Zone Map guide (ADMIN / BUS /
            SCHOOL zones and walking-time windows). Camera keys should be physical
            IDs (``G326``, …) or use ``campus_logical_to_physical``.
        campus_logical_to_physical: Optional map from pipeline camera id to
            physical camera code for zone lookup when seeding the campus guide.
    """
    from video.core.models.camera_topology import CameraTopologyPrior

    if config is None:
        config = CrossCameraConfig()
    if embedder is None:
        embedder = ReIDEmbedder(
            config_file=reid_config_file,
            weights=reid_weights,
            device=reid_device,
        )

    # Load or initialise topology prior
    camera_ids = list(camera_videos.keys())
    max_topo_sec = config.max_transition_sec * 10
    if topology_prior_path and Path(topology_prior_path).exists():
        topology_prior = CameraTopologyPrior.load(topology_prior_path)
        logger.info("Loaded topology prior from %s", topology_prior_path)
    elif seed_topology_campus_guide_v2:
        topology_prior = CameraTopologyPrior.from_campus_guide_v2(
            cameras=camera_ids,
            logical_to_physical=campus_logical_to_physical,
            max_transit_sec=max_topo_sec,
        )
        logger.info(
            "Initialised topology prior from campus zone map guide v2.0: %s",
            camera_ids,
        )
    else:
        topology_prior = CameraTopologyPrior(
            cameras=camera_ids,
            max_transit_sec=max_topo_sec,  # generous upper bound
        )
        logger.info(
            "Initialised fresh topology prior for cameras: %s", camera_ids
        )

    # Stage 1: per camera
    per_camera: list[CameraResult] = []
    for cam_id, vpath in camera_videos.items():
        logger.info("Processing camera %s: %s", cam_id, vpath)
        result = _process_single_camera(
            cam_id, vpath, embedder, num_crops=num_crops, **pipeline_kwargs,
        )
        _stitch_same_camera_fragments(result, config)
        per_camera.append(result)

    # Stage 2: cross-camera match (with topology prior + optional vLLM borderline verify)
    llm_verify_fn = None
    effective_llm_model = os.getenv("MULTICAM_VLLM_MODEL") or llm_model
    if _should_use_multicam_llm_verify(use_llm_verify, llm_base_url):
        from functools import partial

        from video.core.models.event_refinement_llm import verify_person_match_with_llm

        llm_verify_fn = partial(
            verify_person_match_with_llm,
            model=effective_llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        logger.info(
            "Cross-camera borderline VLM verification enabled (model=%s)",
            effective_llm_model,
        )

    global_entities = match_across_cameras(
        per_camera, config, embedder, llm_verify_fn,
        topology_prior=topology_prior,
    )

    # Persist updated topology prior for future runs
    if topology_prior_path:
        topology_prior.save(topology_prior_path)
        logger.info("Topology prior persisted to %s", topology_prior_path)

    # Stage 3: merge events
    entity_lookup = _build_entity_lookup(global_entities)
    merged_events = _merge_events(per_camera, entity_lookup)

    return MultiCameraOutput(
        cameras=dict(camera_videos),
        config=config,
        global_entities=global_entities,
        per_camera=per_camera,
        merged_events=merged_events,
    )


def _build_entity_lookup(
    entities: list[GlobalEntity],
) -> dict[tuple[str, int], str]:
    """Map (camera_id, track_id) → global_entity_id."""
    lookup: dict[tuple[str, int], str] = {}
    for ent in entities:
        for app in ent.appearances:
            lookup[(app.camera_id, app.track_id)] = ent.global_entity_id
    return lookup


def _merge_events(
    per_camera: list[CameraResult],
    entity_lookup: dict[tuple[str, int], str],
) -> list[dict[str, Any]]:
    """Merge events from all cameras; add global_entity_id when matched."""
    merged: list[dict[str, Any]] = []
    for cam in per_camera:
        for ev in cam.events:
            ev_copy = dict(ev)
            ev_copy.setdefault("camera_id", cam.camera_id)
            tid = ev.get("track_id")
            if tid is not None:
                key = (cam.camera_id, tid)
                gid = entity_lookup.get(key)
                if gid is not None:
                    ev_copy["global_entity_id"] = gid
            merged.append(ev_copy)
    merged.sort(key=lambda e: e.get("start_time", 0.0))
    return merged


# ------------------------------------------------------------------
# JSON serialization
# ------------------------------------------------------------------

def multi_camera_output_to_dict(output: MultiCameraOutput) -> dict[str, Any]:
    """Serialize MultiCameraOutput to a JSON-compatible dict."""
    return {
        "meta": {
            "cameras": output.cameras,
            "cross_camera_config": asdict(output.config),
        },
        "global_entities": [
            {
                "global_entity_id": ent.global_entity_id,
                "appearances": [asdict(a) for a in ent.appearances],
            }
            for ent in output.global_entities
        ],
        "events": output.merged_events,
    }


def save_multi_camera_output(
    output: MultiCameraOutput,
    out_path: str | Path,
) -> Path:
    """Write multi-camera result to a JSON file."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = multi_camera_output_to_dict(output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("Multi-camera output saved to %s", out_path)
    return out_path
