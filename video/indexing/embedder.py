import os
from openai import OpenAI
from dotenv import load_dotenv

from typing import List, Union

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

    completion = client.embeddings.create(
        model="text-embedding-v3",
        input=text,
        dimensions=1024,
        encoding_format="float"
    )
    
    if isinstance(text, str):
        return completion.data[0].embedding
    else:
        sorted_data = sorted(completion.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

if __name__ == "__main__":
    test_text = "A silver-gray sedan parked stationary in a parking slot for a long time."
    print(f"Test embedding for: {test_text}")
    try:
        vec = get_qwen_embedding(test_text)
        print(f"OK: dim={len(vec)}")
        print(f"First 5 values: {vec[:5]}")
    except Exception as e:
        print(f"Failed: {e}")
