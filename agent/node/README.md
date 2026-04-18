# node 模块说明

## 目录职责
- 承载图节点实现（路由、执行、反思、回答）。

## 文件职责
- `tool_router_node.py`：解析查询并做路由决策。
- `query_classification_node.py`：并行融合模式下的查询分类（structured/semantic/mixed）。
- `parallel_retrieval_fusion_node.py`：并行执行 SQL 与 Hybrid，并执行加权融合。
- `pure_sql_node.py`：执行 pure_sql 子 agent。
- `hybrid_search_node.py`：执行 hybrid_search 子 agent。
- `reflection_node.py`：质量评估与重试决策。
- `answer_node.py`：最终回答组装。
- `types.py`：`AgentState` 与状态工具函数。
- `cot_engine.py`：CoT 执行引擎。
- `router_prompts.py`：路由提示词模板。
- 其余 `#*.py` / `#*.deprecated`：冻结历史文件，不参与主链路。

## 对外接口（主链路）
- `create_tool_router_node(llm)`
- `create_query_classification_node(...)`
- `create_parallel_retrieval_fusion_node(llm, ...)`
- `create_pure_sql_node(llm=None, **kwargs)`
- `create_hybrid_search_node(llm=None, **kwargs)`
- `create_reflection_node(llm=None, max_retries=..., retry_delay=...)`
- `route_by_tool_choice(state)`
- `route_after_reflection(state)`
- `final_answer_node(state, config, store)`

## 依赖关系
- 被 `graph_builder.py` 调用。
- `pure_sql_node/hybrid_search_node` 依赖 `agents/*/sub_agent.py`。
- 依赖 `types.py` 提供统一状态定义。

## 约定
- 节点函数签名保持 `node(state, config, store) -> dict`。
- 节点只做编排与状态写回，不内嵌工具实现细节。
