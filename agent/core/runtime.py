import os
from pathlib import Path

from langchain_openai import ChatOpenAI


def load_env(project_root: Path | None = None) -> None:
    root = project_root or Path(__file__).resolve().parents[2]
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    if not os.getenv("OPENAI_API_KEY") and os.getenv("DASHSCOPE_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")
    if not os.getenv("OPENAI_BASE_URL") and os.getenv("DASHSCOPE_URL"):
        os.environ["OPENAI_BASE_URL"] = os.getenv("DASHSCOPE_URL")


def build_default_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model_name="qwen3-max",
        temperature=0.0,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_URL"),
    )


def load_init_prompt(project_root: Path | None = None) -> str:
    root = project_root or Path(__file__).resolve().parents[2]
    prompt_path = root / "agent" / "init" / "agent_init_prompt.md"
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8").strip()
