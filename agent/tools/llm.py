import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Union

EMBEDDING_BATCH_LIMIT = 10

def get_qwen_embedding(text: Union[str, List[str]]) -> Union[list[float], List[list[float]]]:
    """
    调用百炼 API 获取文本的 embedding 向量，支持单条或批量传入。
    如果是字符串，返回单条 vector；如果是列表，返回 vector 列表。
    需要提前配置环境变量: DASHSCOPE_API_KEY
    """
    try:
        load_dotenv()
    except Exception:
        pass
        
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", 
    )

    if isinstance(text, str):
        completion = client.embeddings.create(
            model="text-embedding-v3", # 百炼的文本 embedding 模型
            input=text,
            dimensions=1024, # 百炼 v3 模型最大支持 1024
            encoding_format="float"
        )
        return completion.data[0].embedding

    # 批量返回时按接口限制分批请求，再按原始顺序拼接
    all_embeddings: List[list[float]] = []
    for start in range(0, len(text), EMBEDDING_BATCH_LIMIT):
        batch = text[start : start + EMBEDDING_BATCH_LIMIT]
        completion = client.embeddings.create(
            model="text-embedding-v3", # 百炼的文本 embedding 模型
            input=batch,
            dimensions=1024, # 百炼 v3 模型最大支持 1024
            encoding_format="float"
        )
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
