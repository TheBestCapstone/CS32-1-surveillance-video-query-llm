# CHANGELOG

## 2026-03-31

### Removed
- preprocess 层从主调用链移除：`tool_router -> *_preprocess -> *_node` 改为 `tool_router -> *_node`
- graph 中所有 preprocess 节点注册与边已清理
- preprocess 文件改为 `#文件名` 形式弃用保留

### Added
- `AgentState` 新增：
  - `search_config`
  - `sql_plan`
  - `metrics`
- hybrid 节点新增：
  - state 注入参数：`candidate_limit`、`top_k_per_event`、`rerank_top_k`、`distance_threshold`
  - 二次过滤与 explain 信息
  - 指标输出：`hybrid_latency_ms`、`hybrid_recall_count`、`hybrid_filtered_count`、`hybrid_rerank_count`
- pure sql 节点新增：
  - 三步执行（拼装 SQL -> 执行 -> 映射）
  - 参数化查询
  - 插件回调：`strategy`、`row_mapper`、`post_filter`、`validate_config`、`reload_hook`、`connection_factory`
  - 指标输出：`sql_latency_ms`、`sql_result_count`
- 新增测试：
  - `agent/test/test_hybrid.py`
  - `agent/test/test_sql.py`
  - 性能基线输出：`agent/test/perf_baseline.json`

### Migration Guide
- 路由结果节点名变更：
  - `hybrid_preprocess` -> `hybrid_search_node`
  - `pure_sql_preprocess` -> `pure_sql_node`
- 功能开关收敛：
  - `parallel` 已完全关闭
  - `video_vect` 已完全关闭
- 需要在 router 输出或调用前补充：
  - `state.search_config`
  - `state.sql_plan`
- pure sql 若要定制检索策略，使用 `create_pure_sql_node(strategy=..., row_mapper=..., post_filter=...)`
