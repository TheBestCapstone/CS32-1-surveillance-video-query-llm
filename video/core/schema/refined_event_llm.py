"""LangChain 精炼阶段的 Pydantic 输出 schema（与 YOLO pipeline 解耦）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RefinedEntity(BaseModel):
    """
    “实体”层：LLM 把多个碎 track_id 合并成更接近真实的实体（例如 5 辆车）。
    这里的 entity_id 是 LLM 新生成的“全局实体 id”（单镜头内即可用）。
    """

    entity_id: str = Field(description="全局实体 id，例如 car_1 / person_2")
    class_name: str = Field(description="实体类别，如 car / person")
    local_track_ids: list[int] = Field(default_factory=list, description="被合并进来的 local track_id 列表")
    appearance: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "外观特征（用于区分不同车/不同人，避免误合并）。建议键：\n"
            "- color_cn: 颜色中文（如 白/黑/银灰/红/蓝/不确定）\n"
            "- color_confidence: 0~1\n"
            "- vehicle_type_cn: 轿车/ SUV / 卡车/面包车/不确定（仅 car 类）\n"
            "- distinctive_marks_cn: 显著特征（如车顶行李架、贴纸、深色玻璃、衣服颜色等）\n"
        ),
    )
    location: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "位置+场景语义，必须含场景子区与移动相对场景，例如：\n"
            "- scene_zone: entrance|exit|road|road_right|road_left|road_center|parking|parking_slot|sidewalk|far_background\n"
            "- region_text: 如「停车场入口内侧」「马路中间偏右车道」\n"
            "- movement_in_scene_cn: 一句话，同时写清「怎么动」+「在哪个场景」（如：沿马路右侧车道驶过→拐入停车场入口）\n"
            "- representative_bbox_xyxy / representative_time_sec\n"
        ),
    )
    notes: str = Field(default="", description="合并理由/外观/位置/时间等说明")


class RefinedEvent(BaseModel):
    event_id: str = Field(description="事件唯一 id（可由 track_id+时间段拼接）")
    event_type: str = Field(description="事件类型，如 driving_in / parking / walking / interaction 等")
    class_name: str = Field(description="主体类别，如 car / person")
    track_id: int | None = Field(default=None, description="来自 tracker 的 local track_id（若可对应）")
    entity_id: str | None = Field(default=None, description="纠错后的全局实体 id（用于把碎 track 合并）")
    start_time: float = Field(description="事件开始时间（秒）")
    end_time: float = Field(description="事件结束时间（秒）")
    confidence: float = Field(ge=0.0, le=1.0, description="LLM 对该事件存在性的置信度(0~1)")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "行动细节；必须含 movement_scene_narrative_cn：中文一句，同时描述移动方式与场景位置"
            "（入口/出口/马路中间偏右/停车位等），可与 location 呼应。"
        ),
    )
    evidence: dict[str, Any] = Field(
        default_factory=dict,
        description="证据：引用哪些帧时间戳、可见性说明、为何调整 temporal 边界等",
    )
    location: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "该事件的位置+场景（与 bbox 对齐），必填字段建议：\n"
            "- scene_zone: 同上枚举（入口/出口/马路偏右/停车位等）\n"
            "- start_scene_cn / end_scene_cn: 事件起止时刻目标所在场景子区（中文）\n"
            "- movement_scene_cn: 本事件内「移动+场景」一句话总结（如：从马路右侧驶入停车场入口区域后减速）\n"
            "- start_bbox_xyxy/end_bbox_xyxy（若 raw 有则复用）\n"
        ),
    )


class RefinedEventsPayload(BaseModel):
    video_path: str
    analyzed_clip: dict[str, float]  # {"start_sec":..., "end_sec":...}
    scene_context: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "整段 clip 的场景理解（先看全局再写事件）。建议键：\n"
            "- overview_cn: 1~3 句中文总览（停车场/马路/建筑/入口出口大致在哪）\n"
            "- layout_cn: 画面左中右、远中近分别是什么（马路/车位/人行道等）\n"
            "- entrance_exit_guess_cn: 你认为的车辆/行人入口、出口或主要通道在哪一侧\n"
            "- landmarks: 可选，列表，如路灯、斑马线、闸机、树丛等"
        ),
    )
    entities: list[RefinedEntity] = Field(default_factory=list, description="全局实体列表（去重后的车/人）")
    refined_events: list[RefinedEvent]
    temporal_policy: dict[str, Any] = Field(
        default_factory=dict,
        description="时序策略说明：是否严格保留 raw 时序、允许调整的最大幅度等",
    )
    location_policy: dict[str, Any] = Field(
        default_factory=dict,
        description="位置策略说明：使用哪些规则合并位置相似目标（如 bbox IoU/中心距离/同一区域）",
    )


class RefinedAllClipsPayload(BaseModel):
    """对 clips.json 的所有 clip_segments 逐段输出结果。"""

    video_path: str
    clips: list[RefinedEventsPayload]


class VectorEvent(BaseModel):
    video_id: str
    clip_start_sec: float
    clip_end_sec: float
    start_time: float
    end_time: float
    object_type: str
    object_color_cn: str
    appearance_notes_cn: str
    scene_zone_cn: str
    event_text_cn: str
    keywords: list[str]
    start_bbox_xyxy: list[float] | None = None
    end_bbox_xyxy: list[float] | None = None
    entity_hint: str | None = None


class VectorEventsPayload(BaseModel):
    video_id: str
    clip_start_sec: float
    clip_end_sec: float
    events: list[VectorEvent]


class VectorAllClipsPayload(BaseModel):
    video_id: str
    clips: list[VectorEventsPayload]
