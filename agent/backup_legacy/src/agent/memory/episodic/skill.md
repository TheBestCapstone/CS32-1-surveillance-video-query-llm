# Episodic Memory 检索工具 (Skill 指南)

本文档旨在指导 Agent 框架如何将本目录下的 SQLite 向量数据库封装为一个供系统调用的 Tool（工具），并说明在何种场景下应该调用该工具。

## 1. 什么时候应该调用此数据库？

当用户的输入（Query）涉及以下意图时，Agent **必须**调用本工具查询情景记忆数据库：

- **视频内容事实查询**：例如“视频里有没有出现过红色的车？”、“那个人是在哪里跑的？”。
- **特定时间/地点的行为检索**：例如“找一下所有在停车场入口静止停放的车辆”、“寻找有人在十字路口搬运物品的片段”。
- **对象追踪与上下文关联**：例如“之前那辆白色的车后来去了哪里？”。

## 2. 工具封装规范

在 Agent 的工具层（如 LangChain 的 Tool 或自定义函数节点），需要封装 `EventRetriever` 类。

### 推荐的 Tool 接口设计

```python
from src.retrieval.event_retriever import EventRetriever

# 初始化全局 Retriever 实例
episodic_retriever = EventRetriever()

def search_episodic_memory(query: str, object_type: str = None, video_id: str = None, top_k: int = 5) -> str:
    """
    搜索视频中的情景事件记忆。
    
    Args:
        query: 用户的自然语言查询，如 "寻找停放的汽车"
        object_type: (可选) 对象类别过滤，如 "car", "person", "bike", "truck"
        video_id: (可选) 限制在特定视频内搜索，如 "VIRAT_S_000001_00_000000_000500.mp4"
        top_k: 返回的结果数量
        
    Returns:
        JSON 格式的字符串，包含相关事件的列表。
    """
    results = episodic_retriever.hybrid_event_search(
        query_text=query, 
        top_k=top_k, 
        video_id=video_id, 
        object_type=object_type
    )
    
    if not results:
        return "未找到相关的视频事件记录。"
        
    # 格式化输出，方便大模型阅读
    formatted_results = []
    for res in results:
        formatted_results.append({
            "event_id": res["event_id"],
            "video_id": res["video_id"],
            "time_range": f"{res['start_time']}s - {res['end_time']}s",
            "summary": res["event_summary_cn"],
            "relevance_distance": round(res["distance"], 4)
        })
        
    import json
    return json.dumps(formatted_results, ensure_ascii=False, indent=2)
```

## 3. Agent 工作流集成建议

1. **意图识别 (Router)**：当用户提问到来时，大模型首先判断是否需要依赖过去的视频内容。如果是，则将请求路由到 `search_episodic_memory` 工具。
2. **参数提取**：大模型需要从用户的自然语言中提取出结构化参数。例如“找一下视频1里的红色卡车”，提取出 `query="红色的卡车"`, `video_id="视频1"`。
3. **调用并阅读**：Agent 执行上述函数，获取 JSON 返回结果。
4. **生成回答 (Answer)**：Agent 阅读返回的事件列表，总结出人类友好的回答，如“在视频1的 12秒至45秒处，有一辆红色的卡车出现并停在路边”。