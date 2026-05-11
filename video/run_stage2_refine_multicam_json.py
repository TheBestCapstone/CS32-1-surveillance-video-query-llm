#!/usr/bin/env python3
"""Re-run Stage-2 only: ``refine_multi_camera_output`` from Stage-1 multicam JSON."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


def _load_repo_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    default_in = root / "data/multicam_person4/multicam_person4_14-20-14-25.json"
    default_out = root / "data/multicam_person4/multicam_person4_refined_vector.json"

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--multicam-json", type=Path, default=default_in, help="Stage-1 JSON path")
    ap.add_argument("--out-json", type=Path, default=default_out, help="Write refined output here")
    ap.add_argument("--refine-model", default="gpt-5.4", help="RefineEventsConfig.model")
    args = ap.parse_args()

    _load_repo_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    from video.factory.refinement_runner import (
        RefineEventsConfig,
        multicam_output_from_saved_json,
        refine_multi_camera_output,
    )

    src = args.multicam_json.expanduser().resolve()
    if not src.is_file():
        logging.error("Missing Stage-1 JSON: %s", src)
        return 1

    out = multicam_output_from_saved_json(src)
    cfg = RefineEventsConfig(model=args.refine_model, mode="vector")
    logging.info("Refine model=%s mode=vector", cfg.model)
    refined = refine_multi_camera_output(out, config=cfg)

    out_path = args.out_json.expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(refined, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Written %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
