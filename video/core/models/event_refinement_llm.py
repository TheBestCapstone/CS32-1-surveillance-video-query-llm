"""LangChain + OpenAI 多模态：对 pipeline 事件做精炼（不含抽帧与 CLI）。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from video.common.frames import FrameSample
from video.core.schema.refined_event_llm import RefinedEventsPayload, VectorEventsPayload


def refine_events_with_llm(
    *,
    video_path: str,
    clip: dict[str, float],
    raw_events: list[dict[str, Any]],
    frames: list[FrameSample],
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_time_adjust_sec: float = 0.5,
    merge_location_iou_threshold: float = 0.9,
    merge_center_dist_px: float = 30.0,
    merge_location_norm_diff: float = 0.10,
) -> RefinedEventsPayload:
    """将抽帧 + 原始事件发给 LLM，让其输出纠错后的 refined_events（严格 JSON）。"""
    parser = PydanticOutputParser(pydantic_object=RefinedEventsPayload)

    images_content: list[dict[str, Any]] = []
    for f in frames:
        images_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{f.jpg_base64}"},
            }
        )

    system = (
        "你是监控视频事件标注与纠错助手。"
        "你会基于给定的时间段抽帧（带时间戳）与初步事件列表（来自 YOLO+tracking），"
        "对事件做语义纠错、合并碎 track、补充行动细节。"
        "你必须先理解并描述监控场景（停车场、马路、入口/出口、车道左右、人行道等），"
        "并在每条事件的解释中同时写出「移动方式」和「所在场景子区」（例如：从马路中间偏右驶过、驶入停车场入口、在出口附近行人道行走）。"
        "最重要约束：尽量保留 pipeline 给出的 temporal 信息，不要随意大改时间。"
        "输出必须严格符合给定 JSON schema。"
    )

    user_text = (
        f"视频路径: {video_path}\n"
        f"当前分析时间段 clip: start_sec={clip['start_sec']}, end_sec={clip['end_sec']}\n\n"
        "下面是该 clip 内 pipeline 的原始事件（可能存在：误检、时间不准、同一事件拆分等问题）：\n"
        f"{json.dumps(raw_events, ensure_ascii=False, indent=2)}\n\n"
        "现在给你该 clip 均匀抽取的关键帧（每帧的时间戳在文件名/文本里不可见，请你在 evidence 中写明你使用了哪些帧时间戳）：\n"
        + "\n".join([f"- frame_time_sec={f.t_sec:.3f}" for f in frames])
        + "\n\n"
        "任务要求（重要：以保留时序为主；必须写「场景 + 移动」）：\n"
        "0) 先输出 scene_context：用中文概括本 clip 场景——哪里像马路、哪里像停车位、入口/出口或主通道在画面哪一侧（左/中/右、远/近）。\n"
        "1) 再做“实体去重/合并”（要非常保守，避免过度融合）：把属于同一真实车辆/行人的多个 local_track_id 合并到同一个 entity_id。\n"
        "   - 输出 entities 列表（你认为画面里真实有几辆车/几个人）。\n"
        "   - 每个 entity_id 里写明合并了哪些 local_track_ids。\n"
        "   - 合并时必须同时参考：时间重叠/相邻、位置相似度（bbox）、以及帧内容。\n"
        f"     位置合并建议规则（可解释、可调整）：\n"
        f"     - 只有在“非常确定是同一个目标”时才允许合并。\n"
        f"     - 车辆（car）默认不要合并不同 track_id，除非同时满足：\n"
        f"       (a) 时间连续/相邻（<=1s）\n"
        f"       (b) bbox 几乎重合：IoU >= {merge_location_iou_threshold}\n"
        f"       (c) 颜色/外观一致（例如都是白车/银灰车，且无明显矛盾特征）\n"
        f"       中心点距离 <= {merge_center_dist_px} px 只能作为辅证，不能单独作为合并依据。\n"
        f"     - 位置按比例的硬约束（必须遵守）：\n"
        f"       raw_events 已提供 start_center_norm/end_center_norm（0~1 归一化中心点）。\n"
        f"       若两个候选实体的归一化中心点差异在 x 或 y 任一维度 > {merge_location_norm_diff}（即画面宽/高的10%），则禁止合并。\n"
        f"       只有在抽帧中外观几乎完全一致（颜色+显著特征）且时间连续时，才允许作为例外，并在 notes 里明确写出理由。\n"
        "     - 对静止车辆：只有在同一固定车位区域、且 bbox 长时间几乎不变、且颜色一致时，才可把断裂 track_id 合并。\n"
        "     - 行人（person）也要谨慎合并：衣服颜色/体型/位置连续都一致才合并。\n"
        "   - 每个 entity 的 location 里必须包含：scene_zone、region_text、movement_in_scene_cn（移动+场景一句话）。\n"
        "   - 每个 entity 必须输出 appearance（至少 color_cn+color_confidence），用于区分不同实体。\n"
        "2) 再输出 refined_events：\n"
        "   - 事件应绑定到 entity_id（可选保留一个代表性的 track_id）。\n"
        "   - details 里必须包含 movement_scene_narrative_cn：中文一句，同时写「怎么动」和「在场景哪一块」（入口/出口/马路中间偏右/停车位等）。\n"
        "   - location 里必须包含：scene_zone、start_scene_cn、end_scene_cn、movement_scene_cn；"
        "若 raw_events 有 start_bbox_xyxy/end_bbox_xyxy 请保留到 location 并解释与场景的关系。\n"
        "3) temporal 纠错策略（硬约束）：\n"
        f"   - 默认认为 raw_events 的 start_time/end_time 是正确的“强先验”。\n"
        f"   - 只有在抽帧证据非常明确时，才允许调整时间边界，且单侧调整幅度不要超过 {max_time_adjust_sec} 秒。\n"
        "   - 如果你怀疑时间不准但证据不足：不要改时间，只在 evidence 里写“不确定”。\n"
        "4) 误检处理：\n"
        "   - 你可以删除明显误检的事件，或将 confidence 降低并解释原因。\n\n"
        f"{parser.get_format_instructions()}"
    )

    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": user_text},
        *images_content,
    ]
    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=user_content),
        ]
    )
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return parser.parse(text)


def refine_vector_events_with_llm(
    *,
    video_id: str,
    clip: dict[str, float],
    raw_events: list[dict[str, Any]],
    frames: list[FrameSample],
    model: str = "gpt-5.4",
    temperature: float = 0.0,
) -> VectorEventsPayload:
    """上线向量库版本：只输出检索必要字段，严格不改 start/end。"""
    parser = PydanticOutputParser(pydantic_object=VectorEventsPayload)

    images_content: list[dict[str, Any]] = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{f.jpg_base64}"}}
        for f in frames
    ]

    system = (
        "你是监控视频事件抽取器。"
        "你会基于原始事件列表（含 start_time/end_time 与 bbox）以及关键帧，输出用于向量检索的最小事件记录。"
        "硬约束：绝对不要修改 start_time/end_time（必须原样保留）。"
        "不要输出多余字段，不要 Markdown，不要解释。"
    )

    user_text = (
        f"video_id: {video_id}\n"
        f"clip: start_sec={clip['start_sec']}, end_sec={clip['end_sec']}\n\n"
        "raw_events_json（注意：其中的 start_time/end_time 必须原样保留到你的输出里）：\n"
        f"{json.dumps(raw_events, ensure_ascii=False, indent=2)}\n\n"
        "关键帧时间戳：\n"
        + "\n".join([f"- t={f.t_sec:.3f}" for f in frames])
        + "\n\n"
        "输出要求：\n"
        "- 只输出 JSON，且必须符合 schema。\n"
        "- event_text_cn 必须包含：起止时间 + 主体(含颜色) + 动作 + 场景区域（如入口/出口/马路右侧/停车位/人行道）。\n"
        "- object_color_cn：尽量给出白/黑/银灰/红/蓝/深色/不确定。\n"
        "- keywords：用于检索的短词（英文或拼音均可），例如 driving_in/parking/road_right/entrance/sidewalk。\n"
        f"{parser.get_format_instructions()}"
    )

    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=[{"type": "text", "text": user_text}, *images_content]),
        ]
    )
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return parser.parse(text)
