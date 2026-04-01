"""
检测与跟踪：YOLO + Ultralytics track（BoT-SORT / ByteTrack 等）。
对应 README 中 factory/processors/vision.py 职责。
"""

import shutil
from pathlib import Path

import cv2
from ultralytics import YOLO

from video.common.paths import botsort_reid_config_path, yolo_model_dir

_BOTSORT_REID_YAML = botsort_reid_config_path()
_YOLO_MODEL_DIR = yolo_model_dir()
_YOLO11M_LOCAL = _YOLO_MODEL_DIR / "yolo11m.pt"


def resolve_tracker(tracker: str) -> tuple[str, str]:
    """
    将简短名称解析为 Ultralytics 可用的 tracker 路径/内置名。
    返回: (传给 model.track 的 tracker 参数, 人类可读名称)。
    """
    t = tracker.strip().lower()
    if t in ("bytetrack", "byte", "bt"):
        return "bytetrack.yaml", "ByteTrack"
    if t in ("botsort", "bot", "botsort_noreid"):
        return "botsort.yaml", "BoT-SORT(官方默认, with_reid=False)"
    if t in ("botsort_reid", "bot_reid", "default", "botsort+reid"):
        if not _BOTSORT_REID_YAML.is_file():
            return "botsort.yaml", "BoT-SORT(fallback: 未找到 config/trackers/botsort_reid.yaml)"
        return str(_BOTSORT_REID_YAML), "BoT-SORT+ReID(config/trackers/botsort_reid.yaml)"
    p = Path(tracker)
    if p.is_file():
        return str(p.resolve()), str(p.resolve())
    return tracker, tracker


def resolve_model(model: str) -> tuple[str, str]:
    """
    模型路径解析：支持简写 n/s/m/l/x 或任意 .pt / 自定义权重路径。
    返回: (传给 YOLO() 的路径, 写入 meta 的展示名)。
    """
    raw = model.strip()
    key = raw.lower()
    aliases: dict[str, str] = {
        "n": "yolov8n.pt",
        "nano": "yolov8n.pt",
        "s": "yolov8s.pt",
        "small": "yolov8s.pt",
        "m": str(_YOLO11M_LOCAL),
        "medium": str(_YOLO11M_LOCAL),
        "11m": str(_YOLO11M_LOCAL),
        "yolo11m": str(_YOLO11M_LOCAL),
        "yolov11m": str(_YOLO11M_LOCAL),
        "l": "yolov8l.pt",
        "large": "yolov8l.pt",
        "x": "yolov8x.pt",
        "xlarge": "yolov8x.pt",
    }
    if key in aliases:
        p = aliases[key]
        return p, p
    return raw, raw


def run_yolo_track_on_video(
    video_path: str,
    model_path: str = "yolov8n.pt",
    conf: float = 0.25,
    iou: float = 0.45,
    tracker: str = "botsort_reid",
    save_annotated_video: bool = False,
    annotated_video_path: str | None = None,
):
    """
    对视频跑 YOLO + 跟踪（默认 BoT-SORT+ReID），逐帧收集检测结果。
    返回: (fps, 总帧数, 逐帧检测列表, tracker_name)。
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"无法打开视频: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    model_pt, _ = resolve_model(model_path)
    if model_pt == str(_YOLO11M_LOCAL):
        _YOLO_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        if not _YOLO11M_LOCAL.is_file():
            # 先触发 ultralytics 下载，再把权重复制到仓库 _model 目录中，保证可复现。
            downloaded = YOLO("yolo11m.pt")
            src = Path(getattr(downloaded, "ckpt_path", "") or "")
            if src.is_file():
                shutil.copy2(src, _YOLO11M_LOCAL)
            del downloaded
        model_pt = str(_YOLO11M_LOCAL)
    model = YOLO(model_pt)
    tracker_cfg, tracker_name = resolve_tracker(tracker)
    writer: cv2.VideoWriter | None = None
    if save_annotated_video:
        if annotated_video_path is None:
            p = Path(video_path)
            annotated_video_path = str(p.with_name(p.stem + "_tracked.mp4"))

    results = model.track(
        source=video_path,
        conf=conf,
        iou=iou,
        persist=True,
        stream=True,
        verbose=False,
        tracker=tracker_cfg,
        device="mps",
    )

    frame_detections: list[list[tuple[int | None, str, float, list[float]]]] = []
    for r in results:
        if save_annotated_video:
            plotted = r.plot()
            if writer is None:
                h, w = plotted.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(str(annotated_video_path), fourcc, float(fps), (w, h))
            writer.write(plotted)

        row: list[tuple[int | None, str, float, list[float]]] = []
        if r.boxes is not None:
            for box in r.boxes:
                tid = int(box.id[0]) if box.id is not None else None
                cls_id = int(box.cls[0])
                cls_name = model.names[cls_id]
                c = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                row.append((tid, cls_name, c, [x1, y1, x2, y2]))
        frame_detections.append(row)

    if writer is not None:
        writer.release()

    return fps, total_frames, frame_detections, tracker_name
