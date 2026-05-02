import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Union

EMBEDDING_BATCH_LIMIT = 10


def _embedding_provider() -> str:
    return os.environ.get("AGENT_EMBEDDING_PROVIDER", "openai").strip().lower()


def _embedding_model() -> str:
    provider = _embedding_provider()
    default_model = "text-embedding-3-large" if provider == "openai" else "text-embedding-v3"
    return os.environ.get("AGENT_EMBEDDING_MODEL", default_model).strip()


def _embedding_dimensions() -> int | None:
    raw = os.environ.get("AGENT_EMBEDDING_DIMENSIONS", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except Exception:
        return None
    return value if value > 0 else None


def _build_embedding_client() -> OpenAI:
    provider = _embedding_provider()
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")
    return OpenAI(
        api_key=api_key,
        base_url=os.environ.get("DASHSCOPE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip(),
    )


def get_embedding_runtime_profile() -> dict:
    return {
        "provider": _embedding_provider(),
        "model": _embedding_model(),
        "dimensions": _embedding_dimensions(),
    }

def get_qwen_embedding(text: Union[str, List[str]]) -> Union[list[float], List[list[float]]]:
    """
    调用当前配置的 embedding API 获取文本向量，支持单条或批量传入。
    如果是字符串，返回单条 vector；如果是列表，返回 vector 列表。
    通过环境变量控制 provider/model/dimensions。
    """
    try:
        load_dotenv()
    except Exception:
        pass

    client = _build_embedding_client()
    model = _embedding_model()
    dimensions = _embedding_dimensions()

    if isinstance(text, str):
        request = {
            "model": model,
            "input": text,
            "encoding_format": "float",
        }
        if dimensions is not None:
            request["dimensions"] = dimensions
        completion = client.embeddings.create(**request)
        return completion.data[0].embedding

    # 批量返回时按接口限制分批请求，再按原始顺序拼接
    all_embeddings: List[list[float]] = []
    for start in range(0, len(text), EMBEDDING_BATCH_LIMIT):
        batch = text[start : start + EMBEDDING_BATCH_LIMIT]
        request = {
            "model": model,
            "input": batch,
            "encoding_format": "float",
        }
        if dimensions is not None:
            request["dimensions"] = dimensions
        completion = client.embeddings.create(**request)
        sorted_data = sorted(completion.data, key=lambda x: x.index)
        all_embeddings.extend(item.embedding for item in sorted_data)
    return all_embeddings

if __name__ == "__main__":
    # 简单的测试
    test_text = "银灰色轿车在停车位区域长期静止停放"
    print(f"正在测试生成向量: {test_text}")
    try:
        vec = get_qwen_embedding(test_text)
        print(f"✅ 生成成功，向量维度: {len(vec)}")
        print(f"向量前5维: {vec[:5]}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
