import os
from src.indexing.embedder import get_qwen_embedding

def test_api():
    print("=== 测试 1：检查环境变量 ===")
    # 尝试从 .env 加载环境变量
    # 这假设您的当前工作目录是 Capstone
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已尝试加载 .env 文件")
    except ImportError:
        print("⚠️ 未安装 python-dotenv，尝试直接读取系统环境变量")

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if api_key:
        # 打印前 5 个字符，保护隐私
        masked_key = api_key[:5] + "..." + api_key[-4:] if len(api_key) > 9 else "***"
        print(f"✅ 成功获取 DASHSCOPE_API_KEY: {masked_key}")
    else:
        print("❌ 无法获取 DASHSCOPE_API_KEY，请检查 .env 文件或环境变量设置。")
        return

    print("\n=== 测试 2：调用百炼 Embedding API ===")
    test_text = "这是一个简单的测试文本，用于验证向量生成。"
    print(f"📝 测试文本: '{test_text}'")
    
    try:
        vec = get_qwen_embedding(test_text)
        print(f"✅ Embedding 生成成功！")
        print(f"📊 向量维度: {len(vec)}")
        print(f"🔢 向量前 5 维数据: {vec[:5]}")
    except Exception as e:
        print(f"❌ API 调用失败: {e}")

if __name__ == "__main__":
    # 为了能导入 src 模块，确保 python path 正确
    import sys
    sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
    test_api()
