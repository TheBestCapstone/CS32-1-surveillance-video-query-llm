"""
轨迹聚合与事件切片（不依赖 YOLO，仅处理逐帧检测序列）。
对应 README 中 factory/processors/analyzer.py 职责。
"""

from __future__ import annotations

from typing import Any


def _bbox_center(xyxy: list[float]) -> tuple[float, float]:
    x1, y1, x2, y2 = xyxy
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def aggregate_tracks(
    fps: float,
    frame_detections: list[list[tuple[int | None, str, float, list[float]]]],
) -> list[dict[str, Any]]:
    """
    把逐帧检测按 track_id 聚合成一条条轨迹。
    每条轨迹包含: track_id, class_name, start/end_time, motion_score 等。
    """
    tracks_raw: dict[int, list[tuple[int, float, float, float, str, float, list[float]]]] = {}
    for frame_idx, dets in enumerate(frame_detections):
        t_sec = frame_idx / fps if fps > 0 else 0.0
        for tid, cls_name, conf, xyxy in dets:
            if tid is None:
                continue
            cx, cy = _bbox_center(xyxy)
            if tid not in tracks_raw:
                tracks_raw[tid] = []
            tracks_raw[tid].append((frame_idx, t_sec, cx, cy, cls_name, conf, xyxy))

    tracks: list[dict[str, Any]] = []
    for tid, points in tracks_raw.items():
        if not points:
            continue
        frame_indices = [p[0] for p in points]
        times = [p[1] for p in points]
        positions = [(p[2], p[3]) for p in points]
        class_name = points[0][4]

        motion_sum = 0.0
        motion_count = 0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i - 1][0]
            dy = positions[i][1] - positions[i - 1][1]
            motion_sum += (dx * dx + dy * dy) ** 0.5
            motion_count += 1
        motion_score = motion_sum / motion_count if motion_count else 0.0

        time_xyxy: list[tuple[float, list[float]]] = [(p[1], list(p[6])) for p in points]

        tracks.append({
            "track_id": tid,
            "class_name": class_name,
            "start_frame": min(frame_indices),
            "end_frame": max(frame_indices),
            "start_time": min(times),
            "end_time": max(times),
            "positions": positions,
            "frame_indices": frame_indices,
            "times": times,
            "time_xyxy": time_xyxy,
            "motion_score": round(motion_score, 2),
        })
    return tracks


def _bbox_at_time(time_xyxy: list[tuple[float, list[float]]], t_sec: float) -> list[float]:
    if not time_xyxy:
        return [0.0, 0.0, 0.0, 0.0]
    best = min(time_xyxy, key=lambda x: abs(x[0] - t_sec))
    return list(best[1])


def _build_motion_edges(tr: dict[str, Any]) -> list[tuple[float, float, float]]:
    edges: list[tuple[float, float, float]] = []
    fi, pos, times = tr["frame_indices"], tr["positions"], tr["times"]
    for i in range(1, len(pos)):
        gap = fi[i] - fi[i - 1]
        if gap <= 0:
            continue
        dx = pos[i][0] - pos[i - 1][0]
        dy = pos[i][1] - pos[i - 1][1]
        dist = (dx * dx + dy * dy) ** 0.5
        if gap > 15 or dist > 400:
            continue
        edges.append((times[i - 1], times[i], dist))
    return edges


def _find_motion_time_segments(
    edges: list[tuple[float, float, float]],
    t_start: float,
    t_end: float,
    window_sec: float,
    sum_threshold: float,
    sample_step: float = 0.15,
    jitter_floor_px: float = 3.0,
) -> list[tuple[float, float]]:
    if not edges or t_end <= t_start:
        return []
    moving_windows: list[tuple[float, float]] = []
    t = t_start
    while t <= t_end - 0.05:
        tw = t + window_sec
        s = 0.0
        for a, b, d in edges:
            if b <= t or a >= tw:
                continue
            overlap = min(b, tw) - max(a, t)
            if overlap > 0 and (b - a) > 1e-6:
                adj = max(0.0, d - jitter_floor_px)
                s += adj * (overlap / (b - a))
        if s >= sum_threshold:
            moving_windows.append((t, tw))
        t += sample_step

    if not moving_windows:
        return []

    moving_windows.sort(key=lambda x: x[0])
    merged: list[list[float]] = [[moving_windows[0][0], moving_windows[0][1]]]
    for a, b in moving_windows[1:]:
        if a <= merged[-1][1] + sample_step:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(float(x[0]), float(x[1])) for x in merged]


def _merge_overlapping_segments(
    segments: list[dict[str, float]],
    min_gap: float = 0.5,
) -> list[dict[str, float]]:
    if not segments:
        return []
    sorted_segs = sorted(segments, key=lambda s: s["start_sec"])
    out: list[dict[str, float]] = [dict(sorted_segs[0])]
    for s in sorted_segs[1:]:
        if s["start_sec"] <= out[-1]["end_sec"] + min_gap:
            out[-1]["end_sec"] = max(out[-1]["end_sec"], s["end_sec"])
        else:
            out.append(dict(s))
    return out


