#!/usr/bin/env python3
"""Run ragas_eval_runner for Part4 cases of a single video + write a detailed text report.

Example::

    conda activate capstone
    cd agent/test
    python ../../scripts/run_single_video_part4_eval_detail.py \\
        --video-id Normal_Videos_594_x264 \\
        --seed-dir ../../data/part4_pipeline_output/uca_vector_flat \\
        --output-dir ../../data/part4_pipeline_output/single_video_eval_594
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENT_TEST = ROOT / "agent" / "test"
RAGAS_RUNNER = AGENT_TEST / "ragas_eval_runner.py"
DEFAULT_XLSX = AGENT_TEST / "data" / "agent_test.xlsx"


def resolve_seed_file(seed_dir: Path, video_id: str) -> Path | None:
    vid = video_id.strip()
    p = seed_dir / f"{vid}_events_vector_flat.json"
    if p.is_file():
        return p
    if vid.startswith("Normal_Videos_"):
        alt = vid.replace("Normal_Videos_", "Normal_Videos", 1)
        p2 = seed_dir / f"{alt}_events_vector_flat.json"
        if p2.is_file():
            return p2
    if vid.startswith("Normal_Videos") and not vid.startswith("Normal_Videos_"):
        suffix = vid[len("Normal_Videos") :]
        if suffix and suffix[0].isdigit():
            p3 = seed_dir / f"Normal_Videos_{suffix}_events_vector_flat.json"
            if p3.is_file():
                return p3
    return None


def _load_part4_cases(xlsx: Path) -> list[dict[str, Any]]:
    sys.path.insert(0, str(AGENT_TEST))
    from agent_test_importer import AgentTestDatasetImporter, AgentTestImportConfig

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        cfg = AgentTestImportConfig(
            xlsx_path=xlsx,
            output_dir=t,
            sqlite_path=t / "agent_test_eval.sqlite",
            normalized_json_path=t / "agent_test_normalized.json",
            report_json_path=t / "agent_test_import_report.json",
            retrieval_view_path=t / "agent_test_retrieval_eval.json",
            e2e_view_path=t / "agent_test_e2e_eval.json",
            generation_view_path=t / "agent_test_generation_eval.json",
            reset_existing=True,
            include_sheets=["Part4"],
        )
        AgentTestDatasetImporter(cfg).build()
        return json.loads(cfg.normalized_json_path.read_text(encoding="utf-8"))


def _norm_vid(v: str) -> str:
    x = (v or "").strip()
    if x.lower().endswith(".mp4"):
        x = x[:-4]
    if x.startswith("Normal_Videos_"):
        suf = x[len("Normal_Videos_") :]
        if suf and suf[0].isdigit():
            return "Normal_Videos" + suf
    return x


def _vid_from_ctx(ctx: str) -> str:
    m = re.match(r"^Video\s+(\S+)\.", str(ctx or "").strip(), flags=re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _wrong_share(case: dict[str, Any], exp: str) -> float | None:
    ctxs = case.get("retrieved_contexts") or []
    if not ctxs:
        return None
    ne = _norm_vid(exp)
    wrong = sum(1 for t in ctxs if _norm_vid(_vid_from_ctx(t)) != ne)
    return wrong / len(ctxs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-video Part4 RAGAS eval + detail report")
    parser.add_argument("--video-id", type=str, required=True, help="Case video_id as in xlsx (e.g. Normal_Videos_594_x264)")
    parser.add_argument("--seed-dir", type=Path, required=True, help="Directory with *_events_vector_flat.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory (created)")
    parser.add_argument("--xlsx-path", type=Path, default=DEFAULT_XLSX)
    parser.add_argument(
        "--ragas-contexts-filter",
        type=str,
        default="none",
        choices=["none", "same_expected_video"],
        help="Forwarded to ragas_eval_runner.py",
    )
    parser.add_argument(
        "--retrieval-metrics-backend",
        type=str,
        default="llm",
        choices=["llm", "id_based"],
        help="Forwarded to ragas_eval_runner.py (id_based = video-id overlap, no LLM for prec/recall)",
    )
    args = parser.parse_args()

    video_id = args.video_id.strip()
    seed_dir = args.seed_dir.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    xlsx = args.xlsx_path.expanduser().resolve()

    if not xlsx.is_file():
        print(f"ERROR: xlsx not found: {xlsx}", file=sys.stderr)
        sys.exit(1)
    if not seed_dir.is_dir():
        print(f"ERROR: seed dir not found: {seed_dir}", file=sys.stderr)
        sys.exit(1)

    seed_src = resolve_seed_file(seed_dir, video_id)
    if seed_src is None:
        print(f"ERROR: no seed file for video_id={video_id!r} under {seed_dir}", file=sys.stderr)
        sys.exit(1)

    all_cases = _load_part4_cases(xlsx)
    ready = [c for c in all_cases if c.get("e2e_ready") == 1]
    exp_n = _norm_vid(video_id)
    cases = [c for c in ready if _norm_vid(str(c.get("video_id", ""))) == exp_n]
    if not cases:
        print(f"ERROR: no e2e-ready Part4 cases for video_id={video_id!r} (normalized={exp_n!r})", file=sys.stderr)
        sys.exit(1)

    out.mkdir(parents=True, exist_ok=True)
    seeds = out / "single_seeds"
    if seeds.exists():
        shutil.rmtree(seeds)
    seeds.mkdir(parents=True)
    shutil.copy2(seed_src, seeds / seed_src.name)

    case_ids_path = out / "case_ids.txt"
    case_ids_path.write_text("\n".join(str(c["case_id"]) for c in cases) + "\n", encoding="utf-8")

    meta_path = out / "run_meta.json"
    started = datetime.now(timezone.utc).isoformat()
    meta = {
        "started_utc": started,
        "video_id": video_id,
        "normalized_video_id": exp_n,
        "case_ids": [c["case_id"] for c in cases],
        "case_count": len(cases),
        "seed_source": str(seed_src),
        "seed_copied_to": str(seeds / seed_src.name),
        "ragas_contexts_filter": args.ragas_contexts_filter,
        "retrieval_metrics_backend": args.retrieval_metrics_backend,
        "ragas_runner": str(RAGAS_RUNNER),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(RAGAS_RUNNER),
        "--xlsx-path",
        str(xlsx),
        "--output-dir",
        str(out / "eval_output"),
        "--seed-dir",
        str(seeds),
        "--case-ids-file",
        str(case_ids_path),
        "--prepare-subset-db",
        "--include-sheets",
        "Part4",
        "--ragas-contexts-filter",
        args.ragas_contexts_filter,
        "--retrieval-metrics-backend",
        args.retrieval_metrics_backend,
    ]
    log_path = out / "console.log"
    cmd_txt = out / "command.txt"
    cmd_txt.write_text(" ".join(cmd) + "\n", encoding="utf-8")

    env = {**__import__("os").environ, "AGENT_BUILD_VIDEO_COLLECTION": "1"}
    log_fp = open(log_path, "w", encoding="utf-8")
    log_fp.write(f"# started {started}\n# cwd {AGENT_TEST}\n# cmd:\n")
    log_fp.write(" ".join(cmd) + "\n\n")
    log_fp.flush()
    proc = subprocess.run(
        cmd,
        cwd=str(AGENT_TEST),
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_fp.write(f"\n# exit_code={proc.returncode}\n")
    log_fp.close()

    eval_out = out / "eval_output"
    detail_path = out / "evaluation_detail.txt"
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("Single-video Part4 RAGAS evaluation — detail")
    lines.append("=" * 72)
    lines.append(f"UTC end: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"video_id (xlsx): {video_id}")
    lines.append(f"normalized id:  {exp_n}")
    lines.append(f"cases: {len(cases)}  -> {', '.join(str(c['case_id']) for c in cases)}")
    lines.append(f"seed file: {seed_src}")
    lines.append(f"ragas_contexts_filter: {args.ragas_contexts_filter}")
    lines.append(f"retrieval_metrics_backend: {args.retrieval_metrics_backend}")
    lines.append(f"subprocess exit: {proc.returncode}")
    lines.append(f"full console log: {log_path}")
    lines.append("")

    summ_path = eval_out / "summary_report.json"
    e2e_path = eval_out / "e2e_report.json"
    if proc.returncode != 0 or not summ_path.exists():
        lines.append("ERROR: run failed or summary missing; see console.log")
        detail_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {detail_path} (run failed)")
        sys.exit(proc.returncode or 1)

    summary = json.loads(summ_path.read_text(encoding="utf-8"))
    lines.append("--- summary_report.json (aggregate) ---")
    lines.append(f"  top_hit_rate: {summary.get('top_hit_rate')}")
    lines.append(f"  avg_latency_ms: {summary.get('avg_latency_ms')}")
    rs = summary.get("retrieval_summary") or {}
    lines.append(f"  retrieval_metric_backend: {rs.get('retrieval_metric_backend')}")
    lines.append(f"  context_precision_avg: {rs.get('context_precision_avg')}")
    lines.append(f"  context_recall_avg: {rs.get('context_recall_avg')}")
    gs = summary.get("generation_summary") or {}
    lines.append(f"  faithfulness_avg: {gs.get('faithfulness_avg')}")
    lines.append(f"  factual_correctness_avg: {gs.get('factual_correctness_avg')}")
    lines.append(f"  custom_correctness_avg: {gs.get('custom_correctness_avg')}")
    lines.append(f"  ragas_e2e_score_avg: {(summary.get('end_to_end_summary') or {}).get('ragas_e2e_score_avg')}")
    ts = summary.get("temporal_summary") or {}
    lines.append(f"  temporal_iou_avg: {ts.get('temporal_iou_avg')}")
    ls = summary.get("localization_summary") or {}
    lines.append(f"  video_match_score_avg: {ls.get('video_match_score_avg')}")
    boot = summary.get("bootstrap") or {}
    if boot:
        lines.append("")
        lines.append("--- bootstrap (subset DB) ---")
        sq = boot.get("sqlite") or {}
        lines.append(f"  sqlite inserted_rows: {sq.get('inserted_rows')}")
        ch = boot.get("chroma") or {}
        lines.append(f"  chroma child_record_count: {ch.get('child_record_count')}")
        lines.append(f"  chroma video_record_count: {ch.get('video_record_count')}")

    e2e = json.loads(e2e_path.read_text(encoding="utf-8"))
    cases_out = e2e.get("cases", [])
    lines.append("")
    lines.append("--- per-case ---")
    for c in cases_out:
        cid = c.get("case_id")
        r = (c.get("ragas") or {}).get("retrieval", {})
        g = (c.get("ragas") or {}).get("generation", {})
        e2 = (c.get("ragas") or {}).get("end_to_end", {})
        ws = _wrong_share(c, str(c.get("video_id") or ""))
        lines.append("")
        lines.append(f"case_id: {cid}")
        lines.append(f"  question: {c.get('question', '')[:500]}")
        lines.append(f"  top_hit: {c.get('top_hit')}  top_video_ids: {c.get('top_video_ids')}")
        lines.append(f"  predicted_video_id: {c.get('predicted_video_id')}")
        lines.append(f"  non-GT context fraction (of retrieved_contexts): {ws}")
        lines.append(f"  retrieval_metric_backend: {r.get('retrieval_metric_backend')}")
        if r.get("id_based_retrieved_video_ids") is not None:
            lines.append(f"  id_based_retrieved_video_ids: {r.get('id_based_retrieved_video_ids')}")
            lines.append(f"  id_based_reference_video_ids: {r.get('id_based_reference_video_ids')}")
        lines.append(f"  context_precision: {r.get('context_precision')}  context_recall: {r.get('context_recall')}")
        lines.append(f"  faithfulness: {g.get('faithfulness')}  factual_correctness: {g.get('factual_correctness')}")
        lines.append(f"  custom_correctness: {g.get('custom_correctness')}  ragas_e2e: {e2.get('ragas_e2e_score')}")
        ref = (c.get("ragas_input_profile") or {}).get("reference_text") or ""
        lines.append(f"  reference (truncated for RAGAS, {len(ref)} chars): {ref[:400]}")
        prof = c.get("ragas_input_profile") or {}
        if prof.get("ragas_contexts_filter"):
            lines.append(f"  ragas_input_profile filter: {prof.get('ragas_contexts_filter')}")
            for k in sorted(prof.keys()):
                if k.startswith("ragas_context_filter_"):
                    lines.append(f"    {k}: {prof.get(k)}")
        lines.append("  retrieved_contexts (graph, before RAGAS compact):")
        for i, t in enumerate(c.get("retrieved_contexts") or [], 1):
            vid = _vid_from_ctx(t)
            lines.append(f"    [{i}] video={vid!r} match_gt={_norm_vid(vid)==exp_n}  text[:160]={t[:160]!r}")
        rfr = c.get("retrieved_contexts_for_ragas") or []
        lines.append(f"  retrieved_contexts_for_ragas (after compact, n={len(rfr)}):")
        for i, t in enumerate(rfr, 1):
            lines.append(f"    [{i}] {t[:200]!r}...")

    lines.append("")
    lines.append("=" * 72)
    lines.append("Tip: --retrieval-metrics-backend id_based for video-id precision/recall (no LLM).")
    lines.append("     --ragas-contexts-filter same_expected_video to restrict RAGAS contexts to GT video.")
    lines.append("=" * 72)

    detail_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: wrote {detail_path}")
    print(f"     eval JSON under {eval_out}")


if __name__ == "__main__":
    main()
