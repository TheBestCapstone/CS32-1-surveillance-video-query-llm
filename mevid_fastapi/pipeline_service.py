"""Video pipeline service — wraps multi-camera coordinator and DB builders."""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_AGENT_ROOT = _PROJECT_ROOT / "agent"
for _p in (str(_PROJECT_ROOT), str(_AGENT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def ingest_from_seeds(
    seeds_dir: str,
    namespace: str,
    output_base: str,
    reset_existing: bool = True,
) -> dict[str, Any]:
    """Build SQLite + Chroma databases from pre-generated events_vector_flat files.

    Args:
        seeds_dir: Directory containing *_events_vector_flat.json files.
        namespace: Chroma collection namespace prefix.
        output_base: Directory where sqlite / chroma will be written.
        reset_existing: Whether to drop and recreate existing collections.

    Returns:
        Dict with sqlite_path, chroma_path, counts, elapsed_ms.
    """
    from agent.db.chroma_builder import ChromaBuildConfig, ChromaIndexBuilder
    from agent.db.sqlite_builder import SQLiteBuildConfig, SQLiteDatabaseBuilder
    from agent.db.config import (
        CHROMA_CHILD_SUFFIX,
        CHROMA_EVENT_SUFFIX,
        CHROMA_PARENT_SUFFIX,
    )

    t0 = time.perf_counter()
    seeds_path = Path(seeds_dir)
    seed_files = sorted(seeds_path.glob("*_events_vector_flat.json"))
    if not seed_files:
        raise ValueError(f"seeds_dir '{seeds_dir}' 中没有找到 *_events_vector_flat.json 文件")

    out_dir = Path(output_base)
    out_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = out_dir / "episodic_events.sqlite"
    chroma_path = out_dir / "chroma"

    child_col = f"{namespace}_{CHROMA_CHILD_SUFFIX}"
    parent_col = f"{namespace}_{CHROMA_PARENT_SUFFIX}"
    event_col = f"{namespace}_{CHROMA_EVENT_SUFFIX}"

    sqlite_result = SQLiteDatabaseBuilder(
        SQLiteBuildConfig(
            db_path=sqlite_path,
            reset_existing=reset_existing,
            generate_init_prompt=False,
        )
    ).build(seed_files=seed_files)

    chroma_result = ChromaIndexBuilder(
        ChromaBuildConfig(
            chroma_path=chroma_path,
            child_collection=child_col,
            parent_collection=parent_col,
            event_collection=event_col,
            reset_existing=reset_existing,
        )
    ).build(seed_files=seed_files)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "status": "ok",
        "namespace": namespace,
        "sqlite_path": str(sqlite_path),
        "chroma_path": str(chroma_path),
        "seed_file_count": len(seed_files),
        "sqlite_rows": sqlite_result.get("inserted_rows", 0),
        "chroma_child_records": chroma_result.get("child_record_count", 0),
        "chroma_ge_records": chroma_result.get("global_entity_record_count", 0),
        "elapsed_ms": elapsed_ms,
    }


def ingest_from_videos(
    camera_videos: dict[str, str],
    namespace: str,
    output_base: str,
    conf: float = 0.40,
    iou: float = 0.40,
    reid_device: str = "cpu",
    refine: bool = False,
    refine_model: str = "qwen-vl-max",
    reset_existing: bool = True,
) -> dict[str, Any]:
    """Run full multi-camera pipeline and build databases.

    Args:
        camera_videos: {"G329": "/path/to/G329.avi", ...}
        namespace: Chroma collection namespace prefix.
        output_base: Directory for pipeline cache, seeds, sqlite, chroma.
        conf: YOLO detection confidence threshold.
        iou: YOLO tracking IoU threshold.
        reid_device: Device for OSNet Re-ID embedder.
        refine: Whether to run LLM event refinement (Phase 5).
        refine_model: LLM model name for refinement.
        reset_existing: Whether to reset existing DB.

    Returns:
        Same shape as ingest_from_seeds plus pipeline_cache_path.
    """
    import json
    from video.factory.multi_camera_coordinator import (
        run_multi_camera_pipeline,
        multi_camera_output_to_dict,
    )
    from video.core.schema.multi_camera import CrossCameraConfig

    t0 = time.perf_counter()
    out_dir = Path(output_base)
    cache_dir = out_dir / "pipeline_cache"
    seeds_dir = out_dir / "seeds"
    cache_dir.mkdir(parents=True, exist_ok=True)
    seeds_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1-4: multi-camera pipeline
    config = CrossCameraConfig(
        conf=conf,
        iou=iou,
        embedding_threshold=0.63,
        cross_camera_min_score=0.58,
    )
    pipeline_output = run_multi_camera_pipeline(
        camera_videos=camera_videos,
        config=config,
        reid_device=reid_device,
    )
    pipeline_dict = multi_camera_output_to_dict(pipeline_output)
    cache_file = cache_dir / "pipeline_output.json"
    cache_file.write_text(
        json.dumps(pipeline_dict, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Stage 5 (optional): LLM refinement
    if refine:
        from video.factory.refinement_runner import refine_multi_camera_output, RefineEventsConfig
        pipeline_output = refine_multi_camera_output(
            pipeline_output,
            config=RefineEventsConfig(mode="vector", model=refine_model),
        )
        pipeline_dict = multi_camera_output_to_dict(pipeline_output)
        (cache_dir / "pipeline_refined.json").write_text(
            json.dumps(pipeline_dict, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # Convert pipeline output → events_vector_flat seeds
    seed_files = _pipeline_output_to_seeds(pipeline_output, pipeline_dict, seeds_dir, namespace)

    # Build DB
    db_result = ingest_from_seeds(
        seeds_dir=str(seeds_dir),
        namespace=namespace,
        output_base=str(out_dir / "runtime"),
        reset_existing=reset_existing,
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
    return {**db_result, "pipeline_cache_path": str(cache_file), "elapsed_ms": elapsed_ms}


def _pipeline_output_to_seeds(
    pipeline_output: Any,
    pipeline_dict: dict[str, Any],
    seeds_dir: Path,
    namespace: str,
) -> list[Path]:
    """Convert MultiCameraOutput → per-camera events_vector_flat.json seed files."""
    import json

    global_entities: list[dict] = pipeline_dict.get("global_entities") or []
    ge_lookup: dict[str, dict] = {ge["global_entity_id"]: ge for ge in global_entities if ge.get("global_entity_id")}

    per_camera: list[dict] = pipeline_dict.get("per_camera") or []
    merged_events: list[dict] = pipeline_dict.get("merged_events") or []

    # Group merged events by camera
    cam_events: dict[str, list[dict]] = {}
    for ev in merged_events:
        cam = str(ev.get("camera_id") or "").strip()
        if cam:
            cam_events.setdefault(cam, []).append(ev)

    # Get cameras list from pipeline output
    cameras: dict[str, str] = pipeline_dict.get("cameras") or {}

    seed_paths: list[Path] = []
    for cam_id, video_path in cameras.items():
        video_id = Path(video_path).name
        events_for_cam = cam_events.get(cam_id, [])

        flat_events: list[dict] = []
        for ev in events_for_cam:
            entity_hint = str(ev.get("global_entity_id") or ev.get("track_id") or "").strip()
            ge = ge_lookup.get(entity_hint, {})
            ge_camera_ids = ge.get("camera_ids") or []
            cross_camera_ids = [c for c in ge_camera_ids if c != cam_id] if ge_camera_ids else []

            flat_ev = {
                "video_id": video_id,
                "camera_id": cam_id,
                "track_id": str(ev.get("track_id") or ""),
                "entity_hint": entity_hint,
                "start_time": ev.get("start_time"),
                "end_time": ev.get("end_time"),
                "clip_start_sec": ev.get("start_time"),
                "clip_end_sec": ev.get("end_time"),
                "object_type": str(ev.get("class_name") or "person").lower(),
                "object_color": str(ge.get("object_color") or ""),
                "object_color_en": str(ge.get("object_color") or ""),
                "scene_zone_en": str(ev.get("scene_zone") or ""),
                "event_type": str(ev.get("event_type") or ""),
                "appearance_notes": str(ge.get("appearance_notes") or ""),
                "appearance_notes_en": str(ge.get("appearance_notes") or ""),
                "event_text_en": str(ev.get("description_for_llm") or ev.get("event_text") or ""),
                "event_summary_en": str(ev.get("description_for_llm") or ""),
                "keywords": ge.get("keywords") or [],
                "cross_camera_ids": cross_camera_ids,
            }
            flat_events.append(flat_ev)

        safe_name = f"{namespace}_{cam_id}_events_vector_flat.json"
        seed_path = seeds_dir / safe_name
        seed_path.write_text(
            json.dumps({"video_id": video_id, "events": flat_events}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        seed_paths.append(seed_path)

    return seed_paths
