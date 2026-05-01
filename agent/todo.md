# LlamaIndex 双链路改造 Todo

## 改造目标

- 保留外层 `LangGraph` 主图，不改动现有状态流、融合入口、回答节点与评测入口。
- 将两个子检索链替换为 `LlamaIndex` 实现：
  - `SQL` 子链：使用 `SQLDatabase + NLSQLTableQueryEngine` 或自定义 `SQLRetriever`
  - `Vector` 子链：使用 `VectorStoreIndex` 对接 `Chroma`
- 保留当前融合层 `Weighted RRF`
- 保留当前父子投影层 `project_rows_to_parent_context()`
- 保持下游输出协议稳定，避免影响 `answer_node`、`summary_node` 与 `ragas_eval_runner.py`

## 实施原则

- 只替换子检索执行层，不整体重写为 `LlamaIndex Agent`
- 先做适配层，再逐步切换主链路调用
- 所有 `LlamaIndex` 输出统一映射为当前项目既有结果结构
- 不改变当前 `RAGAS` 评测口径与入口

## 阶段一：边界梳理与适配设计

- 明确当前 `SQL` 子链输入输出协议
- 明确当前 `Vector` 子链输入输出协议
- 盘点下游依赖字段：
  - `event_id`
  - `video_id`
  - `track_id`
  - `start_time`
  - `end_time`
  - `event_summary_en`
  - `_distance`
  - `_hybrid_score`
- 设计两个适配器：
  - `LlamaIndexSQLAdapter`
  - `LlamaIndexVectorAdapter`
- 设计统一结果映射函数，确保输出继续兼容：
  - `normalize_sql_rows()`
  - `normalize_hybrid_rows()`

## 阶段二：SQL 子链改造

- 引入 `LlamaIndex SQLDatabase`
- 评估优先方案：
  - 优先尝试 `NLSQLTableQueryEngine`
  - 若结果不可控，改为自定义 `SQLRetriever`
- 将现有结构化过滤条件映射到 `LlamaIndex SQL` 查询输入
- 保留当前 `SQL` 行结果字段格式
- 保持与 `parallel_retrieval_fusion_node` 的调用接口一致
- 增加异常降级与空结果保护

## 阶段三：Vector 子链改造

- 使用 `VectorStoreIndex` 对接现有 `Chroma`
- 保留当前 `child collection` 为默认在线召回入口
- 保留 `parent collection` 供父级投影使用
- 将 `LlamaIndex` 检索结果映射为当前 `hybrid rows` 结构
- 兼容 metadata filter
- 明确分数字段映射策略：
  - `LlamaIndex score`
  - `_distance`
  - `_hybrid_score`
- 先不改 embedding 模型，避免触发整库重建

## 阶段四：主链路接入

- 在不改外层 `LangGraph` 的前提下替换子链内部调用
- `parallel_retrieval_fusion_node` 继续保留并行执行逻辑
- `Weighted RRF` 继续作为融合主逻辑
- `project_rows_to_parent_context()` 继续负责父级投影
- 保持 `merged_result` 与 `rerank_result` 字段语义不变

## 阶段五：验证与评测

- 验证 `answer_node` 输出是否无回归
- 验证 `summary_node` 输出是否无回归
- 验证 `ragas_eval_runner.py` 是否可直接复用
- 对比改造前后：
  - 检索召回数量
  - 融合后结果稳定性
  - 父级投影命中情况
  - `RAGAS` 指标变化
- 记录问题样例与回退条件

## 关键风险

- `LlamaIndex` 返回结构与当前结果协议不一致
- `SQL` 自然语言生成结果可能不稳定
- `Chroma` filter 行为与当前实现存在差异
- 分数语义变化可能影响 `Weighted RRF` 效果
- 若更换 embedding 模型，需要重建向量索引

## 交付物

- `LlamaIndex SQL` 子链适配器
- `LlamaIndex Vector` 子链适配器
- 统一结果映射函数
- 主链路无侵入接入改造
- 一轮 `RAGAS` 对比评测记录

## 验收标准

- 外层 `LangGraph` 主图保持不变
- 两个子链均由 `LlamaIndex` 驱动
- `Weighted RRF` 与父子投影逻辑保持可用
- `answer_node`、`summary_node`、`ragas_eval_runner.py` 无需大改或仅做轻微兼容
- 改造后可稳定跑通现有评测流程
