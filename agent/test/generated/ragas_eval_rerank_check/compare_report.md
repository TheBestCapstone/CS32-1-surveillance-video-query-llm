# Rerank 后 RAGAS 对比报告

## 评测范围

- 数据范围：`Part1 + Part4`
- 本次验证批次：`10` 个 `e2e_ready` case
- 对比对象：
  - 基线链路：`AGENT_USE_LLAMAINDEX_SQL=0`，`AGENT_USE_LLAMAINDEX_VECTOR=0`，`AGENT_ENABLE_RERANK=0`
  - Rerank 后 LlamaIndex 链路：`AGENT_USE_LLAMAINDEX_SQL=1`，`AGENT_USE_LLAMAINDEX_VECTOR=1`，`AGENT_ENABLE_RERANK=1`
- 评测配置：
  - `ragas_concurrency=1`
  - `ragas_case_batch_size=1`
  - `answer_relevancy_strictness=1`
  - `ragas_metric_max_retries=4`
  - `ragas_metric_retry_delay_sec=2.0`

## 本次新实验参数

- 仅重跑新的 `rerank` 链路，不重跑基线
- 新实验环境参数：
  - `AGENT_USE_LLAMAINDEX_SQL=1`
  - `AGENT_USE_LLAMAINDEX_VECTOR=1`
  - `AGENT_ENABLE_RERANK=1`
  - `AGENT_RERANK_CANDIDATE_LIMIT=40`
  - `AGENT_RERANK_TOP_K=5`
  - `AGENT_FUSION_TOP_K=80`
- 旧 `rerank` 对照参数：
  - `AGENT_RERANK_CANDIDATE_LIMIT=20`
  - `AGENT_RERANK_TOP_K=5`
  - `AGENT_FUSION_TOP_K=50`

## 结果总览

| 指标 | 基线链路 | Rerank 后 LlamaIndex | 放大候选池 Rerank | 结论 |
|---|---:|---:|---:|---|
| `case_count` | `10` | `10` | `10` | 持平 |
| `success_count` | `10` | `10` | `10` | 持平 |
| `top_hit_rate` | `0.8` | `0.9` | `0.8` | 原始 rerank 最好 |
| `avg_latency_ms` | `10889.18` | `16273.49` | `15567.24` | 放大候选池仍慢于基线，但略快于原始 rerank |
| `context_precision_avg` | `0.4375` | `0.3889` | `0.4375` | 放大候选池回到基线水平 |
| `context_recall_avg` | `0.375` | `0.3889` | `0.375` | 原始 rerank 最高 |
| `faithfulness_avg` | `0.2201` | `0.3125` | `0.3067` | 两版 rerank 都明显更高 |
| `answer_relevancy_avg` | `0.3323` | `0.3404` | `0.3446` | 放大候选池最高 |
| `factual_correctness_avg` | `0.014` | `0.012` | `0.014` | 放大候选池回到基线水平 |
| `ragas_e2e_score_avg` | `0.2345` | `0.2667` | `0.2508` | 原始 rerank 最好 |
| `ragas_metric_error_cases` | `0` | `0` | `0` | 全部已修复 |

## 调优动作

- `SQL` 子链：
  - 当 `LlamaIndex SQL` 返回 `0` 行时，自动回退到旧的启发式 SQL 检索
- `Vector` 子链：
  - 先走 `LlamaIndex VectorStoreIndex`
  - 若带 filter 无结果，则自动放宽为无 filter 检索
  - 对候选结果增加本地 `BM25 + vector score` 轻量重排
  - 若仍为空，则回退到旧的 `ChromaGateway.search()`
- `Rerank`：
  - 在 `Weighted RRF` 之后接入轻量 `cross-encoder`
  - 当前模型：`cross-encoder/ms-marco-MiniLM-L-6-v2`
  - 接入位置：`fusion -> rerank -> parent projection`
  - 新实验额外放大了 `rerank` 前候选池与融合候选上限
- `RAGAS`：
  - 保持单 case 分批评分
  - 对 `429/rate limit/timeout` 增加重试和退避
  - 默认 `ragas_concurrency=1`
  - 默认 `ragas_case_batch_size=1`

## 相对上一轮未接 Rerank 的变化

- 参照上一份 `10-case` 调优报告中的 LlamaIndex 链路：
  - `top_hit_rate`：`0.9 -> 0.9`，持平
  - `ragas_e2e_score_avg`：`0.2546 -> 0.2667`，有提升
  - `faithfulness_avg`：`0.2431 -> 0.3125`，明显提升
  - `context_recall_avg`：`0.2222 -> 0.3889`，明显提升
  - `avg_latency_ms`：`14748.17 -> 16273.49`，进一步上升

## 放大候选池实验结论

- 相比原始 `rerank`：
  - `top_hit_rate`：`0.9 -> 0.8`，下降
  - `ragas_e2e_score_avg`：`0.2667 -> 0.2508`，下降
  - `answer_relevancy_avg`：`0.3404 -> 0.3446`，小幅上升
  - `faithfulness_avg`：`0.3125 -> 0.3067`，基本持平略降
  - `avg_latency_ms`：`16273.49 -> 15567.24`，略有下降
- 这说明单纯放大 `rerank` 前候选池，不会稳定带来更好的首命中或端到端分数。
- 当前最优仍然是上一版默认候选池的 `rerank` 方案。

## 关键结论

- `ragas_metric_error_cases` 继续保持为 `0`，说明新的 case 分批评分策略稳定有效
- 接入 `rerank` 后：
  - `top_hit_rate` 继续高于基线
  - `ragas_e2e_score_avg` 继续高于基线
  - `faithfulness` 和 `context_recall` 相比未接 `rerank` 的 LlamaIndex 链路也有提升
- 当前主要代价仍然是时延上升
- 放大 `rerank` 前候选池后，没有进一步提升总效果，说明候选扩张不是当前最优方向

## 仍需继续优化的点

- 时延：`rerank` 增加后，图执行平均耗时继续上升
- `context_precision_avg` 低于基线，说明精排后上下文纯度仍可继续调优
- `factual_correctness_avg` 没有同步提升，说明答案生成端还存在改进空间

## 下一步建议

- 保持 `rerank_candidate_limit=20` 作为当前默认实验值
- 针对 `factual_correctness` 不升反降的 case 做定向分析
- 在 `50-case` 或全量 `310-case` 上复核 `rerank` 收益
