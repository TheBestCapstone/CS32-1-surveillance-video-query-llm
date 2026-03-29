from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from .types import AgentState, ToolChoice


TOOL_ROUTER_SYSTEM_PROMPT = """你是一个智能工具路由助手。你的任务是根据用户查询判断需要使用的工具类型。

## 可用工具清单

### 1. hybrid_search (混合检索工具)
- **功能**: 结合向量检索和SQL元数据过滤的混合搜索
- **输入**: event_list(事件关键词列表), meta_list(元数据过滤条件)
- **输出**: 检索结果列表，包含event_id, video_id, _distance, event_summary等字段
- **适用场景**: 用户查询包含"进入"、"离开"、"移动"、"停止"、"出现"等事件描述，同时可能有颜色、时间等条件
- **关键词**: "车"、"人"、"目标"、"物体"、"进入"、"离开"、"移动"、"停止"、"出现"

### 2. pure_sql (纯SQL检索工具)
- **功能**: 基于元数据条件的纯SQL结构化查询
- **输入**: meta_list(元数据过滤条件，如颜色、时间范围、运动状态等)
- **输出**: 符合条件的结果列表
- **适用场景**: 用户查询主要是结构化的条件筛选，如"红色车辆"、"上午9点到10点"、"静止的目标"
- **关键词**: "红色"、"蓝色"、"白色"、"黑色"、"上午"、"下午"、"今天"、"静止"

### 3. video_vect (视频向量检索工具)
- **功能**: 基于语义理解的视频内容向量检索
- **输入**: event_list(事件关键词)
- **输出**: 语义相关的视频片段列表
- **适用场景**: 用户查询需要理解视频内容的语义，如"车辆驶入"、"行人横穿"、"物体遗落"
- **关键词**: "视频"、"画面"、"镜头"、"语义"、"理解"

### 4. parallel_search (并行检索)
- **功能**: 同时执行多个检索工具并合并结果
- **输入**: 多个子查询任务
- **输出**: 合并后的去重排序结果
- **适用场景**: 复杂查询需要多种检索方式协同，如既需要向量检索又需要SQL过滤

## 智能推荐逻辑

1. **首先识别用户意图**:
   - 如果查询包含具体事件描述(进入、离开等) → hybrid_search
   - 如果查询主要是条件筛选(颜色、时间) → pure_sql
   - 如果查询需要语义理解 → video_vect
   - 如果查询复杂涉及多个方面 → parallel_search

2. **组合判断**:
   - 事件描述 + 条件筛选 → parallel_search(hybrid + pure_sql)
   - 事件描述 + 语义需求 → parallel_search(hybrid + video_vect)

3. **错误处理**:
   - 无法判断时默认使用hybrid_search
   - 工具执行失败时记录错误并尝试备选工具

## 输出格式

请直接输出JSON格式的决策结果：
{
  "mode": "hybrid|pure_sql|video_vect|parallel|none",
  "reason": "选择该工具的简要理由",
  "confidence": 0.0-1.0
}

不要输出多余解释，直接输出JSON。"""


def create_tool_router_node(llm: Any = None):
    def tool_router_node(state: AgentState, config: RunnableConfig, store: BaseStore) -> dict[str, Any]:
        del store
        user_query = state.get("user_query", "")

        try:
            actual_llm = llm
            if actual_llm is None:
                import os
                from langchain_openai import ChatOpenAI
                actual_llm = ChatOpenAI(
                    model_name="qwen3-max",
                    temperature=0.0,
                    api_key=os.getenv("DASHSCOPE_API_KEY"),
                    base_url=os.getenv("DASHSCOPE_URL"),
                )

            messages = [
                HumanMessage(content=TOOL_ROUTER_SYSTEM_PROMPT),
                HumanMessage(content=f"用户查询: {user_query}\n\n请输出JSON格式的工具选择决策。"),
            ]
            response = actual_llm.invoke(messages)
            raw_content = response.content if hasattr(response, "content") else str(response)

            import json
            try:
                decision = json.loads(raw_content)
                mode = decision.get("mode", "hybrid")
            except json.JSONDecodeError:
                raw_content_clean = raw_content.strip()
                if raw_content_clean.startswith("```"):
                    lines = raw_content_clean.split("\n")
                    raw_content_clean = "\n".join(lines[1:-1])
                try:
                    decision = json.loads(raw_content_clean)
                    mode = decision.get("mode", "hybrid")
                except json.JSONDecodeError:
                    mode = "hybrid"

        except Exception as exc:
            mode = "hybrid"

        if not mode or mode == "none":
            if any(kw in user_query.lower() for kw in ["车", "人", "进入", "离开", "移动"]):
                mode = "hybrid"
            elif any(kw in user_query.lower() for kw in ["红色", "蓝色", "白色", "黑色", "上午", "今天"]):
                mode = "pure_sql"
            elif any(kw in user_query.lower() for kw in ["视频", "画面"]):
                mode = "video_vect"
            else:
                mode = "hybrid"

        sql_needed = mode == "pure_sql"
        hybrid_needed = mode == "hybrid"
        video_vect_needed = mode == "video_vect"
        parallel_needed = mode == "parallel"

        sub_queries: dict[str, Any] = {}
        if hybrid_needed:
            sub_queries["hybrid"] = {}
        if sql_needed:
            sub_queries["sql"] = {}
        if video_vect_needed:
            sub_queries["video_vect"] = {}

        tool_choice: ToolChoice = {
            "mode": mode,
            "sql_needed": sql_needed,
            "hybrid_needed": hybrid_needed,
            "video_vect_needed": video_vect_needed,
            "sub_queries": sub_queries,
        }

        thought = f"工具路由决策: mode={mode}"
        return {
            "tool_choice": tool_choice,
            "is_parallel": parallel_needed,
            "parallel_queries": list(sub_queries.keys()) if parallel_needed else [],
            "thought": thought,
            "messages": [AIMessage(content=f"工具路由完成: {mode}")],
        }

    return tool_router_node


def route_by_tool_choice(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")

    if mode == "hybrid":
        return "hybrid_preprocess"
    elif mode == "parallel":
        return "parallel_flow"
    elif mode == "sql":
        return "pure_sql_preprocess"
    elif mode == "video_vect":
        return "video_vect_preprocess"
    else:
        return "reflection_node"


def route_from_preprocess(state: AgentState) -> str:
    tool_choice = state.get("tool_choice", {})
    mode = tool_choice.get("mode", "none")

    if mode == "parallel":
        return "parallel_flow"
    elif mode == "hybrid":
        return "hybrid_search_node"
    elif mode == "sql":
        return "pure_sql_node"
    elif mode == "video_vect":
        return "video_vect_node"
    else:
        return "reflection_node"


if __name__ == "__main__":
    router = create_tool_router_node()
    out = router({"user_query": "车进入镜头", "parsed_question": {}}, {}, None)
    print("mode:", out["tool_choice"]["mode"])