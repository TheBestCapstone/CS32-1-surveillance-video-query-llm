import os
from src.indexing.embedder import get_qwen_embedding


def test_api():
    print("=== Test 1: environment variable ===")
    try:
        from dotenv import load_dotenv

        load_dotenv()
        print("OK: attempted to load .env")
    except ImportError:
        print("Warning: python-dotenv not installed; using process environment only")

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if api_key:
        masked_key = api_key[:5] + "..." + api_key[-4:] if len(api_key) > 9 else "***"
        print(f"OK: DASHSCOPE_API_KEY present: {masked_key}")
    else:
        print("Error: DASHSCOPE_API_KEY not set; check .env or export.")
        return

    print("\n=== Test 2: Dashscope embedding API ===")
    test_text = "Simple English test sentence for embedding smoke test."
    print(f"text: '{test_text}'")

    try:
        vec = get_qwen_embedding(test_text)
        print("OK: embedding returned")
        print(f"dim: {len(vec)}")
        print(f"first 5 values: {vec[:5]}")
    except Exception as e:
        print(f"API error: {e}")


if __name__ == "__main__":
    import sys

    sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
    test_api()
