# 调优后 RAGAS 对比报告

## 评测范围

- 数据范围：`Part1 + Part4`
- 本次验证批次：`10` 个 `e2e_ready` case
- 对比对象：
  - 基线链路：`AGENT_USE_LLAMAINDEX_SQL=0`，`AGENT_USE_LLAMAINDEX_VECTOR=0`
  - 调优后 LlamaIndex 链路：`AGENT_USE_LLAMAINDEX_SQL=1`，`AGENT_USE_LLAMAINDEX_VECTOR=1`
- 评测配置：
  - `ragas_concurrency=1`
  - `answer_relevancy_strictness=1`
  - `ragas_metric_max_retries=4`
  - `ragas_metric_retry_delay_sec=2.0`

## 结果总览

| 指标 | 基线链路 | 调优后 LlamaIndex | 结论 |
|---|---:|---:|---|
| `case_count` | `10` | `10` | 持平 |
| `success_count` | `10` | `10` | 持平 |
| `top_hit_rate` | `0.8` | `0.9` | LlamaIndex 更好 |
| `avg_latency_ms` | `10642.07` | `14748.17` | LlamaIndex 更慢 |
| `context_precision_avg` | `0.4375` | `0.5` | LlamaIndex 更高 |
| `context_recall_avg` | `0.3125` | `0.2222` | 基线更高 |
| `faithfulness_avg` | `0.2619` | `0.2431` | 基线略高 |
| `answer_relevancy_avg` | `0.2973` | `0.3784` | LlamaIndex 更好 |
| `factual_correctness_avg` | `0.014` | `0.026` | LlamaIndex 更好 |
| `ragas_e2e_score_avg` | `0.2242` | `0.2546` | LlamaIndex 更好 |
| `ragas_metric_error_cases` | `0` | `0` | 已修复 |

## 调优动作

- `SQL` 子链：
  - 当 `LlamaIndex SQL` 返回 `0` 行时，自动回退到旧的启发式 SQL 检索
- `Vector` 子链：
  - 先走 `LlamaIndex VectorStoreIndex`
  - 若带 filter 无结果，则自动放宽为无 filter 检索
  - 对候选结果增加本地 `BM25 + vector score` 轻量重排
  - 若仍为空，则回退到旧的 `ChromaGateway.search()`
- `RAGAS`：
  - 指标计算从并发改为串行
  - 对 `429/rate limit/timeout` 增加重试和退避
  - 默认 `ragas_concurrency` 降为 `1`
  - 默认 `answer_relevancy_strictness` 降为 `1`

## 关键结论

- `ragas_metric_error_cases` 已从之前的高比例错误降到 `0`
- 调优后 `LlamaIndex` 链路在这轮 `10-case` 验证中：
  - `top_hit_rate` 超过基线
  - `ragas_e2e_score_avg` 超过基线
  - 但仍有明显时延成本

## 仍需继续优化的点

- 时延：`LlamaIndex` 链路平均图时延仍高于基线
- `context_recall_avg` 仍低于基线，说明上下文覆盖面还不够稳
- 当前 SQL fallback 和 vector fallback 让链路更稳，但也意味着效果提升并不完全来自纯 `LlamaIndex` 原生能力

## 下一步建议

- 针对 `top_hit` 未命中的剩余 case 做定向分析
- 引入真正的 `rerank`
- 进一步收敛 `Vector` 子链的 filter 与打分行为
- 在更大样本上复核当前结论，例如 `50-case` 或全量 `310-case`
