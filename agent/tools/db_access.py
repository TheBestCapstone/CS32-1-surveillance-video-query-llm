import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from .llm import get_qwen_embedding
from .py2sql import SQLVideoSearchTool


_LOG = logging.getLogger(__name__)
_ALPHA_DEPRECATION_LOGGED = False


class LanceDBGateway:
    def __init__(self, db_path: Path, table_name: str = "episodic_events") -> None:
        self.db_path = Path(db_path)
        self.table_name = table_name
        self._tool = SQLVideoSearchTool(db_path=self.db_path, table_name=self.table_name)

    def search(
        self,
        metadata_filters: list[Any],
        event_queries: list[str],
        candidate_limit: int = 80,
        top_k_per_event: int = 20,
    ) -> list[dict[str, Any]]:
        return self._tool.search(
            metadata_filters=metadata_filters,
            event_queries=event_queries,
            candidate_limit=candidate_limit,
            top_k_per_event=top_k_per_event,
        )


class ChromaGateway:
    def __init__(self, db_path: Path, collection_name: str = "basketball_tracks") -> None:
        import chromadb

        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=str(self.db_path))
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _build_where(metadata_filters: list[dict[str, Any]]) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []
        for item in metadata_filters:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip()
            value = item.get("value")
            if not key or value is None:
                continue
            # Chroma metadata filter: exact match
            clauses.append({key: value})
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def get_records_by_ids(self, record_ids: list[str]) -> list[dict[str, Any]]:
        ids = [str(item).strip() for item in record_ids if str(item).strip()]
        if not ids:
            return []
        res = self._collection.get(ids=ids, include=["documents", "metadatas"])
        out: list[dict[str, Any]] = []
        for idx, record_id in enumerate(res.get("ids", [])):
            documents = res.get("documents", [])
            metadatas = res.get("metadatas", [])
            doc = documents[idx] if idx < len(documents) else None
            meta = metadatas[idx] if idx < len(metadatas) else {}
            out.append(
                {
                    "record_id": record_id,
                    "document": doc,
                    "metadata": meta or {},
                }
            )
        return out

    def search(
        self,
        *,
        query: str,
        metadata_filters: list[dict[str, Any]],
        alpha: float | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Pure-vector retrieval against the configured Chroma collection.

        ``alpha`` is kept for backward compatibility with callers from the
        legacy hybrid path but is no longer used for ranking. The lexical
        channel now lives in ``BM25Index`` (see ``agent/tools/bm25_index.py``)
        and is fused with these vector results by ``hybrid_tools`` /
        ``llamaindex_adapter`` via reciprocal-rank fusion. Passing a non-default
        ``alpha`` triggers a single-shot deprecation log so callers can be
        migrated.
        """

        if limit <= 0:
            return []
        global _ALPHA_DEPRECATION_LOGGED
        if alpha is not None and not _ALPHA_DEPRECATION_LOGGED:
            _LOG.warning(
                "ChromaGateway.search(alpha=%s) is deprecated; the lexical channel "
                "moved to BM25Index. Argument is ignored.",
                alpha,
            )
            _ALPHA_DEPRECATION_LOGGED = True

        where = self._build_where(metadata_filters)
        query_vec = get_qwen_embedding(query)
        # Over-fetch so downstream RRF has rank information even when callers
        # only need a small ``limit`` of fused results.
        oversample = max(int(os.getenv("AGENT_CHROMA_VECTOR_OVERSAMPLE", "3")), 1)
        n_results = max(limit * oversample, limit)
        res = self._collection.query(
            query_embeddings=[query_vec],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        if not ids:
            return []

        # Chroma already ranks ascending by cosine distance for the
        # ``hnsw:space=cosine`` index, so we keep that order and surface the
        # cosine similarity as ``_vector_score`` for telemetry.
        out: list[dict[str, Any]] = []
        for idx in range(min(len(ids), int(limit))):
            meta = metas[idx] or {}
            distance = float(dists[idx])
            cosine_sim = max(0.0, 1.0 - distance)
            out.append(
                {
                    "event_id": ids[idx],
                    "video_id": meta.get("video_id"),
                    "track_id": meta.get("entity_hint"),
                    "start_time": meta.get("start_time"),
                    "end_time": meta.get("end_time"),
                    "object_type": meta.get("object_type"),
                    "object_color_en": meta.get("object_color"),
                    "scene_zone_en": meta.get("scene_zone"),
                    "event_summary_en": docs[idx],
                    "event_text": docs[idx],
                    "_distance": distance,
                    "_vector_score": cosine_sim,
                    "_source_type": "vector",
                }
            )
        return out


class SQLiteGateway:
    def __init__(self, db_path: Path, table_name: str = "episodic_events") -> None:
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.allowed_fields = {
            "event_id",
            "video_id",
            "camera_id",
            "track_id",
            "start_time",
            "end_time",
            "object_type",
            "object_color_cn",
        }

    def _build_where(self, metadata_filters: list[dict[str, Any]]) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for item in metadata_filters:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field", "")).strip()
            if field not in self.allowed_fields:
                continue
            op = str(item.get("op", "==")).strip().lower()
            value = item.get("value")
            if op in {"=", "=="}:
                clauses.append(f"{field} = ?")
                params.append(value)
            elif op in {"!=", "<>"}:
                clauses.append(f"{field} != ?")
                params.append(value)
            elif op in {">", ">=", "<", "<="}:
                clauses.append(f"{field} {op} ?")
                params.append(value)
            elif op == "contains":
                clauses.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
        if not clauses:
            return "", []
        return " WHERE " + " AND ".join(clauses), params

    def search(self, metadata_filters: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []
        where_clause, params = self._build_where(metadata_filters)
        sql = (
            f"SELECT event_id, video_id, camera_id, track_id, start_time, end_time, object_type, object_color_cn "
            f"FROM {self.table_name}{where_clause} ORDER BY start_time ASC LIMIT ?"
        )
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(sql, [*params, int(limit)]).fetchall()
            results = [dict(row) for row in rows]
            for row in results:
                row.setdefault("_distance", 0.0)
                if not row.get("event_summary_cn"):
                    row["event_summary_cn"] = (
                        f"{row.get('object_color_cn', '')}{row.get('object_type', '')}"
                        f" @{row.get('start_time')}-{row.get('end_time')}"
                    )
            return results
        finally:
            conn.close()
