"""Shared utilities for multi-camera test scripts.

All test outputs go to ``lib.OUTPUT_DIR`` (default: ``../output``).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── path setup ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
OUTPUT_DIR = (_HERE / ".." / "output").resolve()
ROOT_DIR = (_HERE / ".." / ".." / ".." / "..").resolve()


def setup_env() -> dict[str, str]:
    """Set environment variables to point to the test_mulcamera databases.

    Returns a dict of the applied values for logging.
    """
    env_vars = {
        "AGENT_SQLITE_DB_PATH": str(
            ROOT_DIR / "agent" / "test_mulcamera" / "episodic_events.sqlite"
        ),
        "AGENT_CHROMA_PATH": str(ROOT_DIR / "agent" / "test_mulcamera" / "chroma"),
        "AGENT_CHROMA_CHILD_COLLECTION": "mul_camera_tracks",
        "AGENT_CHROMA_PARENT_COLLECTION": "mul_camera_tracks_parent",
        "AGENT_CHROMA_EVENT_COLLECTION": "mul_camera_events",
        "AGENT_CHROMA_GLOBAL_ENTITY_COLLECTION": "mul_camera_global_entities",
    }
    for key, value in env_vars.items():
        os.environ[key] = value
    return env_vars


# ── timing ────────────────────────────────────────────────────────────────────


@dataclass
class Timer:
    label: str = ""
    _start: float = 0.0
    elapsed_ms: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000


# ── result types ──────────────────────────────────────────────────────────────


@dataclass
class TestCase:
    name: str
    passed: bool = False
    details: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuite:
    name: str
    cases: list[TestCase] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def failed(self) -> int:
        return len(self.cases) - self.passed


@dataclass
class TestReport:
    title: str
    suites: list[TestSuite] = field(default_factory=list)
    started_at: str = ""
    elapsed_sec: float = 0.0
    env_vars: dict[str, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(len(s.cases) for s in self.suites)

    @property
    def passed(self) -> int:
        return sum(s.passed for s in self.suites)

    @property
    def failed(self) -> int:
        return self.total - self.passed


# ── output helpers ────────────────────────────────────────────────────────────


def write_json_report(report: TestReport, name: str = "report") -> Path:
    """Write a JSON report to ``OUTPUT_DIR/{name}.json``."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.json"
    data = {
        "title": report.title,
        "started_at": report.started_at,
        "elapsed_sec": round(report.elapsed_sec, 2),
        "total_cases": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "env_vars": report.env_vars,
        "suites": [
            {
                "name": s.name,
                "passed": s.passed,
                "failed": s.failed,
                "cases": [
                    {
                        "name": c.name,
                        "passed": c.passed,
                        "details": c.details,
                        "metrics": c.metrics,
                    }
                    for c in s.cases
                ],
            }
            for s in report.suites
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_md_summary(report: TestReport, name: str = "summary") -> Path:
    """Write a human-readable Markdown summary to ``OUTPUT_DIR/{name}.md``."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.md"
    lines: list[str] = []
    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(f"**Started**: {report.started_at}  ")
    lines.append(f"**Elapsed**: {report.elapsed_sec:.2f}s  ")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append(f"| Suite | Total | Passed | Failed |")
    lines.append(f"|-------|------:|-------:|-------:|")
    for s in report.suites:
        lines.append(f"| {s.name} | {len(s.cases)} | {s.passed} | {s.failed} |")
    lines.append(f"| **Total** | **{report.total}** | **{report.passed}** | **{report.failed}** |")
    lines.append("")

    for s in report.suites:
        lines.append(f"## {s.name}")
        lines.append("")
        for c in s.cases:
            icon = "✅" if c.passed else "❌"
            lines.append(f"- {icon} **{c.name}**")
            if c.details:
                lines.append(f"  {c.details}")
            if c.metrics:
                for k, v in c.metrics.items():
                    if isinstance(v, float):
                        lines.append(f"  - `{k}`: {v:.3f}")
                    else:
                        lines.append(f"  - `{k}`: {v}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_questions() -> dict[str, list[dict[str, Any]]]:
    """Load the sampled 60 questions from JSON."""
    path = ROOT_DIR / "agent" / "test_mulcamera" / "sampled_60_questions.json"
    with open(path) as f:
        return json.load(f)
