# 流式输出与上下文预算治理

## 目标
- 评估并规范当前系统的用户级 `streaming` 与统一 `token budget` 管理方式。
- 明确什么已经具备，什么暂未落地，后续应如何安全推进。
- 本文档是治理方案，不改变当前主链行为。

## 当前现状

### 1. 已有能力
- 图执行层支持状态流：
  - 调用方式：`graph.stream(..., stream_mode="values")`
  - 现状：测试和调试可以实时观察节点推进
- `summary_node` 已对最终总结使用较小输出上限：
  - 当前通过 `llm.bind(max_tokens=120)` 控制总结长度
- `InputValidator.sanitize_query()` 对输入长度有清洗逻辑
- `parallel_retrieval_fusion_node` 对检索规模已有运行时上限：
  - `AGENT_FUSION_TOP_K`
  - `AGENT_PARALLEL_BRANCH_TIMEOUT_SEC`
  - `search_config.sql_limit`
  - `search_config.hybrid_limit`

### 2. 缺失能力
- 用户级 token streaming 尚未正式接入
- 没有统一的全链路 token budget 分配器
- 没有“每个节点最多能消费多少上下文”的统一约束
- 没有“query fan-out / rewrite 扩写 / 多查询”对应的预算规则

## 当前关键预算点

### 输入侧
- `InputValidator.sanitize_query()`：
  - 负责 query 清洗与基础限制
  - 是第一道成本控制入口

### 检索侧
- `search_config.candidate_limit = 80`
- `search_config.hybrid_limit = 50`
- `search_config.sql_limit = 80`
- `AGENT_FUSION_TOP_K` 控制融合后保留上限

### 生成侧
- `summary_node`：
  - 当前 `max_tokens = 120`
  - 只使用前若干 top results 做总结

## 治理原则

### G1. 预算先于增强
- 新增 `multi-query`、`HyDE`、`decomposition` 之前，必须先定义预算。
- 不允许先扩 fan-out，再补成本约束。

### G2. 用户可见输出优先受控
- 最终 `summary` 的长度必须先受控。
- 任何额外解释、trace、citation 都应和最终回答分离管理。

### G3. 检索预算和生成预算分开治理
- 检索预算：
  - 控制候选数、分支 fan-out、回退策略
- 生成预算：
  - 控制 prompt 长度、上下文条数、最终输出 token 数

## 建议的统一预算模型

### 1. Query Budget
| 项目 | 建议上限 | 说明 |
|---|---:|---|
| 原始 query 长度 | `500 chars` | 超长输入先裁剪和清洗 |
| rewrite 输出长度 | 原 query 的 `<= 1.5x` | 防止 rewrite 失控扩写 |
| future multi-query fan-out | `<= 3` | 当前默认不启用 |

### 2. Retrieval Budget
| 项目 | 建议上限 | 说明 |
|---|---:|---|
| SQL rows | `80` | 当前已接近此口径 |
| Hybrid rows | `50` | 当前已接近此口径 |
| Fused rows | `50` | 当前由 `AGENT_FUSION_TOP_K` 控制 |
| 最终 summary 消费结果条数 | `<= 3~5` | 当前总结只需少量 top results |

### 3. Generation Budget
| 项目 | 建议上限 | 说明 |
|---|---:|---|
| summary 输出 token | `120` | 当前已实现 |
| 用户级最终回答字数 | `< 90 words` | 当前 prompt 已约束 |
| citation 数 | `<= 3` | 当前已按最小引用控制 |

## Streaming 治理建议

### 当前推荐策略
- 保持“节点级状态流”作为默认可观测方式
- 暂不把最终用户回答做 token-by-token streaming 主链化

### 原因
- 当前系统是多节点图执行，用户更关心的是：
  - 节点是否推进
  - 两路是否都执行
  - 是否降级
  - 最终引用是否存在
- 如果直接上用户级 token streaming，会引入：
  - 中途 answer 被 summary 覆盖的体验问题
  - citation 追加时序问题
  - 更复杂的中断与错误处理

### 后续如果要接用户级 streaming
- 建议只对 `summary_node` 的最终输出做 streaming
- 不建议对中间 draft answer 做 streaming
- citation 应在最终完成时整体附加，不要边流边变

## 建议的 trace 字段

### 预算相关 trace
- `query_length`
- `rewritten_query_length`
- `sql_rows_count`
- `hybrid_rows_count`
- `fused_rows_count`
- `summary_input_rows`
- `summary_output_length`

### 未来可追加
- `estimated_prompt_tokens`
- `estimated_output_tokens`
- `budget_exceeded_flags`

## 准入规则

### 什么时候允许做 `streaming`
- 当 citation、summary、error fallback 的时序已明确
- 当用户侧有明确体验需求
- 当 trace 中可区分：
  - `draft started`
  - `final summary completed`
  - `citations appended`

### 什么时候允许做更强 rewrite / multi-query
- 已有统一 token budget
- 已有 query fan-out trace
- 已有召回收益证据

## 当前结论
- `streaming` 不是当前主线阻塞项
- `token budget` 需要先文档化，再逐步内聚到统一配置
- 当前最稳妥策略是：
  - 保持节点级流式观测
  - 控制 summary 输出
  - 控制检索候选规模
  - 暂不启用高成本 rewrite 增强

## 一句话规则
- 先把预算说清楚，再谈更强能力；先保证最终回答稳定，再考虑更激进的 streaming 体验。
