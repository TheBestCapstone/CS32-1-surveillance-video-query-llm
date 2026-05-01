import os
from openai import OpenAI
from dotenv import load_dotenv

from typing import List, Union

EMBEDDING_BATCH_LIMIT = 10

def get_qwen_embedding(text: Union[str, List[str]]) -> Union[list[float], List[list[float]]]:
    """
    Call Dashscope-compatible embeddings API (single string or batch list).
    Requires DASHSCOPE_API_KEY in the environment.
    """
    try:
        load_dotenv()
    except Exception:
        pass
        
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("Set environment variable DASHSCOPE_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", 
    )

    if isinstance(text, str):
        completion = client.embeddings.create(
            model="text-embedding-v3",
            input=text,
            dimensions=1024,
            encoding_format="float"
        )
        return completion.data[0].embedding
    all_embeddings: List[list[float]] = []
    for start in range(0, len(text), EMBEDDING_BATCH_LIMIT):
        batch = text[start : start + EMBEDDING_BATCH_LIMIT]
        completion = client.embeddings.create(
            model="text-embedding-v3",
            input=batch,
            dimensions=1024,
            encoding_format="float"
        )
        sorted_data = sorted(completion.data, key=lambda x: x.index)
        all_embeddings.extend(item.embedding for item in sorted_data)
    return all_embeddings

if __name__ == "__main__":
    test_text = "A silver-gray sedan parked stationary in a parking slot for a long time."
    print(f"Test embedding for: {test_text}")
    try:
        vec = get_qwen_embedding(test_text)
        print(f"OK: dim={len(vec)}")
        print(f"First 5 values: {vec[:5]}")
    except Exception as e:
        print(f"Failed: {e}")
