import sqlite3
from pathlib import Path
from typing import Any

from .py2sql import SQLVideoSearchTool


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
