#!/usr/bin/env python3
"""Convert Stage 2 UCA dense captions (*_events_uca.json) to vector_flat format
that the database builders (SQLiteBuilder / ChromaBuilder) can consume.

Usage::

    conda activate capstone
    python scripts/convert_uca_to_vector_flat.py \
        --input-dir data/part4_pipeline_output \
        --output-dir data/part4_pipeline_output/uca_vector_flat
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _infer_keywords(sentence: str) -> list[str]:
    """Extract simple keyword hints from a UCA sentence.

    This is intentionally lightweight — the sentence text itself is the main
    content that retrieval will work against. Keywords help SQLite filtering.
    """
    low = sentence.lower()
    keywords: set[str] = set()

    # Objects
    for kw in ["car", "cars", "truck", "trucks", "vehicle", "vehicles"]:
        if kw in low:
            keywords.add("vehicle")
            break
    if "person" in low or "people" in low:
        keywords.add("person")

    # Motion
    if any(w in low for w in ["walking", "walks", "running", "runs"]):
        keywords.add("walking")
    if any(w in low for w in ["driving", "drives", "moving", "moves", "passing"]):
        keywords.add("moving")
    if any(w in low for w in ["stationary", "static", "parked", "standing", "still", "remains", "remain"]):
        keywords.add("stationary")

    # Zones (domain-specific for UCFCrime gas station)
    if "gas station" in low or "forecourt" in low:
        keywords.add("gas_station")
    if "pump" in low or "pumps" in low:
        keywords.add("fuel_pump")
    if "road" in low:
        keywords.add("roadside")
    if "parking" in low:
        keywords.add("parking")
    if "entrance" in low:
        keywords.add("entrance")
    if "background" in low:
        keywords.add("background")
    if "foreground" in low:
        keywords.add("foreground")
    if "sidewalk" in low:
        keywords.add("sidewalk")

    return sorted(keywords) if keywords else ["scene_description"]


def convert_uca_file(uca_path: Path, output_dir: Path) -> Path | None:
    """Convert a single _events_uca.json → _events_vector_flat.json."""
    data: dict[str, Any] = json.loads(uca_path.read_text(encoding="utf-8"))

    video_name: str = data.get("video_name", "")
    duration: float = float(data.get("duration", 0))
    timestamps: list[list[float]] = data.get("timestamps", [])
    sentences: list[str] = data.get("sentences", [])

    if not video_name:
        print(f"  SKIP {uca_path.name}: missing video_name")
        return None

    if len(timestamps) != len(sentences):
        print(
            f"  WARN {uca_path.name}: timestamps({len(timestamps)}) != "
            f"sentences({len(sentences)}), truncating to min"
        )
        n = min(len(timestamps), len(sentences))
        timestamps = timestamps[:n]
        sentences = sentences[:n]

    video_id = f"{video_name}.mp4"
    events: list[dict[str, Any]] = []

    for i, (ts, sentence) in enumerate(zip(timestamps, sentences)):
        start = float(ts[0])
        end = float(ts[1])
        duration_sec = round(max(end - start, 0.0), 4)

        events.append({
            "video_id": video_id,
            "clip_start_sec": 0.0,
            "clip_end_sec": duration,
            "start_time": start,
            "end_time": end,
            "duration_sec": duration_sec,
            "event_text_en": sentence,
            "event_text": sentence,
            "event_summary_en": sentence,
            "keywords": _infer_keywords(sentence),
            "entity_hint": f"uca_seg_{i:03d}",
            "object_type": "",
            "object_color": "",
            "appearance_notes": "",
            "scene_zone": "",
        })

    output = {
        "video_id": video_id,
        "video_name": video_name,
        "duration": duration,
        "source_format": "uca_converted",
        "events": events,
    }

    out_path = output_dir / f"{video_name}_events_vector_flat.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert UCA dense captions to vector_flat format for DB builders"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/part4_pipeline_output"),
        help="Directory with *_events_uca.json files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/part4_pipeline_output/uca_vector_flat"),
        help="Output directory for *_events_vector_flat.json files",
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir.expanduser().resolve()
    output_dir: Path = args.output_dir.expanduser().resolve()

    if not input_dir.is_dir():
        print(f"ERROR: input directory not found: {input_dir}")
        return

    uca_files = sorted(input_dir.glob("*_events_uca.json"))
    if not uca_files:
        print(f"No *_events_uca.json files found in {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Input:  {input_dir}  ({len(uca_files)} UCA files)")
    print(f"Output: {output_dir}")

    converted = 0
    for uca_path in uca_files:
        out_path = convert_uca_file(uca_path, output_dir)
        if out_path:
            converted += 1

    print(f"\nDone. Converted {converted}/{len(uca_files)} files → {output_dir}")


if __name__ == "__main__":
    main()
