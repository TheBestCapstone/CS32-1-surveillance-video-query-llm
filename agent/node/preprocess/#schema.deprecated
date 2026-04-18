from typing import Any, Dict, List, Optional


class TableSchema:
    def __init__(self, table_name: str, fields: List[Dict[str, Any]]):
        self.table_name = table_name
        self.fields = {f["name"]: f for f in fields}

    def get_field(self, name: str) -> Optional[Dict[str, Any]]:
        return self.fields.get(name)

    def has_field(self, name: str) -> bool:
        return name in self.fields

    def get_filterable_fields(self) -> List[Dict[str, Any]]:
        return [f for f in self.fields.values() if f.get("filterable", False)]

    def get_searchable_fields(self) -> List[Dict[str, Any]]:
        return [f for f in self.fields.values() if f.get("searchable", False)]


class SchemaRegistry:
    _instance: Optional["SchemaRegistry"] = None

    def __init__(self):
        self._schemas: Dict[str, TableSchema] = {}
        self._register_default_schemas()

    @classmethod
    def get_instance(cls) -> "SchemaRegistry":
        if cls._instance is None:
            cls._instance = SchemaRegistry()
        return cls._instance

    def _register_default_schemas(self):
        self.register_schema(TableSchema("video_events", [
            {"name": "object_color_cn", "type": "string", "filterable": True, "searchable": True, "description": "目标颜色中文名"},
            {"name": "object_type_cn", "type": "string", "filterable": True, "searchable": True, "description": "目标类型中文名"},
            {"name": "appearance_notes_cn", "type": "string", "filterable": True, "searchable": True, "description": "运动状态"},
            {"name": "start_time", "type": "float", "filterable": True, "searchable": False, "description": "开始时间(秒)"},
            {"name": "end_time", "type": "float", "filterable": True, "searchable": False, "description": "结束时间(秒)"},
            {"name": "event_summary", "type": "string", "filterable": False, "searchable": True, "description": "事件摘要"},
            {"name": "event", "type": "string", "filterable": False, "searchable": True, "description": "核心事件"},
            {"name": "camera_id", "type": "string", "filterable": True, "searchable": True, "description": "摄像头ID"},
        ]))

        self.register_schema(TableSchema("video_vect", [
            {"name": "event", "type": "string", "filterable": False, "searchable": True, "description": "核心语义事件"},
            {"name": "scene", "type": "string", "filterable": False, "searchable": True, "description": "场景描述"},
            {"name": "behavior", "type": "string", "filterable": False, "searchable": True, "description": "行为描述"},
            {"name": "object", "type": "string", "filterable": False, "searchable": True, "description": "目标描述"},
            {"name": "camera_id", "type": "string", "filterable": True, "searchable": True, "description": "摄像头ID"},
        ]))

    def register_schema(self, schema: TableSchema) -> None:
        self._schemas[schema.table_name] = schema

    def get_schema(self, table_name: str) -> Optional[TableSchema]:
        return self._schemas.get(table_name)

    def list_tables(self) -> List[str]:
        return list(self._schemas.keys())

    def get_table_fields(self, table_name: str) -> List[Dict[str, Any]]:
        schema = self.get_schema(table_name)
        if schema is None:
            return []
        return list(schema.fields.values())


def get_schema_registry() -> SchemaRegistry:
    return SchemaRegistry.get_instance()


def build_filterable_fields_prompt(table_name: str) -> str:
    registry = get_schema_registry()
    schema = registry.get_schema(table_name)
    if schema is None:
        return ""

    lines = [f"表名: {table_name}", "可过滤字段:"]
    for field in schema.get_filterable_fields():
        lines.append(f"  - {field['name']}: {field['description']} (类型: {field['type']})")
    return "\n".join(lines)
