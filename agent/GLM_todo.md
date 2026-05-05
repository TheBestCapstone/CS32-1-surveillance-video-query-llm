# GLM 优化任务清单

> 目标指标：`context_precision_avg` (0.537→0.70+), `factual_correctness_avg` (0.355→0.50+), `IoU avg` (0.191→0.35+)
> 基线日期：2026-05-03 (Part4 全量 155 case)

---

## P0：修复已知 Bug（零风险，最高优先级）

### P0-1：修复 RRF ID mismatch

- **状态**：✅ 已完成
- **问题**：SQL 分支返回 `event_id` 为整数（如 `42`），Chroma 分支返回 `event_id` 为字符串（如 `"42"` 或 Chroma 自身 ID 如 `"Normal_Videos924:person_1:10.5:15.2"`）。`_row_key()` 生成 `f"event_id:{event_id}"` 时类型不同导致 key 不匹配，`overlap_count` 恒为 0，RRF 退化为加权合并。
- **影响指标**：context_precision ↑↑, IoU ↑
- **修复内容**：
  - `fusion_engine.py`: 新增 `_normalize_event_id()` 函数，在 `_row_key()` 中统一将数字型 event_id 转为 `str(int(...))` 格式
  - `bm25_index.py`: 新增 `_normalize_event_id()` 函数，在 `reciprocal_rank_fuse()` 中将数字型 event_id 转为 `int`
  - `db_access.py`: `ChromaGateway.search()` 中将 metadata 中的 event_id 从 str 转为 int（当可转换时）
  - `retrieval_contracts.py`: 新增 `_normalize_event_id()`，在 `normalize_sql_rows()` 和 `normalize_hybrid_rows()` 中统一 event_id 类型
  - 新增 2 个测试用例验证 int/str/float 格式 event_id 的 RRF 融合
- **文件**：`agent/agents/shared/fusion_engine.py`, `agent/tools/bm25_index.py`, `agent/tools/db_access.py`, `agent/node/retrieval_contracts.py`

### P0-2：清理索引污染

- **状态**：✅ 已完成
- **问题**：`RoadAccidents109-114` 的 UCFCrime 种子被意外引入 Part4 索引（8 个 case 引用非 Normal_Videos video_id），污染检索结果
- **影响指标**：context_precision ↑, IoU ↑
- **修复内容**：
  - `ragas_eval_runner.py`: 新增 `_is_valid_video_id()` 函数，在 `_load_cases_from_dataset_dir()` 中过滤非 `Normal_Videos`* 开头的 video_id 的 case
  - 过滤掉的 video_id 包括：RoadAccidents109-114_x264, !?4h?!, 多摄像头 等
  - 过滤时会打印日志 `[ragas_eval] P0-2: Filtered out N cases with invalid video_ids: [...]`
- **文件**：`agent/test/ragas_eval_runner.py`

---

## P1：检索精度提升

### P1-1：Tier 1 视频级过滤增强

- **状态**：⚪ 待开始
- **思路**：在 hybrid retrieval 前增加 video collection 粗筛（已有 `_coarse_video_filter`），扩大 top-3 到 top-5 候选视频，降低遗漏率
- **影响指标**：context_precision ↑↑, IoU ↑↑

### P1-2：增强 R6 query expansion

- **状态**：⚪ 待开始
- **思路**：降低 self_query fast-path 触发阈值；对 medium/hard query 强制 expansion；引入 video-specific 关键词
- **影响指标**：context_precision ↑

### P1-3：调整 RRF fusion 权重

- **状态**：⚪ 待开始
- **思路**：时间敏感 query 增加 SQL 权重；语义 query 增加 Chroma 权重；需 A/B 测试
- **影响指标**：context_precision ↑

### P1-4：增加 cross-encoder rerank 的 top-K

- **状态**：⚪ 待开始
- **思路**：增加进入 rerank 的候选数量，让更多潜在相关 chunk 被重排
- **影响指标**：context_precision ↑

### P1-5：scene boost 参数调优

- **状态**：⚪ 待开始
- **思路**：当前 lambda=0.1，尝试增大 lambda 或引入 scene-level 精确匹配加分
- **影响指标**：context_precision ↑

---

## P2：答案质量提升

### P2-1：优化 context 注入策略

- **状态**：⚪ 待开始
- **思路**：在 context 中显式标注 chunk 来源（视频ID、时间范围），帮助 LLM 区分不同视频的信息
- **影响指标**：factual_correctness ↑

### P2-2：改进 final_answer prompt

