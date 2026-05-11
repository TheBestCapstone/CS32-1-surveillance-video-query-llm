#!/usr/bin/env python3
"""Intrinsic evaluation of Person4 multicam outputs (no ground-truth labels required).

Reads:
  - Stage 1: multicam_person4_14-20-14-25.json
  - Stage 2: multicam_person4_refined_vector.json

Produces descriptive metrics: entity counts, cross-camera linkage, per-camera events,
refined field coverage, object_type mix. For supervised P/R/F1 against identities,
use MEVID tooling (tests/eval_multicam_entity.py) with annotation zip + matching scenario.

Usage (repo root, conda capstone):
  python agent/test_mulcamera/eval_person4_outputs.py \\
    --stage1 data/multicam_person4/multicam_person4_14-20-14-25.json \\
    --refined data/multicam_person4/multicam_person4_refined_vector.json \\
    --out agent/test_mulcamera/eval_person4_report.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def eval_stage1(data: dict[str, Any]) -> dict[str, Any]:
    entities = data.get("global_entities", [])
    merged = data.get("events", [])
    meta = data.get("meta", {})
    cams = list(meta.get("cameras", {}).keys())

    per_entity = []
    multi_cam_entities = 0
    for ent in entities:
        apps = ent.get("appearances", [])
        cam_set = {a["camera_id"] for a in apps}
        confs = [float(a.get("confidence", 0.0)) for a in apps]
        row = {
            "global_entity_id": ent.get("global_entity_id"),
            "n_appearances": len(apps),
            "n_distinct_cameras": len(cam_set),
            "cameras": sorted(cam_set),
            "mean_confidence": sum(confs) / len(confs) if confs else 0.0,
        }
        per_entity.append(row)
        if len(cam_set) >= 2:
            multi_cam_entities += 1

    ev_by_cam: dict[str, int] = defaultdict(int)
    with_gid = 0
    for ev in merged:
        cid = ev.get("camera_id")
        if cid:
            ev_by_cam[str(cid)] += 1
        if ev.get("global_entity_id"):
            with_gid += 1

    return {
        "n_cameras_configured": len(cams),
        "camera_ids": sorted(cams),
        "n_global_entities": len(entities),
        "n_multi_camera_entities_cam_ge_2": multi_cam_entities,
        "n_merged_events": len(merged),
        "merged_events_with_global_entity_id": with_gid,
        "fraction_merged_tagged_global": round(with_gid / len(merged), 4) if merged else 0.0,
        "merged_events_per_camera": dict(sorted(ev_by_cam.items())),
        "entities_detail": per_entity,
    }


def eval_refined(data: dict[str, Any]) -> dict[str, Any]:
    """data is cam_id -> { video_id, events: [...] }"""
    total = 0
    by_cam: dict[str, int] = {}
    obj_types = Counter()
    with_entity_hint = 0
    with_keywords_nonempty = 0

    for cam_id, payload in data.items():
        evs = payload.get("events", []) if isinstance(payload, dict) else []
        by_cam[cam_id] = len(evs)
        total += len(evs)
        for ev in evs:
            ot = ev.get("object_type") or "unknown"
            obj_types[ot] += 1
            if ev.get("entity_hint"):
                with_entity_hint += 1
            kws = ev.get("keywords") or []
            if isinstance(kws, list) and len(kws) > 0:
                with_keywords_nonempty += 1

    return {
        "n_cameras": len(data),
        "n_refined_events_total": total,
        "refined_events_per_camera": dict(sorted(by_cam.items())),
        "object_type_counts": dict(obj_types),
        "entity_hint_non_null_count": with_entity_hint,
        "fraction_entity_hint_set": round(with_entity_hint / total, 4) if total else 0.0,
        "fraction_keywords_nonempty": round(with_keywords_nonempty / total, 4) if total else 0.0,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stage1",
        type=Path,
        default=root / "data/multicam_person4/multicam_person4_14-20-14-25.json",
    )
    ap.add_argument(
        "--refined",
        type=Path,
        default=root / "data/multicam_person4/multicam_person4_refined_vector.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "eval_person4_report.json",
    )
    args = ap.parse_args()

    s1_path = args.stage1.expanduser().resolve()
    rf_path = args.refined.expanduser().resolve()

    report: dict[str, Any] = {
        "inputs": {"stage1": str(s1_path), "refined": str(rf_path)},
        "notes": [
            "No GT identity labels for Person4 in-repo: metrics are intrinsic/diagnostic only.",
            "For supervised entity P/R/F1 use tests/eval_multicam_entity.py with MEVID annotations.",
        ],
    }

    if s1_path.is_file():
        report["stage1_intrinsic"] = eval_stage1(_load(s1_path))
    else:
        report["stage1_intrinsic"] = None
        report["stage1_error"] = f"missing file: {s1_path}"

    if rf_path.is_file():
        report["stage2_refined_intrinsic"] = eval_refined(_load(rf_path))
    else:
        report["stage2_refined_intrinsic"] = None
        report["stage2_error"] = f"missing file: {rf_path}"

    out_path = args.out.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
