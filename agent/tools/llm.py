import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Union

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

    completion = client.embeddings.create(
        model="text-embedding-v3", # 百炼的文本 embedding 模型
        input=text,
        dimensions=1024, # 百炼 v3 模型最大支持 1024
        encoding_format="float"
    )
    
    if isinstance(text, str):
        return completion.data[0].embedding
    else:
        # 批量返回，注意按照输入顺序整理
        sorted_data = sorted(completion.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

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
