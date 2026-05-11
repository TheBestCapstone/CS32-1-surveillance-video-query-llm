"""
scripts/generate_mevid_vector_flat.py
--------------------------------------
Converts MEVID pipeline cache → per-video *_events_vector_flat.json seed files
required by ragas_eval_runner.py (Chroma + SQLite).

Run AFTER test_mevid_full.py has populated the pipeline cache, OR let this
script run the pipeline inline with --run-pipeline.

Output: agent/test/data/events_vector_flat/<video_id>_events_vector_flat.json
        (one file per unique video_id across all 6 slots / ~48 files)

Usage
-----
    # Requires pipeline cache to already exist
    python scripts/generate_mevid_vector_flat.py

    # Run pipeline first, then convert (needs videos in _data/mevid_slots/)
    python scripts/generate_mevid_vector_flat.py --run-pipeline --reid-device cuda

    # Single slot
    python scripts/generate_mevid_vector_flat.py --slot 16-35

    # Force overwrite existing output files
    python scripts/generate_mevid_vector_flat.py --force
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from video.indexing.search_enrichment import enrich_event_for_search  # noqa: E402

PIPELINE_CACHE_DIR = ROOT / "_cache" / "mevid_pipeline"
OUT_DIR = ROOT / "agent" / "test" / "data" / "events_vector_flat"

# ── Slot → camera → stem ──────────────────────────────────────────────────────
SLOT_CAMERAS: dict[str, dict[str, str]] = {
    "11-20": {
        "G329": "2018-03-11.11-20-00.11-25-00.admin.G329.r13",
        "G330": "2018-03-11.11-20-00.11-25-00.school.G330.r13",
        "G336": "2018-03-11.11-20-00.11-25-00.school.G336.r13",
        "G419": "2018-03-11.11-20-00.11-25-00.school.G419.r13",
        "G420": "2018-03-11.11-20-00.11-25-00.school.G420.r13",
        "G421": "2018-03-11.11-20-00.11-25-00.school.G421.r13",
        "G423": "2018-03-11.11-20-00.11-25-00.school.G423.r13",
        "G508": "2018-03-11.11-20-00.11-25-00.bus.G508.r13",
    },
    "11-55": {
        "G299": "2018-03-11.11-55-00.12-00-00.school.G299.r13",
        "G328": "2018-03-11.11-55-00.12-00-00.school.G328.r13",
        "G330": "2018-03-11.11-55-00.12-00-00.school.G330.r13",
        "G419": "2018-03-11.11-55-00.12-00-00.school.G419.r13",
        "G420": "2018-03-11.11-55-00.12-00-00.school.G420.r13",
        "G506": "2018-03-11.11-55-00.12-00-00.bus.G506.r13",
        "G508": "2018-03-11.11-55-00.12-00-00.bus.G508.r13",
    },
    "13-50": {
        "G328": "2018-03-11.13-50-01.13-55-01.school.G328.r13",
        "G329": "2018-03-11.13-50-01.13-55-01.admin.G329.r13",
        "G339": "2018-03-11.13-50-01.13-55-01.school.G339.r13",
        "G421": "2018-03-11.13-50-01.13-55-01.school.G421.r13",
        "G424": "2018-03-11.13-50-01.13-55-01.school.G424.r13",
        "G506": "2018-03-11.13-50-01.13-55-01.bus.G506.r13",
        "G508": "2018-03-11.13-50-01.13-55-01.bus.G508.r13",
    },
    "14-20": {
        "G328": "2018-03-11.14-20-01.14-25-01.school.G328.r13",
        "G339": "2018-03-11.14-20-01.14-25-01.school.G339.r13",
        "G419": "2018-03-11.14-20-01.14-25-01.school.G419.r13",
        "G421": "2018-03-11.14-20-01.14-25-01.school.G421.r13",
        "G423": "2018-03-11.14-20-01.14-25-01.school.G423.r13",
        "G505": "2018-03-11.14-20-01.14-25-01.bus.G505.r13",
        "G506": "2018-03-11.14-20-01.14-25-01.bus.G506.r13",
        "G508": "2018-03-11.14-20-01.14-25-01.bus.G508.r13",
    },
    "16-20": {
        "G326": "2018-03-11.16-20-01.16-25-01.admin.G326.r13",
        "G328": "2018-03-11.16-20-01.16-25-01.school.G328.r13",
        "G329": "2018-03-11.16-20-01.16-25-01.admin.G329.r13",
        "G336": "2018-03-11.16-20-01.16-25-01.school.G336.r13",
        "G419": "2018-03-11.16-20-01.16-25-01.school.G419.r13",
        "G420": "2018-03-11.16-20-01.16-25-01.school.G420.r13",
        "G506": "2018-03-11.16-20-01.16-25-01.bus.G506.r13",
        "G508": "2018-03-11.16-20-01.16-25-01.bus.G508.r13",
    },
    "16-35": {
        "G326": "2018-03-11.16-35-01.16-40-01.admin.G326.r13",
        "G328": "2018-03-11.16-35-01.16-40-01.school.G328.r13",
        "G329": "2018-03-11.16-35-01.16-40-01.admin.G329.r13",
        "G336": "2018-03-11.16-35-01.16-40-01.school.G336.r13",
        "G339": "2018-03-11.16-35-01.16-40-01.school.G339.r13",
        "G419": "2018-03-11.16-35-01.16-40-01.school.G419.r13",
        "G420": "2018-03-11.16-35-01.16-40-01.school.G420.r13",
        "G423": "2018-03-11.16-35-01.16-40-00.school.G423.r13",
        "G506": "2018-03-11.16-35-01.16-40-01.bus.G506.r13",
        "G638": "2018-03-11.16-35-01.16-40-01.school.G638.r13",
    },
}

# Location token in stem → scene_zone
_LOCATION_ZONE = {"admin": "road", "school": "yard", "bus": "road"}

# Common colors to look for in event text
_COLORS = [
    "red", "blue", "green", "black", "white", "yellow",
    "orange", "grey", "gray", "brown", "purple", "pink",
    "dark", "light",
]

_APPEARANCE_TERMS = [
    "hoodie", "jacket", "coat", "shirt", "t-shirt", "pants", "trousers",
    "jeans", "shorts", "skirt", "dress", "bag", "backpack", "handbag",
    "hat", "cap", "hood", "scarf", "fur", "collar", "long", "sleeve",
]

_COLOR_ALIASES = {
    "gray": "grey",
    "light gray": "light_grey",
    "light grey": "light_grey",
    "dark gray": "dark_grey",
    "dark grey": "dark_grey",
    "silver gray": "silver_grey",
    "silver grey": "silver_grey",
}

_STOPWORDS = {
    "a", "an", "the", "is", "in", "at", "to", "of", "and", "or",
    "from", "with", "for", "by", "on", "into", "that", "this",
    "was", "were", "has", "have", "had", "be", "been", "are",
    "its", "it", "he", "she", "they", "person", "camera",
    "unknown",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _zone_from_stem(stem: str) -> str:
    """Infer scene_zone from location token in video stem."""
    for loc, zone in _LOCATION_ZONE.items():
        if f".{loc}." in stem:
            return zone
    return "unknown"


def _extract_color(text: str) -> str:
    tl = text.lower()
    for phrase, alias in _COLOR_ALIASES.items():
        if phrase in tl:
            return alias
    for c in _COLORS:
        if c in tl:
            return _COLOR_ALIASES.get(c, c)
    return "unknown"


def _extract_keywords(text: str, max_k: int = 6) -> list[str]:
    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
    seen: dict[str, None] = {}
    for w in words:
        if w not in _STOPWORDS:
            seen[w] = None
    return list(seen)[:max_k]


def _normalize_keywords(value: object, fallback_text: str = "", max_k: int = 6) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        seen: set[str] = set()
        for item in value:
            token = str(item).strip().lower().replace(" ", "_")
            if token and token not in seen:
                out.append(token)
                seen.add(token)
        if out:
            return out[:max_k]
    if isinstance(value, str) and value.strip():
        out = []
        seen = set()
        for token in re.split(r"[,;/\s]+", value.strip().lower()):
            token = token.strip().replace(" ", "_")
            if token and token not in seen and token not in _STOPWORDS:
                out.append(token)
                seen.add(token)
        if out:
            return out[:max_k]
    return _extract_keywords(fallback_text, max_k=max_k)


def _appearance_keywords(text: str) -> list[str]:
    tl = text.lower().replace("-", " ")
    out: list[str] = []
    seen: set[str] = set()

    def add(token: str) -> None:
        token = token.strip().lower().replace(" ", "_")
        if token and token != "unknown" and token not in seen:
            out.append(token)
            seen.add(token)

    for phrase, alias in _COLOR_ALIASES.items():
        if phrase in tl:
            add(alias)
    for c in _COLORS:
        if re.search(rf"\b{re.escape(c)}\b", tl):
            add(_COLOR_ALIASES.get(c, c))
    for term in _APPEARANCE_TERMS:
        term_re = term.replace("-", r"[-\s]?")
        if re.search(rf"\b{term_re}\b", tl):
            add(term.replace("-", "_"))

    # Useful compounds for natural-language clothing queries.
    if ("light grey" in tl or "light gray" in tl) and "hoodie" in tl:
        add("light_grey_hoodie")
    if ("dark" in tl or "black" in tl) and "coat" in tl:
        add("dark_coat")
    if ("black" in tl or "dark" in tl) and "hood" in tl:
        add("hood_up")
    if "fur" in tl and ("hood" in tl or "collar" in tl):
        add("fur_trimmed_hood")
    return out


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _is_unknown_text(value: object) -> bool:
    txt = _clean_text(value).lower()
    return txt in {"", "unknown", "n/a", "none", "null"}


def _append_unique(items: list[str], extra: list[str], max_len: int = 12) -> list[str]:
    seen = set(items)
    for token in extra:
        token = str(token).strip().lower().replace(" ", "_")
        if token and token != "unknown" and token not in seen:
            items.append(token)
            seen.add(token)
        if len(items) >= max_len:
            break
    return items


def _event_key_from_time(ev: dict) -> tuple[float, float, str]:
    return (
        round(float(ev.get("start_time", 0.0)), 1),
        round(float(ev.get("end_time", 0.0)), 1),
        str(ev.get("object_type") or ev.get("class_name") or "").lower(),
    )


def _fmt_sec(s: float) -> str:
    m, sec = divmod(int(s), 60)
    return f"{m}:{sec:02d}"


def _get_video_duration(video_path: Path) -> float:
    """Get duration via OpenCV; fall back to 300.0 (5-min MEVID clip)."""
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        n   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        if n > 0 and fps > 0:
            return n / fps
    except Exception:
        pass
    return 300.0  # default 5-minute MEVID clip


# ── Core conversion ───────────────────────────────────────────────────────────

def pipeline_events_to_vector_flat(
    video_id: str,
    camera_id: str,
    events: list[dict],
    global_entities: list[dict],
    duration: float,
    refined_events: list[dict] | None = None,
) -> dict:
    """Convert pipeline CameraResult events → vector_flat dict."""

    # Build track_id → global_entity_id lookup plus entity trajectory text for
    # cross-camera RAG. The agent needs this even when LLM refinement is disabled.
    track_to_entity: dict[int, str] = {}
    entity_to_apps: dict[str, list[dict]] = {}
    for ge in global_entities:
        entity_id = str(ge.get("global_entity_id") or "")
        if entity_id:
            entity_to_apps[entity_id] = list(ge.get("appearances", []))
        for app in ge.get("appearances", []):
            if app.get("camera_id") == camera_id:
                tid = app.get("track_id")
                if tid is not None:
                    track_to_entity[int(tid)] = ge["global_entity_id"]

    # Build refined event lookup. New refined outputs include track_id; older caches may
    # not, so keep a time/class fallback for compatibility.
    refined_by_track: dict[int, dict] = {}
    refined_by_time: dict[tuple[float, float, str], dict] = {}
    if refined_events:
        for ev in refined_events:
            tid = ev.get("track_id")
            if tid is not None:
                try:
                    refined_by_track[int(tid)] = ev
                except Exception:
                    pass
            refined_by_time[_event_key_from_time(ev)] = ev

    scene_zone = _zone_from_stem(video_id)

    flat_events: list[dict] = []
    for idx, ev in enumerate(events, start=1):
        t_start = float(ev.get("start_time", 0.0))
        t_end   = float(ev.get("end_time",   t_start + 1.0))
        cls     = ev.get("class_name") or ev.get("object_type") or "person"
        tid     = ev.get("track_id", idx)
        entity_id = track_to_entity.get(int(tid) if isinstance(tid, (int, float)) else idx, "")

        refined_event = None
        if isinstance(tid, (int, float)):
            refined_event = refined_by_track.get(int(tid))
        if refined_event is None:
            refined_event = refined_by_time.get(_event_key_from_time(ev))

        # Prefer LLM-refined fields; fall back to generated pipeline text.
        refined_text = ""
        refined_color = ""
        refined_appearance = ""
        refined_keywords: list[str] = []
        refined_entity_hint = ""
        if refined_event:
            refined_text = _clean_text(refined_event.get("event_text") or refined_event.get("description"))
            refined_color = _clean_text(refined_event.get("object_color"))
            if refined_color.lower() == "unknown":
                refined_color = ""
            refined_appearance = _clean_text(refined_event.get("appearance_notes"))
            if _is_unknown_text(refined_appearance):
                refined_appearance = ""
            refined_keywords = _normalize_keywords(refined_event.get("keywords"), refined_text)
            refined_entity_hint = _clean_text(refined_event.get("entity_hint"))

        refined_text = refined_text or ev.get("event_text", "")

        cross_camera_text = ""
        if entity_id:
            apps = sorted(
                entity_to_apps.get(entity_id, []),
                key=lambda a: float(a.get("start_time", 0.0)),
            )
            if apps:
                chain = " -> ".join(
                    f"{a.get('camera_id')} track#{a.get('track_id')} "
                    f"{_fmt_sec(float(a.get('start_time', 0.0)))}-"
                    f"{_fmt_sec(float(a.get('end_time', 0.0)))}"
                    for a in apps
                )
                cams = ", ".join(dict.fromkeys(str(a.get("camera_id")) for a in apps))
                cross_camera_text = (
                    f" cross-camera same-person candidate {entity_id}; "
                    f"seen in cameras {cams}; trajectory {chain}."
                )

        if refined_text:
            event_text = refined_text
        else:
            event_text = (
                f"From {t_start:.1f}s to {t_end:.1f}s, {cls} "
                f"(track #{tid}) detected in camera {camera_id} "
                f"({_fmt_sec(t_start)}–{_fmt_sec(t_end)})"
            )
        if cross_camera_text and cross_camera_text not in event_text:
            event_text += cross_camera_text

        if refined_color:
            color = refined_color
        else:
            color = _extract_color(" ".join([refined_appearance, refined_text]))
        keywords = [
            k for k in (refined_keywords or _extract_keywords(" ".join([event_text, refined_appearance])))
            if str(k).strip().lower() != "unknown"
        ]
        if camera_id.lower() not in keywords:
            keywords = [camera_id.lower()] + keywords
        keywords = _append_unique(
            keywords,
            _appearance_keywords(" ".join([refined_appearance, refined_text, event_text])),
        )
        if entity_id:
            for token in ("cross_camera", "same_person", entity_id.lower()):
                if token not in keywords:
                    keywords.append(token)

        motion_desc = ev.get("motion_description", "")
        if refined_appearance:
            appearance_notes = refined_appearance
        elif motion_desc:
            appearance_notes = f"High activity; {motion_desc}"
        elif refined_text and not _is_unknown_text(refined_text):
            appearance_notes = f"Observed event; {refined_text}"
        else:
            appearance_notes = (
                f"Observed event; {cls} present from "
                f"{_fmt_sec(t_start)} to {_fmt_sec(t_end)}"
            )
        if entity_id:
            apps = entity_to_apps.get(entity_id, [])
            cams = ", ".join(dict.fromkeys(str(a.get("camera_id")) for a in apps))
            if cams and "same-person candidate" not in appearance_notes:
                appearance_notes += f"; same-person candidate {entity_id} across {cams}"

        entity_hint = f"track_{tid}"
        if refined_entity_hint:
            entity_hint = refined_entity_hint
        elif entity_id:
            entity_hint = f"{entity_id}_{camera_id}"

        record = {
            "video_id":       video_id,
            "camera_id":      camera_id,
            "track_id":       tid,
            "entity_hint":    entity_hint,
            "clip_start_sec": 0.0,
            "clip_end_sec":   duration,
            "start_time":     t_start,
            "end_time":       t_end,
            "object_type":    cls,
            "object_color":   color,
            "appearance_notes": appearance_notes,
            "scene_zone":     scene_zone,
            "event_text":     event_text,
            "keywords":       keywords,
            "start_bbox_xyxy": [None, None, None, None],
            "end_bbox_xyxy":   [None, None, None, None],
            # cross-camera context
            "global_entity_id": entity_id or None,
        }
        flat_events.append(
            enrich_event_for_search(
                record,
                camera_id=camera_id,
                global_entity_id=entity_id,
                trajectory_text=cross_camera_text.strip(),
            )
        )

    return {
        "video_id": video_id,
        "duration": duration,
        "camera_id": camera_id,
        "events": flat_events,
    }


# ── Inline pipeline runner (used by --run-pipeline) ───────────────────────────

def run_and_cache_pipeline(slot: str, video_dir: Path, reid_device: str) -> dict:
    """Import and run the multi-camera pipeline; save cache."""
    from video.factory.multi_camera_coordinator import run_multi_camera_pipeline
    from video.core.schema.multi_camera import CrossCameraConfig

    cam_map = SLOT_CAMERAS[slot]
    camera_videos = {
        cam: str(video_dir / f"{stem}.avi")
        for cam, stem in cam_map.items()
        if (video_dir / f"{stem}.avi").exists()
    }
    if not camera_videos:
        print(f"  [{slot}] No videos found — skipping")
        return {}

    config = CrossCameraConfig(
        max_transition_sec=300.0,
        embedding_threshold=0.60,
        cross_camera_min_score=0.60,
        person_only=True,
    )
    print(f"  [{slot}] Running pipeline on {list(camera_videos)} …")
    t0 = time.time()
    mc = run_multi_camera_pipeline(
        camera_videos=camera_videos,
        config=config,
        reid_device=reid_device,
        num_crops=5,
        model_path="11m",
        conf=0.25,
        iou=0.25,
    )

    # Serialise (skip ndarray fields)
    per_cam = [
        {
            "camera_id": cr.camera_id,
            "events":    cr.events,
            "clips":     cr.clips,
            "meta":      cr.meta,
        }
        for cr in mc.per_camera
    ]
    entities = [
        {
            "global_entity_id": ge.global_entity_id,
            "appearances": [
                {"camera_id": a.camera_id, "track_id": a.track_id,
                 "start_time": a.start_time, "end_time": a.end_time,
                 "confidence": a.confidence}
                for a in ge.appearances
            ],
        }
        for ge in mc.global_entities
    ]
    result = {
        "slot": slot,
        "elapsed_sec": round(time.time() - t0, 1),
        "cameras_run": list(camera_videos),
        "global_entities": entities,
        "per_camera": per_cam,
        "merged_events": mc.merged_events,
    }
    PIPELINE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = PIPELINE_CACHE_DIR / f"{slot}_pipeline.json"
    cache.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [{slot}] Done in {result['elapsed_sec']}s — cached to {cache}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate *_events_vector_flat.json seed files from MEVID pipeline cache"
    )
    ap.add_argument("--slot", default="", help="Process one slot only, e.g. 16-35")
    ap.add_argument("--video-dir", default="_data/mevid_slots",
                    help="Directory with downloaded .avi files (needed for duration + --run-pipeline)")
    ap.add_argument("--out-dir", default=str(OUT_DIR),
                    help="Output directory for vector flat JSON files")
    ap.add_argument("--run-pipeline", action="store_true",
                    help="Run YOLO+ReID pipeline if cache is missing (slow, ~30 min/slot)")
    ap.add_argument("--reid-device", default="cpu",
                    help="ReID device when --run-pipeline is set (cpu | cuda)")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing output files")
    args = ap.parse_args()

    video_dir = ROOT / args.video_dir
    out_dir   = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    slots = [args.slot] if args.slot else list(SLOT_CAMERAS)

    written = skipped = errors = 0

    for slot in slots:
        cache_file = PIPELINE_CACHE_DIR / f"{slot}_pipeline.json"
        refined_file = PIPELINE_CACHE_DIR / f"{slot}_refined.json"
        appearance_refined_file = PIPELINE_CACHE_DIR / f"{slot}_appearance_refined.json"

        # Load or generate pipeline cache
        if cache_file.exists():
            pipeline = json.loads(cache_file.read_text(encoding="utf-8"))
            print(f"[{slot}] Loaded pipeline cache: "
                  f"{len(pipeline.get('per_camera', []))} cameras, "
                  f"{len(pipeline.get('global_entities', []))} entities")
        elif args.run_pipeline:
            print(f"[{slot}] No cache found — running pipeline …")
            pipeline = run_and_cache_pipeline(slot, video_dir, args.reid_device)
            if not pipeline:
                errors += 1
                continue
        else:
            print(f"[{slot}] ✗  No pipeline cache at {cache_file}")
            print(f"         Run: python tests/test_mevid_full.py --slot {slot} --video-dir {args.video_dir}")
            print(f"         Or:  python scripts/generate_mevid_vector_flat.py --slot {slot} --run-pipeline")
            errors += 1
            continue

        # Load refined events if available
        refined_by_cam: dict[str, list[dict]] = {}
        if refined_file.exists():
            refined = json.loads(refined_file.read_text(encoding="utf-8"))
            for cam_id, cam_data in refined.get("per_camera", {}).items():
                refined_by_cam[cam_id] = cam_data.get("events", [])
            print(f"[{slot}] Loaded LLM-refined events for {len(refined_by_cam)} cameras")
        if appearance_refined_file.exists():
            appearance_refined = json.loads(appearance_refined_file.read_text(encoding="utf-8"))
            loaded = 0
            for cam_id, cam_data in appearance_refined.get("per_camera", {}).items():
                refined_by_cam.setdefault(cam_id, [])
                refined_by_cam[cam_id].extend(cam_data.get("events", []))
                loaded += 1
            print(f"[{slot}] Loaded crop-based appearance refinement for {loaded} cameras")

        global_entities = pipeline.get("global_entities", [])
        per_camera = {cr["camera_id"]: cr for cr in pipeline.get("per_camera", [])}

        cam_map = SLOT_CAMERAS[slot]
        for cam_id, stem in cam_map.items():
            if cam_id not in per_camera:
                print(f"  [{slot}/{cam_id}] not in pipeline cache — skipped")
                continue

            out_file = out_dir / f"{stem}_events_vector_flat.json"
            if out_file.exists() and not args.force:
                print(f"  [{slot}/{cam_id}] already exists — skip (use --force to overwrite)")
                skipped += 1
                continue

            cam_result = per_camera[cam_id]
            events     = cam_result.get("events", [])

            # Get video duration
            video_path = video_dir / f"{stem}.avi"
            duration   = _get_video_duration(video_path) if video_path.exists() else 300.0

            flat = pipeline_events_to_vector_flat(
                video_id        = stem,
                camera_id       = cam_id,
                events          = events,
                global_entities = global_entities,
                duration        = duration,
                refined_events  = refined_by_cam.get(cam_id),
            )

            out_file.write_text(
                json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"  [{slot}/{cam_id}] ✓  {len(flat['events'])} events → {out_file.name}")
            written += 1

    print(f"\nDone.  Written={written}  Skipped={skipped}  Errors={errors}")
    if written > 0:
        print(f"Output directory: {out_dir}")
        print("\nNext steps:")
        print("  1. Add OPENAI_API_KEY to .env")
        print("  2. python agent/test/ragas_eval_runner.py \\")
        print("       --xlsx-path agent/test/data/agent_test_mevid.xlsx \\")
        print(f"      --seed-dir {out_dir} \\")
        print("       --prepare-subset-db \\")
        print("       --limit 100")


if __name__ == "__main__":
    main()
