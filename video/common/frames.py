"""视频抽帧、分辨率与事件 bbox 归一化（OpenCV，供精炼或其它模块复用）。"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import cv2


@dataclass
class FrameSample:
    t_sec: float
    jpg_base64: str


def _encode_bgr_to_jpg_base64(img_bgr, quality: int = 85) -> str:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("JPEG 编码失败")
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def sample_frames_uniform(
    video_path: str,
    start_sec: float,
    end_sec: float,
    num_frames: int = 12,
    resize_width: int = 768,
) -> list[FrameSample]:
    """在 [start_sec, end_sec] 区间均匀抽帧，并把每帧编码成 base64 JPEG。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    duration = max(0.0, end_sec - start_sec)
    if duration <= 0:
        cap.release()
        return []

    times = [start_sec + (i + 0.5) * duration / num_frames for i in range(num_frames)]
    out: list[FrameSample] = []

    for t in times:
        frame_idx = int(round(t * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        h, w = frame.shape[:2]
        if resize_width and w > resize_width:
            new_w = resize_width
            new_h = int(h * (new_w / w))
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

        out.append(FrameSample(t_sec=float(t), jpg_base64=_encode_bgr_to_jpg_base64(frame)))

    cap.release()
    return out


def get_video_size(video_path: str) -> tuple[int, int]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {video_path}")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    if w <= 0 or h <= 0:
        raise RuntimeError("无法读取视频分辨率")
    return w, h


def _bbox_center_norm(xyxy: list[float], w: int, h: int) -> tuple[float, float]:
    x1, y1, x2, y2 = xyxy
    cx = (x1 + x2) / 2.0 / w
    cy = (y1 + y2) / 2.0 / h
    return float(cx), float(cy)


def enrich_events_with_normalized_location(raw_events: list[dict[str, Any]], w: int, h: int) -> list[dict[str, Any]]:
    """
    给 raw_events 补充归一化位置字段，供 LLM 做“按比例合并”的硬约束。
    输出字段（若 bbox 存在）：start_center_norm / end_center_norm / start_bbox_norm / end_bbox_norm
    """
    out: list[dict[str, Any]] = []
    for e in raw_events:
        e2 = dict(e)
        for key in ("start_bbox_xyxy", "end_bbox_xyxy"):
            if key in e2 and isinstance(e2[key], list) and len(e2[key]) == 4:
                x1, y1, x2, y2 = [float(v) for v in e2[key]]
                e2[key] = [x1, y1, x2, y2]
                e2[key.replace("_xyxy", "_norm")] = [x1 / w, y1 / h, x2 / w, y2 / h]
                cx, cy = _bbox_center_norm([x1, y1, x2, y2], w, h)
                e2[key.replace("_bbox_xyxy", "_center_norm")] = [cx, cy]
        out.append(e2)
    return out
