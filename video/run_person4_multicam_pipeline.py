#!/usr/bin/env python3
"""Run multi-camera pipeline on the Person4 folder (8 AVI streams).

Stage 1: detection / Re-ID / cross-camera match. Borderline **复核** uses
``run_multi_camera_pipeline`` defaults (``use_llm_verify=None``: auto when
``OPENAI_BASE_URL`` / ``VLLM_OPENAI_BASE_URL`` / ``OPENAI_URL`` is set).

Stage 2 (optional): ``refine_multi_camera_output`` with configurable refine model
(default ``gpt-5.4``).

Requires conda env ``capstone``. LLM keys/URLs may live in the repo root ``.env``
(loaded automatically via ``python-dotenv``).

Example:
  cd /path/to/Capstone && PYTHONPATH=. python video/run_person4_multicam_pipeline.py
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path


def _load_repo_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


def _collect_camera_videos(input_dir: Path) -> dict[str, str]:
    camera_videos: dict[str, str] = {}
    for p in sorted(input_dir.glob("*.avi")):
        m = re.search(r"\.(G\d+)\.", p.name)
        if not m:
            raise ValueError(f"No .Gxxx. camera id in filename: {p.name}")
        cid = m.group(1)
        if cid in camera_videos:
            raise ValueError(f"Duplicate camera id {cid}")
        camera_videos[cid] = str(p.resolve())
    if not camera_videos:
        raise ValueError(f"No .avi files under {input_dir}")
    return camera_videos


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    _load_repo_dotenv()
    default_in = root / "video_data/Mul_camera/Person4_14-20-14-25"
    default_out = root / "data/multicam_person4"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--input-dir",
        type=Path,
        default=default_in,
        help=f"Folder with AVIs (default: {default_in})",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=default_out,
        help=f"Output directory (default: {default_out})",
    )
    ap.add_argument("--reid-device", default="cuda", help="Re-ID device (default: cuda)")
    ap.add_argument(
        "--no-llm-verify",
        action="store_true",
        help="Disable borderline VLM verification (default: LLM verify ON)",
    )
    ap.add_argument(
        "--no-campus-topology",
        action="store_true",
        help="Do not seed CameraTopologyPrior from campus zone guide v2.0",
    )
    ap.add_argument(
        "--no-refine",
        action="store_true",
        help="Skip Stage-2 VLM refine (refine_multi_camera_output)",
    )
    ap.add_argument(
        "--refine-model",
        default="gpt-5.4",
        help="RefineEventsConfig.model for vector refinement (default: gpt-5.4)",
    )
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    input_dir = args.input_dir.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    camera_videos = _collect_camera_videos(input_dir)
    logging.info("Cameras: %d — %s", len(camera_videos), sorted(camera_videos.keys()))

    out_json = out_dir / "multicam_person4_14-20-14-25.json"
    topo_json = out_dir / "camera_topology_person4.json"

    from video.factory.multi_camera_coordinator import (
        run_multi_camera_pipeline,
        save_multi_camera_output,
    )

    # Borderline 复核：None = 与 coordinator 一致（有 OPENAI_BASE_URL 等则自动开）
    verify_arg: bool | None
    if args.no_llm_verify:
        verify_arg = False
    else:
        verify_arg = None

    out = run_multi_camera_pipeline(
        camera_videos=camera_videos,
        reid_device=args.reid_device,
        model_path="n",
        tracker="botsort_reid",
        conf=0.25,
        iou=0.45,
        use_llm_verify=verify_arg,
        seed_topology_campus_guide_v2=not args.no_campus_topology,
        topology_prior_path=str(topo_json),
    )
    save_multi_camera_output(out, out_json)
    logging.info("Written: %s", out_json)
    logging.info("Topology: %s", topo_json)
    logging.info(
        "global_entities=%d merged_events=%d",
        len(out.global_entities),
        len(out.merged_events),
    )

    if not args.no_refine:
        from video.factory.refinement_runner import RefineEventsConfig, refine_multi_camera_output

        refine_cfg = RefineEventsConfig(model=args.refine_model, mode="vector")
        logging.info("Stage-2 refine: model=%s mode=vector", refine_cfg.model)
        refined = refine_multi_camera_output(out, config=refine_cfg)
        refined_path = out_dir / "multicam_person4_refined_vector.json"
        refined_path.write_text(
            json.dumps(refined, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logging.info("Written: %s", refined_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
