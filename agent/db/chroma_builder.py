import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import (
    DEFAULT_CHROMA_CHILD_COLLECTION,
    DEFAULT_CHROMA_PARENT_COLLECTION,
    DEFAULT_CHROMA_PATH,
)
from ..tools.llm import get_qwen_embedding


logger = logging.getLogger(__name__)


class ChromaBuildError(RuntimeError):
    pass


@dataclass
class ChromaBuildConfig:
    chroma_path: Path = DEFAULT_CHROMA_PATH
    child_collection: str = DEFAULT_CHROMA_CHILD_COLLECTION
    parent_collection: str = DEFAULT_CHROMA_PARENT_COLLECTION
    reset_existing: bool = False


class ChromaIndexBuilder:
    def __init__(self, config: ChromaBuildConfig) -> None:
        self.config = config
        self.chroma_path = config.chroma_path
        self.child_collection = config.child_collection
        self.parent_collection = config.parent_collection

    def build(self, seed_files: list[Path] | None = None) -> dict[str, Any]:
        import chromadb

        seed_files = seed_files or []
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        events = self._load_seed_events(seed_files)
        child_records = self._build_child_records(events)
        parent_records = self._build_parent_records(child_records)

        try:
            client = chromadb.PersistentClient(path=str(self.chroma_path))
            if self.config.reset_existing:
                self._delete_collection_if_exists(client, self.child_collection)
                self._delete_collection_if_exists(client, self.parent_collection)

            child_collection = client.get_or_create_collection(
                name=self.child_collection,
                metadata={"hnsw:space": "cosine", "index_role": "child"},
            )
            parent_collection = client.get_or_create_collection(
                name=self.parent_collection,
                metadata={"hnsw:space": "cosine", "index_role": "parent"},
            )

            if child_records:
                self._upsert_records(child_collection, child_records)
            if parent_records:
                self._upsert_records(parent_collection, parent_records)
        except Exception as exc:
            logger.exception("Failed to build chroma indexes")
            raise ChromaBuildError(f"Build failed for {self.chroma_path}: {exc}") from exc

        return {
            "chroma_path": str(self.chroma_path),
            "seed_files": [str(x) for x in seed_files],
            "child_collection": self.child_collection,
            "parent_collection": self.parent_collection,
            "child_record_count": len(child_records),
            "parent_record_count": len(parent_records),
            "chunk_strategy": {
                "child": "track-level (video_id + entity_hint)",
                "parent": "video-level (video_id)",
            },
        }

    @staticmethod
    def _delete_collection_if_exists(client: Any, collection_name: str) -> None:
        try:
            client.delete_collection(collection_name)
        except Exception:
            logger.info("Skip deleting collection %s because it does not exist", collection_name)

    @staticmethod
    def _upsert_records(collection: Any, records: list[dict[str, Any]]) -> None:
        embeddings = get_qwen_embedding([record["document"] for record in records])
        collection.upsert(
            ids=[record["id"] for record in records],
            documents=[record["document"] for record in records],
            metadatas=[record["metadata"] for record in records],
            embeddings=embeddings,
        )

    def _load_seed_events(self, seed_files: list[Path]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for seed_file in seed_files:
            if not seed_file.exists():
                raise ChromaBuildError(f"Seed file not found: {seed_file}")

            payload = json.loads(seed_file.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("events"), list):
                fallback = str(payload.get("video_id", "")).strip() or None
                events.extend(self._normalize_events(payload["events"], fallback))
                continue
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict) and isinstance(item.get("events"), list):
                        fallback = str(item.get("video_id", "")).strip() or None
                        events.extend(self._normalize_events(item["events"], fallback))
                    elif isinstance(item, dict):
                        events.extend(self._normalize_events([item], None))
                continue
            if isinstance(payload, dict):
                events.extend(self._normalize_events([payload], None))
                continue
            raise ChromaBuildError(f"Unsupported seed JSON format: {seed_file}")
        return events

    @staticmethod
    def _normalize_events(raw_events: list[dict[str, Any]], fallback_video_id: str | None) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            video_id = str(event.get("video_id") or fallback_video_id or "").strip()
            entity_hint = str(event.get("entity_hint") or event.get("track_id") or "na").strip()
            if not video_id:
                continue
            normalized.append(
                {
                    "video_id": video_id,
                    "entity_hint": entity_hint,
                    "start_time": event.get("start_time"),
                    "end_time": event.get("end_time"),
                    "object_type": event.get("object_type"),
                    "object_color": event.get("object_color_en") or event.get("object_color"),
                    "scene_zone": event.get("scene_zone_en") or event.get("scene_zone"),
                    "appearance_notes": event.get("appearance_notes_en") or event.get("appearance_notes"),
                    "event_text": (
                        event.get("event_text_en")
                        or event.get("event_summary_en")
                        or event.get("event_text")
                        or event.get("event_summary")
                    ),
                    "keywords": ChromaIndexBuilder._normalize_keywords(event.get("keywords")),
                    "raw_event": event,
                }
            )
        return normalized

    @staticmethod
    def _normalize_keywords(raw_keywords: Any) -> list[str]:
        if isinstance(raw_keywords, list):
            return [str(item).strip() for item in raw_keywords if str(item).strip()]
        if isinstance(raw_keywords, str):
            text = raw_keywords.replace("|", ",").replace(";", ",")
            return [part.strip() for part in text.split(",") if part.strip()]
        return []

    @staticmethod
    def _dedupe_text(values: list[Any]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return out

    @staticmethod
    def _safe_min(values: list[Any]) -> float | None:
        nums = [float(v) for v in values if isinstance(v, (int, float))]
        return min(nums) if nums else None

    @staticmethod
    def _safe_max(values: list[Any]) -> float | None:
        nums = [float(v) for v in values if isinstance(v, (int, float))]
        return max(nums) if nums else None

    @staticmethod
    def _format_time(value: float | None) -> str:
        if value is None:
            return "unknown"
        return f"{value:.3f}".rstrip("0").rstrip(".")

    def _build_child_records(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for event in events:
            key = (event["video_id"], event["entity_hint"])
            grouped.setdefault(key, []).append(event)

        records: list[dict[str, Any]] = []
        for (video_id, entity_hint), group in sorted(grouped.items()):
            start_time = self._safe_min([item.get("start_time") for item in group])
            end_time = self._safe_max([item.get("end_time") for item in group])
            appearance_notes = self._dedupe_text([item.get("appearance_notes") for item in group])
            scene_zones = self._dedupe_text([item.get("scene_zone") for item in group])
            event_texts = self._dedupe_text([item.get("event_text") for item in group])
            object_types = self._dedupe_text([item.get("object_type") for item in group])
            object_colors = self._dedupe_text([item.get("object_color") for item in group])
            keywords = self._dedupe_text(
                [keyword for item in group for keyword in item.get("keywords", [])]
            )
            child_id = f"{video_id}_{entity_hint}"
            parent_id = video_id
            document = self._build_child_document(
                video_id=video_id,
                entity_hint=entity_hint,
                appearance_notes=appearance_notes,
                scene_zones=scene_zones,
                event_texts=event_texts,
                keywords=keywords,
                start_time=start_time,
                end_time=end_time,
            )
            records.append(
                {
                    "id": child_id,
                    "document": document,
                    "metadata": {
                        "record_level": "child",
                        "video_id": video_id,
                        "parent_id": parent_id,
                        "entity_hint": entity_hint,
                        "object_type": object_types[0] if object_types else "unknown",
                        "object_color": object_colors[0] if object_colors else "unknown",
                        "scene_zone": scene_zones[0] if scene_zones else "unknown",
                        "start_time": start_time if start_time is not None else -1.0,
                        "end_time": end_time if end_time is not None else -1.0,
                        "event_count": len(group),
                        "keywords": ", ".join(keywords),
                    },
                }
            )
        return records

    @staticmethod
    def _build_child_document(
        *,
        video_id: str,
        entity_hint: str,
        appearance_notes: list[str],
        scene_zones: list[str],
        event_texts: list[str],
        keywords: list[str],
        start_time: float | None,
        end_time: float | None,
    ) -> str:
        sections = [
            f"Video {video_id}. Track {entity_hint}.",
            f"Time range {ChromaIndexBuilder._format_time(start_time)}s to {ChromaIndexBuilder._format_time(end_time)}s.",
        ]
        if appearance_notes:
            sections.append("Appearance notes: " + " ".join(appearance_notes))
        if scene_zones:
            sections.append("Located in: " + ", ".join(scene_zones) + ".")
        if event_texts:
            sections.append("Events: " + " ".join(event_texts))
        if keywords:
            sections.append("Keywords: " + ", ".join(keywords) + ".")
        return " ".join(sections)

    def _build_parent_records(self, child_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in child_records:
            video_id = str(record["metadata"].get("video_id", "")).strip()
            if not video_id:
                continue
            grouped.setdefault(video_id, []).append(record)

        records: list[dict[str, Any]] = []
        for video_id, group in sorted(grouped.items()):
            start_time = self._safe_min([item["metadata"].get("start_time") for item in group])
            end_time = self._safe_max([item["metadata"].get("end_time") for item in group])
            child_ids = [item["id"] for item in group]
            scene_zones = self._dedupe_text([item["metadata"].get("scene_zone") for item in group])
            object_types = self._dedupe_text([item["metadata"].get("object_type") for item in group])
            object_colors = self._dedupe_text([item["metadata"].get("object_color") for item in group])
            document = self._build_parent_document(
                video_id=video_id,
                child_records=group,
                scene_zones=scene_zones,
                object_types=object_types,
                object_colors=object_colors,
                start_time=start_time,
                end_time=end_time,
            )
            records.append(
                {
                    "id": video_id,
                    "document": document,
                    "metadata": {
                        "record_level": "parent",
                        "video_id": video_id,
                        "child_count": len(group),
                        "start_time": start_time if start_time is not None else -1.0,
                        "end_time": end_time if end_time is not None else -1.0,
                        "scene_zones": ", ".join(scene_zones),
                        "object_types": ", ".join(object_types),
                        "object_colors": ", ".join(object_colors),
                        "child_ids_json": json.dumps(child_ids, ensure_ascii=False),
                    },
                }
            )
        return records

    @staticmethod
    def _build_parent_document(
        *,
        video_id: str,
        child_records: list[dict[str, Any]],
        scene_zones: list[str],
        object_types: list[str],
        object_colors: list[str],
        start_time: float | None,
        end_time: float | None,
    ) -> str:
        sections = [
            f"Video {video_id}.",
            f"Video time range {ChromaIndexBuilder._format_time(start_time)}s to {ChromaIndexBuilder._format_time(end_time)}s.",
            f"This parent record summarizes {len(child_records)} child tracks.",
        ]
        if object_types:
            sections.append("Object types: " + ", ".join(object_types) + ".")
        if object_colors:
            sections.append("Object colors: " + ", ".join(object_colors) + ".")
        if scene_zones:
            sections.append("Scene zones: " + ", ".join(scene_zones) + ".")
        child_summaries = [record["document"] for record in child_records]
        if child_summaries:
            sections.append("Child track summaries: " + " ".join(child_summaries))
        return " ".join(sections)