def slice_events(
    tracks: list[dict[str, Any]],
    fps: float,
    frame_detections: list[list[tuple[int | None, str, float, list[float]]]],
    motion_threshold: float = 3.0,
    min_clip_duration: float = 1.0,
    max_static_duration: float = 30.0,
    motion_window_sec: float = 1.5,
    motion_window_sum_threshold: float = 20.0,
    motion_segment_pad_sec: float = 0.8,
):
    """根据轨迹生成事件与 clip 段。"""
    events: list[dict[str, Any]] = []
    clip_segments: list[dict[str, float]] = []

    for tr in tracks:
        t_start = tr["start_time"]
        t_end = tr["end_time"]
        duration = t_end - t_start
        motion_mean = tr["motion_score"]
        edges = _build_motion_edges(tr)
        motion_segs = _find_motion_time_segments(
            edges,
            t_start,
            t_end,
            motion_window_sec,
            motion_window_sum_threshold,
        )

        if not motion_segs and duration < 25 and edges:
            max_edge = max(e[2] for e in edges)
            total_adj = sum(max(0.0, e[2] - 3.0) for e in edges)
            if max_edge >= 12 or total_adj >= motion_window_sum_threshold * 0.8:
                motion_segs = [(t_start, t_end)]

        if motion_segs:
            for ms, me in motion_segs:
                cs = max(t_start, ms - motion_segment_pad_sec)
                ce = min(t_end, me + motion_segment_pad_sec)
                if ce - cs < min_clip_duration:
                    ce = min(t_end, cs + min_clip_duration)
                events.append({
                    "event_type": "motion_segment",
                    "track_id": tr["track_id"],
                    "class_name": tr["class_name"],
                    "start_time": round(cs, 3),
                    "end_time": round(ce, 3),
                    "start_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], cs),
                    "end_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], ce),
                    "motion_level": "high",
                    "motion_window_sec": motion_window_sec,
                    "description_for_llm": (
                        f"{tr['class_name']} (id={tr['track_id']}) shows significant movement "
                        f"in this interval (e.g. driving in, walking)."
                    ),
                })
                if ce - cs >= min_clip_duration * 0.5:
                    clip_segments.append({"start_sec": cs, "end_sec": ce})

            last_m_end = motion_segs[-1][1]
            if t_end - last_m_end >= 5.0:
                events.append({
                    "event_type": "presence_after_motion",
                    "track_id": tr["track_id"],
                    "class_name": tr["class_name"],
                    "start_time": round(last_m_end, 3),
                    "end_time": round(t_end, 3),
                    "start_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], last_m_end),
                    "end_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_end),
                    "motion_level": "low",
                    "description_for_llm": (
                        f"{tr['class_name']} (id={tr['track_id']}) mostly stationary after moving."
                    ),
                })

        elif motion_mean >= motion_threshold:
            t_app_end = t_start + min(min_clip_duration, duration)
            t_dis_start = max(t_end - min_clip_duration, t_start)
            events.append({
                "event_type": "appearance",
                "track_id": tr["track_id"],
                "class_name": tr["class_name"],
                "start_time": t_start,
                "end_time": t_app_end,
                "start_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_start),
                "end_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_app_end),
                "motion_level": "high",
                "description_for_llm": f"{tr['class_name']} (id={tr['track_id']}) appears and moves.",
            })
            events.append({
                "event_type": "disappearance",
                "track_id": tr["track_id"],
                "class_name": tr["class_name"],
                "start_time": t_dis_start,
                "end_time": t_end,
                "start_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_dis_start),
                "end_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_end),
                "motion_level": "high",
                "description_for_llm": f"{tr['class_name']} (id={tr['track_id']}) leaves.",
            })
            t = t_start
            while t < t_end:
                seg_end = min(t + max_static_duration, t_end)
                if seg_end - t >= min_clip_duration:
                    clip_segments.append({"start_sec": t, "end_sec": seg_end})
                t = seg_end
        else:
            clip_dur = min(duration, max_static_duration)
            events.append({
                "event_type": "presence_static",
                "track_id": tr["track_id"],
                "class_name": tr["class_name"],
                "start_time": t_start,
                "end_time": t_end,
                "start_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_start),
                "end_bbox_xyxy": _bbox_at_time(tr["time_xyxy"], t_end),
                "motion_level": "low",
                "description_for_llm": f"{tr['class_name']} (id={tr['track_id']}) present with little motion.",
            })
            if clip_dur >= min_clip_duration:
                clip_segments.append({"start_sec": t_start, "end_sec": t_start + clip_dur})

    merged = _merge_overlapping_segments(clip_segments, min_gap=0.5)
    return events, merged
