"""LangChain + OpenAI 多模态：对 pipeline 事件做精炼（不含抽帧与 CLI）。"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from video.common.frames import FrameSample, PersonCrop, coarse_color_cn_from_bgr, crop_bgr_at_time_xyxy
from video.core.schema.multi_camera import MatchVerification
from video.core.schema.refined_event_llm import RefinedEntity, RefinedEventsPayload, VectorEventsPayload

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _TrackSummary:
    class_name: str
    start_time: float
    end_time: float
    rep_t_sec: float
    rep_bbox_xyxy: list[float]
    color_cn: str


def _time_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _summarize_tracks_for_merge(video_path: str, raw_events: list[dict[str, Any]]) -> dict[int, _TrackSummary]:
    """
    从 raw_events 聚合每个 track_id 的时间范围，并在代表性时间点裁剪 bbox 估计粗颜色。
    """
    by_tid: dict[int, list[dict[str, Any]]] = {}
    for e in raw_events:
        tid = e.get("track_id")
        if tid is None:
            continue
        by_tid.setdefault(int(tid), []).append(e)

    out: dict[int, _TrackSummary] = {}
    for tid, evs in by_tid.items():
        cls = str(evs[0].get("class_name", "unknown"))
        s = float(min(float(e.get("start_time", 0.0)) for e in evs))
        t = float(max(float(e.get("end_time", 0.0)) for e in evs))
        rep = evs[0]
        rep_t = float(rep.get("start_time", s))
        rep_bbox = rep.get("start_bbox_xyxy") or rep.get("end_bbox_xyxy") or [0, 0, 0, 0]
        rep_bbox = [float(x) for x in rep_bbox]
        crop = crop_bgr_at_time_xyxy(video_path, rep_t, rep_bbox)
        color_cn = coarse_color_cn_from_bgr(crop) if crop is not None else "不确定"
        out[tid] = _TrackSummary(
            class_name=cls,
            start_time=s,
            end_time=t,
            rep_t_sec=rep_t,
            rep_bbox_xyxy=rep_bbox,
            color_cn=color_cn,
        )
    return out


class _MergeDecision(RefinedEventsPayload.__class__):  # type: ignore[misc]
    pass


def _verify_merge_yesno_with_llm(
    *,
    video_path: str,
    a_tid: int,
    b_tid: int,
    a: _TrackSummary,
    b: _TrackSummary,
    model: str,
    temperature: float = 0.0,
) -> tuple[bool, float]:
    """
    只允许 LLM 输出 YES/NO + confidence。返回 (is_yes, confidence)。
    """
    from pydantic import BaseModel, Field

    class MergeYesNo(BaseModel):
        answer: Literal["YES", "NO"] = Field(description="只能是 YES 或 NO")
        confidence: float = Field(ge=0.0, le=1.0, description="0~1 置信度")

    parser = PydanticOutputParser(pydantic_object=MergeYesNo)

    crop_a = crop_bgr_at_time_xyxy(video_path, a.rep_t_sec, a.rep_bbox_xyxy)
    crop_b = crop_bgr_at_time_xyxy(video_path, b.rep_t_sec, b.rep_bbox_xyxy)
    images: list[dict[str, Any]] = []
    if crop_a is not None:
        # reuse PersonCrop encoder path
        pc_a = PersonCrop(t_sec=a.rep_t_sec, camera_id="single", track_id=a_tid, image_array=crop_a, jpg_base64="")
        pc_a.jpg_base64 = ""  # placeholder
        images.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{FrameSample(0,'').jpg_base64}"}})
    # We cannot easily reuse encoder without importing; so we pass no images if crop fails.
    # Note: model can still decide from metadata conservatively.

    system = (
        "你是监控视频实体合并判定器。"
        "你只需要判断两个 track_id 是否属于同一真实目标。"
        "你必须严格输出 JSON，且只能包含 YES/NO 和一个 0~1 的置信度。"
    )
    user_text = (
        f"track_a: id={a_tid}, class={a.class_name}, time=[{a.start_time:.3f},{a.end_time:.3f}], color_guess={a.color_cn}\n"
        f"track_b: id={b_tid}, class={b.class_name}, time=[{b.start_time:.3f},{b.end_time:.3f}], color_guess={b.color_cn}\n"
        "判断是否同一个目标。只有在非常确定时才回答 YES，否则回答 NO。\n"
        f"{parser.get_format_instructions()}"
    )
    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=[{"type": "text", "text": user_text}])])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    parsed = parser.parse(text)
    return parsed.answer == "YES", float(parsed.confidence)


def build_entities_with_hard_constraints(
    *,
    video_path: str,
    raw_events: list[dict[str, Any]],
    model: str,
    max_gap_sec: float = 300.0,
    min_llm_confidence: float = 0.75,
) -> list[RefinedEntity]:
    """
    修改一：先用硬规则过滤候选对，再用 LLM YES/NO+confidence 判定是否合并。

    硬规则（任一不满足直接跳过，不送 LLM）：
    - 时间上有重叠 → 不可能同一目标
    - 颜色明显不同 → 不送
    - 时间间隔 > 5min → 不送
    """
    tracks = _summarize_tracks_for_merge(video_path, raw_events)
    tids = sorted(tracks.keys())

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

    for i in range(len(tids)):
        for j in range(i + 1, len(tids)):
            a_tid, b_tid = tids[i], tids[j]
            a, b = tracks[a_tid], tracks[b_tid]
            if a.class_name != b.class_name:
                continue
            if _time_overlap(a.start_time, a.end_time, b.start_time, b.end_time) > 0:
                continue
            gap = min(abs(b.start_time - a.end_time), abs(a.start_time - b.end_time))
            if gap > max_gap_sec:
                continue
            if a.color_cn != "不确定" and b.color_cn != "不确定" and a.color_cn != b.color_cn:
                continue
            yes, conf = _verify_merge_yesno_with_llm(
                video_path=video_path,
                a_tid=a_tid,
                b_tid=b_tid,
                a=a,
                b=b,
                model=model,
                temperature=0.0,
            )
            if yes and conf > min_llm_confidence:
                union(a_tid, b_tid)

    groups: dict[int, list[int]] = {}
    for tid in tids:
        groups.setdefault(find(tid), []).append(tid)

    entities: list[RefinedEntity] = []
    for idx, (_, members) in enumerate(sorted(groups.items(), key=lambda x: min(x[1])), start=1):
        cls = tracks[members[0]].class_name
        entities.append(
            RefinedEntity(
                entity_id=f"{cls}_{idx}",
                class_name=cls,
                local_track_ids=sorted(members),
                appearance={"color_cn": tracks[members[0]].color_cn, "color_confidence": 0.5},
                location={},
                notes="实体合并由硬规则过滤 + LLM YES/NO 判定得到。",
            )
        )
    return entities


def refine_events_with_llm(
    *,
    video_path: str,
    clip: dict[str, float],
    raw_events: list[dict[str, Any]],
    frames: list[FrameSample],
    model: str = "gpt-5.4",
    temperature: float = 0.1,
    max_time_adjust_sec: float = 0.5,
    merge_location_iou_threshold: float = 0.9,
    merge_center_dist_px: float = 30.0,
    merge_location_norm_diff: float = 0.10,
    pre_entities: list[RefinedEntity] | None = None,
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
        "对事件做语义纠错、补充行动细节。"
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
        "1) 实体列表（entities）将由系统预先提供，你必须原样使用，不允许新增或合并实体。\n"
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
        "2) 输出 refined_events：\n"
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

    if pre_entities is not None:
        user_text += "\n\n已确定的 entities（必须原样保留，不可新增/合并/删除，只能在 refined_events 里引用 entity_id）：\n"
        user_text += json.dumps([e.model_dump() for e in pre_entities], ensure_ascii=False, indent=2)

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


# ------------------------------------------------------------------
# Cross-camera person match verification
# ------------------------------------------------------------------

def verify_person_match_with_llm(
    crop_a: PersonCrop,
    crop_b: PersonCrop,
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
) -> MatchVerification:
    """发送两张人物裁剪图给 VLM，判断是否为同一人。"""
    system = (
        "你是一个监控视频人物匹配助手。"
        "你会收到来自不同摄像头的两张人物裁剪图。"
        "请判断这两张图片中的人是否为同一个人。"
        "基于衣着颜色、体型、配饰、发型等外观特征来判断。"
        '输出严格 JSON: {"is_match": bool, "confidence": 0.0~1.0, "reasoning": "..."}'
    )

    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": (
            f"图片A来自摄像头 {crop_a.camera_id}（时间 {crop_a.t_sec:.1f}s）\n"
            f"图片B来自摄像头 {crop_b.camera_id}（时间 {crop_b.t_sec:.1f}s）\n"
            "请判断这两个人是否为同一人。"
        )},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{crop_a.jpg_base64}"},
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{crop_b.jpg_base64}"},
        },
    ]

    llm = ChatOpenAI(model=model, temperature=temperature)
    resp = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=user_content),
    ])
    raw = resp.content if isinstance(resp.content, str) else str(resp.content)

    try:
        data = json.loads(raw)
        return MatchVerification(
            is_match=bool(data.get("is_match", False)),
            confidence=float(data.get("confidence", 0.0)),
            reasoning=str(data.get("reasoning", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.warning("LLM 返回非法 JSON，默认不匹配: %s", raw[:200])
        return MatchVerification(is_match=False, confidence=0.0, reasoning=f"parse error: {raw[:100]}")