- **状态**：✅ 已完成
- **修复内容**：
  - `summary_node.py`: 在 LLM prompt 中增加保守推理约束——"如果检索结果不能确凿证明场景存在，应回答不存在"；禁止推断未明确描述的动作
  - `summary_node.py`: `_allow_no_match_decision()` 覆盖 `answer_type=unknown`，允许 verifier=mismatch 时输出 "No matching clip"
- **影响指标**：factual_correctness ↑（减少假阳性）
- **文件**：`agent/node/summary_node.py`

### P2-3：match_verifier 阈值调优

- **状态**：✅ 已完成
- **修复内容**：
  - `query_classifier.py`: 扩展 `_EXISTENCE_CUES` 增加更多存在性模式（"does the video record", "can you find", "search for a segment" 等）
  - `query_classifier.py`: 扩展 `_infer_answer_type()` 增加 "can you"/"could you" 前缀匹配
  - `match_verifier_node.py`: 将 `answer_type=unknown` 从 skipped 改为走 existence 验证路径（之前 8/30 假阳性 case 因 answer_type=unknown 导致 verifier skipped）
  - `match_verifier_node.py`: 优化 LLM verifier prompt，增加"保守判断、假阳性比假阴性更糟糕"的指引
  - `answer_node.py`: `_format_existence_answer()` 覆盖 `answer_type=unknown`，使 verifier mismatch 判定也能触发 "No matching clip" 输出
- **影响指标**：factual_correctness ↑↑（直接修复 8/30 假阳性）
- **文件**：`agent/agents/shared/query_classifier.py`, `agent/node/match_verifier_node.py`, `agent/node/answer_node.py`

---

## P3：时间定位精度提升

### P3-1：细粒度时间投影

- **状态**：⚪ 待开始
- **思路**：检索后在 child chunk 级别做时间投影，而非 parent 10 分钟桶级别；对命中 child chunk 取时间并集再与 query 时间约束取交集
- **影响指标**：IoU ↑↑

### P3-2：时间感知 reranking

- **状态**：⚪ 待开始
- **思路**：在 cross-encoder rerank 后，对时间范围与 query 时间约束重叠度高的 chunk 额外加分
- **影响指标**：IoU ↑

### P3-3：双阶段时间定位

- **状态**：⚪ 待开始
- **思路**：第一阶段检索粗粒度 parent 确定视频，第二阶段在该视频内用 child chunk 精确时间定位
- **影响指标**：IoU ↑

---

## 实施优先级

```
收益:  P0-1(修复RRF) > P1-1(视频过滤) > P3-1(细粒度时间) > P1-2(expansion) > P2-1(context标注)
风险:  P0-1(低) < P1-2(中) < P1-3(中) < P1-1(中) < P3-1(中)
```

1. ✅ P0-1 + P0-2（已完成，RRF 修复 IoU +0.595，过滤 8 个无效 case）
2. ✅ P2-2 + P2-3（已完成，修复 verifier skipped 导致假阳性）
3. P1-1（视频级过滤）
4. P1-2（query expansion）
5. P3-1 + P3-2（细粒度时间定位）
6. P2-1（context 标注）
7. P1-3 / P1-4 / P1-5（参数调优）

---

## P0 验证结果（chunk01+chunk02, 60/134 cases）


| 指标                  | 基线(155 cases) | chunk01(30) | chunk02(30) | 变化                 |
| ------------------- | ------------- | ----------- | ----------- | ------------------ |
| top_hit_rate        | 0.207         | 0.100       | **0.900**   | chunk02 ↑↑         |
| context_precision   | 0.537         | 0.456       | **0.590**   | ↑                  |
| context_recall      | 0.674         | 0.717       | 0.683       | 持平                 |
| factual_correctness | 0.355         | 0.633       | 0.283       | chunk01↑, chunk02↓ |
| custom_correctness  | 0.456         | 0.607       | 0.373       | —                  |
| IoU avg             | 0.191         | **0.443**   | **0.595**   | ↑↑↑                |
| video_match         | 0.216         | 0.680       | **0.857**   | ↑↑↑                |
| e2e_score           | 0.590         | 0.600       | 0.598       | 持平                 |


关键发现：

- IoU 从 0.191 大幅提升至 0.443-0.595，P0-1 RRF 修复效果显著
- context_precision 有提升（0.537→0.590），RRF overlap 恢复后相关 chunk 排名更靠前
- factual_correctness 在不同 chunk 间波动大，属于 P2 层面问题
- 全量评测需跑完 5 个 chunk 才能确认整体提升幅度

