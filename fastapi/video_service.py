from __future__ import annotations

import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Literal

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_AGENT_ROOT = _PROJECT_ROOT / "agent"
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agent.db.chroma_builder import ChromaBuildConfig, ChromaIndexBuilder  # noqa: E402
from agent.db.config import (  # noqa: E402
    CHROMA_CHILD_SUFFIX,
    CHROMA_EVENT_SUFFIX,
    CHROMA_PARENT_SUFFIX,
    get_graph_chroma_child_collection,
    get_graph_chroma_event_collection,
    get_graph_chroma_namespace,
    get_graph_chroma_parent_collection,
    get_graph_chroma_path,
    get_graph_sqlite_db_path,
)
from agent.db.sqlite_builder import SQLiteBuildConfig, SQLiteDatabaseBuilder  # noqa: E402
from video.factory.pipeline_outputs import refined_events_as_dict, video_events_as_json_dicts  # noqa: E402
from video.factory.refinement_runner import RefineEventsConfig  # noqa: E402

ALLOWED_VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}
DEFAULT_MAX_UPLOAD_BYTES = 512 * 1024 * 1024


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(filename or "").strip())
    return cleaned or "uploaded_video.mp4"


def _write_json(file_path: Path, payload: dict[str, Any]) -> Path:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def _parse_target_classes(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    classes = [item.strip() for item in str(raw).split(",") if item.strip()]
    return classes or None


def _max_upload_bytes() -> int:
    raw = str(os.getenv("FASTAPI_MAX_UPLOAD_MB", "512")).strip()
    try:
        return max(1, int(raw)) * 1024 * 1024
    except ValueError:
        return DEFAULT_MAX_UPLOAD_BYTES


def _validate_upload_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        raise ValueError("只支持上传 MP4、AVI、MOV、MKV 视频文件")


def _build_seed_from_pipeline_documents(
    events_document: dict[str, Any],
    clips_document: dict[str, Any],
) -> dict[str, Any]:
    del clips_document
    meta = events_document.get("meta") if isinstance(events_document.get("meta"), dict) else {}
    source_events = events_document.get("events") if isinstance(events_document.get("events"), list) else []
    video_path = str(meta.get("video_path") or "").strip()
    video_id = Path(video_path).name if video_path else "uploaded_video.mp4"
    camera_id = str(meta.get("camera_id") or "").strip() or None

    events: list[dict[str, Any]] = []
    for item in source_events:
        if not isinstance(item, dict):
            continue
        track_id = str(item.get("track_id") or "na").strip()
        object_type = str(item.get("class_name") or "object").strip().lower()
        event_type = str(item.get("event_type") or "event").strip().lower()
        description = str(item.get("description_for_llm") or "").strip()
        start_time = item.get("start_time")
        end_time = item.get("end_time")
        summary = description or f"{object_type} {event_type}".strip()
        keywords = [token for token in [object_type, event_type] if token and token != "object"]
        seed_event = {
            "video_id": video_id,
            "camera_id": camera_id,
            "track_id": track_id,
            "entity_hint": f"track_{track_id}",
            "start_time": start_time,
            "end_time": end_time,
            "clip_start_sec": start_time,
            "clip_end_sec": end_time,
            "object_type": object_type,
            "object_color_en": "unknown",
            "scene_zone_en": "",
            "event_type": event_type,
            "motion_level": item.get("motion_level"),
            "appearance_notes_en": f"Detected by video pipeline from uploaded file {video_id}.",
            "event_text_en": summary,
            "event_summary_en": summary,
            "keywords": keywords,
            "start_bbox_xyxy": item.get("start_bbox_xyxy"),
            "end_bbox_xyxy": item.get("end_bbox_xyxy"),
            "source_event": item,
        }
        events.append(seed_event)
    return {"video_id": video_id, "events": events}


class VideoIngestService:
    def __init__(self) -> None:
        self.data_root = Path(__file__).resolve().parent / "data"

    def _job_dir(self, job_id: str) -> Path:
        return self.data_root / "video_jobs" / job_id

    @staticmethod
    def _collection_names(namespace: str | None) -> tuple[str, str, str]:
        if not namespace:
            return (
                get_graph_chroma_child_collection(),
                get_graph_chroma_parent_collection(),
                get_graph_chroma_event_collection(),
            )
        normalized = namespace.strip()
        return (
            f"{normalized}_{CHROMA_CHILD_SUFFIX}",
            f"{normalized}_{CHROMA_PARENT_SUFFIX}",
            f"{normalized}_{CHROMA_EVENT_SUFFIX}",
        )

    def _runtime_targets_for_job(self, job_dir: Path, job_id: str) -> tuple[Path, Path, str]:
        runtime_dir = job_dir / "runtime"
        chroma_dir = runtime_dir / "chroma"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        return runtime_dir / "episodic_events.sqlite", chroma_dir, f"upload_{job_id.replace('-', '_')}"

    def _save_upload_file(self, upload_file: Any, upload_dir: Path) -> tuple[str, Path]:
        safe_name = _safe_filename(getattr(upload_file, "filename", "") or "uploaded_video.mp4")
        _validate_upload_filename(safe_name)
        saved_video_path = upload_dir / safe_name
        written_bytes = 0
        max_bytes = _max_upload_bytes()
        with saved_video_path.open("wb") as sink:
            while True:
                chunk = upload_file.file.read(1024 * 1024)
                if not chunk:
                    break
                written_bytes += len(chunk)
                if written_bytes > max_bytes:
                    sink.close()
                    saved_video_path.unlink(missing_ok=True)
                    raise ValueError(f"上传文件过大，不能超过 {max_bytes // (1024 * 1024)} MB")
                sink.write(chunk)
        if hasattr(upload_file, "file"):
            upload_file.file.close()
        return safe_name, saved_video_path

    def process_upload(
        self,
        *,
        upload_file: Any,
        tracker: str,
        model_path: str,
        conf: float,
        iou: float,
        target_classes: str | None,
        camera_id: str | None,
        refine_mode: Literal["none", "vector", "full"],
        refine_model: str,
        import_to_db: bool,
        sqlite_path: str | None,
        chroma_path: str | None,
        chroma_namespace: str | None,
    ) -> dict[str, Any]:
        return self.process_uploads(
            upload_files=[upload_file],
            tracker=tracker,
            model_path=model_path,
            conf=conf,
            iou=iou,
            target_classes=target_classes,
            camera_id=camera_id,
            refine_mode=refine_mode,
            refine_model=refine_model,
            import_to_db=import_to_db,
            sqlite_path=sqlite_path,
            chroma_path=chroma_path,
            chroma_namespace=chroma_namespace,
        )

    def process_uploads(
        self,
        *,
        upload_files: list[Any],
        tracker: str,
        model_path: str,
        conf: float,
        iou: float,
        target_classes: str | None,
        camera_id: str | None,
        refine_mode: Literal["none", "vector", "full"],
        refine_model: str,
        import_to_db: bool,
        sqlite_path: str | None,
        chroma_path: str | None,
        chroma_namespace: str | None,
    ) -> dict[str, Any]:
        del sqlite_path, chroma_path, chroma_namespace
        if not upload_files:
            raise ValueError("至少需要上传一个视频文件")
        job_id = f"video-{uuid.uuid4().hex[:12]}"
        job_dir = self._job_dir(job_id)
        upload_dir = job_dir / "upload"
        output_dir = job_dir / "output"
        upload_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        run_kwargs: dict[str, Any] = {
            "model_path": model_path,
            "conf": float(conf),
            "iou": float(iou),
            "tracker": tracker,
        }
        parsed_classes = _parse_target_classes(target_classes)
        if parsed_classes is not None:
            run_kwargs["target_classes"] = parsed_classes
        if camera_id:
            run_kwargs["camera_id"] = camera_id.strip()

        db_import: dict[str, Any] | None = None
        runtime_sqlite_path: Path | None = None
        runtime_chroma_path: Path | None = None
        runtime_namespace: str | None = None
        file_artifacts: list[dict[str, Any]] = []
        filenames: list[str] = []
        seed_paths: list[Path] = []
        pipeline_file_meta: list[dict[str, Any]] = []
        total_events_count = 0
        total_clip_count = 0

        for upload_file in upload_files:
            safe_name, saved_video_path = self._save_upload_file(upload_file, upload_dir)
            filenames.append(safe_name)

            events_document, clips_document = video_events_as_json_dicts(str(saved_video_path), **run_kwargs)
            base_name = saved_video_path.stem
            events_path = _write_json(output_dir / f"{base_name}_events.json", events_document)
            clips_path = _write_json(output_dir / f"{base_name}_clips.json", clips_document)
            seed_payload = _build_seed_from_pipeline_documents(events_document, clips_document)
            seed_json_path = _write_json(output_dir / f"{base_name}_db_seed.json", seed_payload)

            refined_path: Path | None = None
            seed_path = seed_json_path
            if refine_mode == "vector":
                refined_payload = refined_events_as_dict(
                    events_document,
                    clips_document,
                    RefineEventsConfig(mode="vector", model=refine_model),
                )
                refined_path = _write_json(output_dir / f"{base_name}_vector_flat.json", refined_payload)
                seed_path = refined_path
            elif refine_mode == "full":
                refined_payload = refined_events_as_dict(
                    events_document,
                    clips_document,
                    RefineEventsConfig(mode="full", model=refine_model),
                )
                refined_path = _write_json(output_dir / f"{base_name}_refined_full.json", refined_payload)
                if import_to_db:
                    vector_payload = refined_events_as_dict(
                        events_document,
                        clips_document,
                        RefineEventsConfig(mode="vector", model=refine_model),
                    )
                    seed_path = _write_json(output_dir / f"{base_name}_vector_flat.json", vector_payload)

            seed_paths.append(seed_path)
            events_count = len(events_document.get("events") or [])
            clip_count = len(clips_document.get("clip_segments") or [])
            total_events_count += events_count
            total_clip_count += clip_count
            pipeline_file_meta.append(
                {
                    "filename": safe_name,
                    "video_path": str(saved_video_path),
                    "events_count": events_count,
                    "clip_count": clip_count,
                    "meta": events_document.get("meta") if isinstance(events_document.get("meta"), dict) else {},
                }
            )
            file_artifacts.append(
                {
                    "filename": safe_name,
                    "uploaded_video_path": str(saved_video_path),
                    "events_json_path": str(events_path),
                    "clips_json_path": str(clips_path),
                    "refined_json_path": str(refined_path) if refined_path else None,
                    "db_seed_path": str(seed_path),
                }
            )

        if import_to_db:
            runtime_sqlite_path, runtime_chroma_path, runtime_namespace = self._runtime_targets_for_job(job_dir, job_id)
            resolved_sqlite_path = runtime_sqlite_path
            resolved_chroma_path = runtime_chroma_path
            resolved_namespace = runtime_namespace
            child_collection, parent_collection, event_collection = self._collection_names(
                resolved_namespace
            )

            sqlite_builder = SQLiteDatabaseBuilder(
                SQLiteBuildConfig(
                    db_path=resolved_sqlite_path,
                    reset_existing=False,
                    generate_init_prompt=False,
                )
            )
            chroma_builder = ChromaIndexBuilder(
                ChromaBuildConfig(
                    chroma_path=resolved_chroma_path,
                    child_collection=child_collection,
                    parent_collection=parent_collection,
                    event_collection=event_collection,
                    reset_existing=False,
                )
            )
            db_import = {
                "sqlite": sqlite_builder.build(seed_files=seed_paths),
                "chroma": chroma_builder.build(seed_files=seed_paths),
            }

        return {
            "status": "ok",
            "job_id": job_id,
            "filename": filenames[0],
            "filenames": filenames,
            "file_count": len(filenames),
            "refine_mode": refine_mode,
            "imported_to_db": import_to_db,
            "pipeline_meta": {
                "batch": True,
                "file_count": len(filenames),
                "files": pipeline_file_meta,
            },
            "events_count": total_events_count,
            "clip_count": total_clip_count,
            "artifacts": file_artifacts,
            "database_import": db_import,
            "runtime_target": {
                "sqlite_path": str(runtime_sqlite_path) if runtime_sqlite_path else None,
                "chroma_path": str(runtime_chroma_path) if runtime_chroma_path else None,
                "chroma_namespace": runtime_namespace,
            },
        }


video_ingest_service = VideoIngestService()
