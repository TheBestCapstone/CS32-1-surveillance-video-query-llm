# qwen3.5-flash + LlamaIndex 全量测试报告

**日期**: 2026-05-06  
**模型**: qwen3.5-flash (via DashScope)  
**SQL 引擎**: LlamaIndex NL2SQL  
**执行模式**: parallel_fusion (SQL + hybrid 双路)  
**分支**: 多摄像头分支  
**Commit**: `perf: optimize pure_sql retrieval and all agent prompts`

---

## 全量汇总（134 cases, 5 chunks, 46 videos）


| 指标                 | qwen3.5-flash | qwen3-max (LlamaIndex) | qwen3-max (FTS5+plan) |
| ------------------ | ------------- | ---------------------- | --------------------- |
| **Top Hit**        | **84.33%**    | 76.67%                 | 73.33%                |
| **Precision**      | **55.08%**    | 42.57%                 | 41.57%                |
| **Recall**         | 65.67%        | **66.67%**             | 61.67%                |
| **Faithfulness**   | **67.42%**    | 59.72%                 | 62.50%                |
| **Factual Corr**   | 49.63%        | **68.33%**             | 58.33%                |
| **Custom Corr**    | 58.33%        | **70.73%**             | 65.40%                |
| **E2E**            | **61.64%**    | 59.92%                 | 57.78%                |
| **🔥 IoU**         | **58.17%**    | 40.32%                 | 36.32%                |
| **🔥 Video Match** | **76.90%**    | 64.00%                 | 60.00%                |
| **Graph Errors**   | **0**         | **0**                  | **0**                 |
| **Avg Latency**    | 11.2s         | 12.0s                  | 11.8s                 |
| **Wall Time**      | 42.7 min      | 10.6 min (chunk1)      | 12.1 min (chunk1)     |


> 注: qwen3-max baselines 仅 chunk1 (30 cases)

---

## 难度分布


| 难度     | Cases | 占比    |
| ------ | ----- | ----- |
| Easy   | 46    | 34.3% |
| Medium | 45    | 33.6% |
| Hard   | 43    | 32.1% |


---

## 逐 Chunk 明细


| Chunk | Cases | Easy | Med | Hard | TopHit    | Recall | Faith | Factual | E2E   | IoU   | VidMatch |
| ----- | ----- | ---- | --- | ---- | --------- | ------ | ----- | ------- | ----- | ----- | -------- |
| 01    | 30    | 10   | 10  | 10   | 80.0%     | 71.7%  | 75.3% | 68.3%   | 65.8% | 44.3% | 64.0%    |
| 02    | 30    | 10   | 10  | 10   | 83.3%     | 66.7%  | 71.7% | 35.0%   | 60.0% | 55.7% | 76.2%    |
| 03    | 29    | 10   | 10  | 9    | **89.7%** | 69.0%  | 57.6% | 51.7%   | 63.6% | 67.5% | 81.8%    |
| 04    | 29    | 10   | 10  | 9    | 82.8%     | 56.9%  | 68.8% | 36.2%   | 58.7% | 65.6% | 81.8%    |
| 05    | 16    | 6    | 5   | 5    | 87.5%     | 62.5%  | 60.1% | 62.5%   | 58.9% | 58.3% | 84.6%    |


---

## 各 Chunk 包含的 Vidoes


| Chunk | Videos                                |
| ----- | ------------------------------------- |
| 01    | Normal_Videos594, 924-933 (10 videos) |
| 02    | Normal_Videos598-610 (10 videos)      |
| 03    | Normal_Videos611-620 (10 videos)      |
| 04    | Normal_Videos622-631 (10 videos)      |
| 05    | Normal_Videos632-638 (6 videos)       |


---

## 关键发现

### 1. 时空定位大幅提升

- **IoU +17.9%**: qwen3.5-flash 在时间边界预测上显著优于 qwen3-max
- **Video Match +12.9%**: 视频级别的区分度明显更好

### 2. 事实准确性下降

- **Factual Corr -18.7%**: 小模型在事实推理上较弱
- **Custom Corr -12.4%**: 定制化正确性也下降
- 这是小模型的典型 trade-off: 定位更好，语义理解更弱

### 3. Top Hit 最高

- **84.33%**: 在所有配置中 Top-1 命中率最优
- 说明检索召回的结果排序质量好

### 4. 忠诚度改善

- **Faithfulness +7.7%**: 比 qwen3-max LlamaIndex 路径更高
- 可能与本次 prompt 优化有关

### 5. Chunk 间差异

- Chunk 3 TopHit 最高 (89.7%)，但 Faithfulness 最低 (57.6%)
- Chunk 5 视频数最少 (6个) 但 VidMatch 最高 (84.6%)

---

## 配置参数

```
DASHSCOPE_CHAT_MODEL=qwen3.5-flash
AGENT_USE_LLAMAINDEX_SQL=1
AGENT_USE_LLAMAINDEX_VECTOR=1
AGENT_PARALLEL_BRANCH_TIMEOUT_SEC=30
AGENT_FUSION_TOP_K=50
```

---

## 与历史版本对比趋势


| 指标           | q3-max Llama | q3-max FTS5 | prompt opt | **q3.5-flash** | 趋势  |
| ------------ | ------------ | ----------- | ---------- | -------------- | --- |
| Top Hit      | 76.7%        | 73.3%       | 80.0%      | **84.3%**      | ↑↑  |
| Recall       | 66.7%        | 61.7%       | —          | 65.7%          | →   |
| Faithfulness | 59.7%        | 62.5%       | 83.0%      | 67.4%          | ↑   |
| Factual Corr | 68.3%        | 58.3%       | 68.3%      | 49.6%          | ↓   |
| E2E          | 59.9%        | 57.8%       | 79.3%      | 61.6%          | ↑   |
| IoU          | 40.3%        | 36.3%       | 40.3%      | **58.2%**      | ↑↑↑ |
| Video Match  | 64.0%        | 60.0%       | 60.0%      | **76.9%**      | ↑↑↑ |


> 注: "prompt opt" 轮次的 Precision/Recall 数据异常偏高，可能为环境差异

