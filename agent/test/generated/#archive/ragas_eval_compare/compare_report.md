# RAGAS 对比报告

## 评测范围

- 数据范围：`Part1 + Part4`
- 本次对比批次：`20` 个 `e2e_ready` case
- 全量可评测样本：`310` 个
- 图执行模式：`parallel_fusion`
- 对比对象：
  - 基线链路：`AGENT_USE_LLAMAINDEX_SQL=0`，`AGENT_USE_LLAMAINDEX_VECTOR=0`
  - LlamaIndex 链路：`AGENT_USE_LLAMAINDEX_SQL=1`，`AGENT_USE_LLAMAINDEX_VECTOR=1`

## 结果总览

| 指标 | 基线链路 | LlamaIndex 链路 | 结论 |
|---|---:|---:|---|
| `case_count` | `20` | `20` | 持平 |
| `success_count` | `20` | `20` | 持平 |
| `top_hit_rate` | `0.90` | `0.75` | 基线更好 |
| `avg_latency_ms` | `11026.16` | `16297.94` | LlamaIndex 更慢 |
| `context_precision_avg` | `0.4167` | `0.5833` | LlamaIndex 更高 |
| `context_recall_avg` | `0.5` | `0.5` | 持平 |
| `faithfulness_avg` | `0.2274` | `0.2005` | 基线略好 |
| `answer_relevancy_avg` | `0.3472` | `0.2838` | 基线更好 |
| `factual_correctness_avg` | `0.0167` | `0.0` | 基线更好 |
| `ragas_e2e_score_avg` | `0.2867` | `0.2214` | 基线更好 |
| `ragas_metric_error_cases` | `13` | `13` | 均受限流影响 |

## 关键观察

- 当前版本下，`LlamaIndex` 链路没有超过基线链路。
- 最直接的业务指标 `top_hit_rate` 从 `0.90` 降到 `0.75`，说明首命中与检索排序存在退化。
- 端到端 `RAGAS e2e` 从 `0.2867` 降到 `0.2214`，整体质量未提升。
- 图执行平均时延从 `11.0s` 上升到 `16.3s`，当前接入也带来了明显性能开销。
- 唯一正向信号是 `context_precision_avg` 从 `0.4167` 提升到 `0.5833`，说明 `LlamaIndex` 在部分样本上返回的上下文更“集中”，但没有转化成更好的命中率和最终回答质量。

## 明显掉点样本

- `PART1_0003`
  - 基线：`top_hit=True`，`ragas_e2e_score=0.404`
  - LlamaIndex：`top_hit=False`，`ragas_e2e_score=0.0`
- `PART1_0005`
  - 基线：`top_hit=True`，`ragas_e2e_score=0.7033`
  - LlamaIndex：`top_hit=False`，`ragas_e2e_score=0.0`
- `PART1_0011`
  - 基线：`top_hit=True`，`ragas_e2e_score=0.3452`
  - LlamaIndex：`top_hit=False`，`ragas_e2e_score=0.0`

## 对结果的解释

- 当前 `Vector` 子链切到了 `LlamaIndex` 的 `VectorStoreIndex`，但旧链路中的 `BM25 + cosine` 混合打分没有完全保留。
- 当前 `SQL` 子链虽然切到了 `NLSQLTableQueryEngine`，但生成式 SQL 与项目原有启发式/工具式 SQL 行为并不完全等价。
- 因此这次接入更像“框架切换”，还不是“排序与效果对齐”。

## 评测可信度说明

- 两组结果都出现了 `13` 个 `RAGAS metric error cases`
- 根因是 `gpt-4o` 在评测中触发了 `TPM 429 rate limit`
- 因此：
  - `RAGAS` 均值有一定噪声
  - 但 `top_hit_rate`、图执行成功率、平均延迟仍然具有参考价值
- 如果后续要做正式结论，建议补跑一轮：
  - `ragas_concurrency=1`
  - 或降低 `answer_relevancy_strictness`

## 当前结论

- 从这轮 `20-case` 对比看，当前版本的 `LlamaIndex` 接入 **工程上可用，但效果上未优于基线**。
- 现阶段更合适的定位是：
  - `LlamaIndex` 已成功接入为可选子链实现
  - 但默认生产效果不建议仅因为“框架升级”就直接认定为更优

## 建议动作

- 短期：
  - 保留 `LlamaIndex` 默认开启，但把旧链路继续保留为回退能力
  - 优先调优 `Vector` 子链的排序和 filter 对齐
- 中期：
  - 补 `rerank`
  - 对齐旧链路 `BM25 + cosine` 行为
  - 针对掉点 case 做定向分析
- 长期：
  - 再决定是否扩大 `LlamaIndex` 在系统中的职责边界
