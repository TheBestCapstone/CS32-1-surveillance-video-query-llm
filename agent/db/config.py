import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "data" / "SQLite" / "episodic_events.sqlite"
DEFAULT_LANCEDB_PATH = PROJECT_ROOT / "data" / "lancedb"
DEFAULT_CHROMA_PATH = PROJECT_ROOT / "data" / "chroma" / "basketball_tracks"
DEFAULT_CHROMA_COLLECTION = "basketball_tracks"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def get_graph_sqlite_db_path() -> Path:
    raw = os.getenv("AGENT_SQLITE_DB_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_SQLITE_PATH


def get_graph_lancedb_path() -> Path:
    raw = os.getenv("AGENT_LANCEDB_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_LANCEDB_PATH


def get_graph_chroma_path() -> Path:
    raw = os.getenv("AGENT_CHROMA_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_CHROMA_PATH


def get_graph_chroma_collection() -> str:
    raw = os.getenv("AGENT_CHROMA_COLLECTION", "").strip()
    if raw:
        return raw
    return DEFAULT_CHROMA_COLLECTION


def persist_env_value(key: str, value: str, env_file: Path | None = None) -> Path:
    target = env_file or DEFAULT_ENV_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("", encoding="utf-8")

    lines = target.read_text(encoding="utf-8").splitlines()
    replaced = False
    new_lines: list[str] = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        new_lines.append(f"{key}={value}")

    target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return target
