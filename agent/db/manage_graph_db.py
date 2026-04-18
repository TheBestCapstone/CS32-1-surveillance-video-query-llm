import argparse
import json
import logging
from pathlib import Path

from .config import (
    DEFAULT_ENV_FILE,
    get_graph_chroma_collection,
    get_graph_chroma_path,
    get_graph_lancedb_path,
    get_graph_sqlite_db_path,
    persist_env_value,
)
from .sqlite_builder import SQLiteBuildConfig, SQLiteDatabaseBuilder


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("manage_graph_db")


def cmd_build(args: argparse.Namespace) -> None:
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else get_graph_sqlite_db_path()
    seed_files = [Path(x).expanduser().resolve() for x in args.seed_json]
    init_prompt_md_path = (
        Path(args.init_prompt_md).expanduser().resolve() if args.init_prompt_md else None
    )
    init_prompt_json_path = (
        Path(args.init_prompt_json).expanduser().resolve() if args.init_prompt_json else None
    )
    builder = SQLiteDatabaseBuilder(
        SQLiteBuildConfig(
            db_path=db_path,
            reset_existing=bool(args.reset),
            generate_init_prompt=not bool(args.no_init_prompt),
            init_prompt_md_path=init_prompt_md_path or SQLiteBuildConfig.init_prompt_md_path,
            init_prompt_json_path=init_prompt_json_path or SQLiteBuildConfig.init_prompt_json_path,
        )
    )
    result = builder.build(seed_files=seed_files)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_switch(args: argparse.Namespace) -> None:
    env_path = Path(args.env_file).expanduser().resolve() if args.env_file else DEFAULT_ENV_FILE
    if args.sqlite_path:
        sqlite_path = str(Path(args.sqlite_path).expanduser().resolve())
        persist_env_value("AGENT_SQLITE_DB_PATH", sqlite_path, env_file=env_path)
        logger.info("Updated AGENT_SQLITE_DB_PATH=%s", sqlite_path)
    if args.lancedb_path:
        lancedb_path = str(Path(args.lancedb_path).expanduser().resolve())
        persist_env_value("AGENT_LANCEDB_PATH", lancedb_path, env_file=env_path)
        logger.info("Updated AGENT_LANCEDB_PATH=%s", lancedb_path)
    if args.chroma_path:
        chroma_path = str(Path(args.chroma_path).expanduser().resolve())
        persist_env_value("AGENT_CHROMA_PATH", chroma_path, env_file=env_path)
        logger.info("Updated AGENT_CHROMA_PATH=%s", chroma_path)
    if args.chroma_collection:
        persist_env_value("AGENT_CHROMA_COLLECTION", args.chroma_collection, env_file=env_path)
        logger.info("Updated AGENT_CHROMA_COLLECTION=%s", args.chroma_collection)

    print(
        json.dumps(
            {
                "env_file": str(env_path),
                "effective_sqlite_path": str(get_graph_sqlite_db_path()),
                "effective_lancedb_path": str(get_graph_lancedb_path()),
                "effective_chroma_path": str(get_graph_chroma_path()),
                "effective_chroma_collection": get_graph_chroma_collection(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/switch databases used by agent graph")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Create sqlite schema, indexes, and seed rows")
    p_build.add_argument("--db-path", type=str, default="", help="Target sqlite db path")
    p_build.add_argument("--seed-json", nargs="*", default=[], help="Seed json file(s)")
    p_build.add_argument("--reset", action="store_true", help="Delete existing db before build")
    p_build.add_argument("--no-init-prompt", action="store_true", help="Disable init prompt generation")
    p_build.add_argument("--init-prompt-md", type=str, default="", help="Output markdown path for init prompt")
    p_build.add_argument("--init-prompt-json", type=str, default="", help="Output json path for init prompt profile")
    p_build.set_defaults(func=cmd_build)

    p_switch = sub.add_parser("switch", help="One-click switch db path for graph via .env")
    p_switch.add_argument("--sqlite-path", type=str, default="", help="New sqlite db path")
    p_switch.add_argument("--lancedb-path", type=str, default="", help="New LanceDB path")
    p_switch.add_argument("--chroma-path", type=str, default="", help="New Chroma persistent path")
    p_switch.add_argument("--chroma-collection", type=str, default="", help="New Chroma collection name")
    p_switch.add_argument("--env-file", type=str, default="", help="Custom .env file path")
    p_switch.set_defaults(func=cmd_switch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
