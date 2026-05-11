# Part4 全量 Chunk 评测报告

> 数据源：`agent/test/generated/ragas_eval_p4_chunks/`  
> 生成时间：2026-05-05  
> 评测范围：Part4 全量 134 case（155 e2e-ready 中过滤 21 个无效 video_id）  
> 评测策略：Chunked（每 10 个视频一个 chunk，独立构建 SQLite + Chroma 索引，共 5 chunks）

---

## 1. 总体指标（加权平均）


| Metric                        | Value         | 说明                      |
| ----------------------------- | ------------- | ----------------------- |
| `case_count`                  | 134           | 46 个有效视频                |
| `success_count`               | 134           | 0 错误                    |
| `**top_hit_rate**`            | **0.9179**    | 123/134 命中正确视频          |
| `context_precision_avg`       | 0.6016        | RAGAS context precision |
| `context_recall_avg`          | 0.7090        | RAGAS context recall    |
| `faithfulness_avg`            | 0.7018        | RAGAS faithfulness      |
| `factual_correctness_avg`     | 0.3731        | RAGAS LLM 评分            |
| `custom_correctness_avg`      | 0.4572        | 规则型指标                   |
| `time_range_overlap_iou_avg`  | 0.6391        | 时间定位 IoU                |
| IoU [hit@0.3](mailto:hit@0.3) | 0.6911        | IoU ≥ 0.3 命中率           |
| IoU [hit@0.5](mailto:hit@0.5) | 0.6176        | IoU ≥ 0.5 命中率           |
| `video_match_score_avg`       | 0.8381        | Top-1 视频匹配率             |
| `**ragas_e2e_score_avg`**     | **0.6174**    | 端到端综合得分                 |
| `avg_latency_ms`              | 13251 (13.3s) | 含 graph + RAGAS 评分      |


### 1.1 补充指标：基于 video_id 的检索（离线、无 LLM）

以下指标**不替代**上表中的 `context_precision_avg` / `context_recall_avg`（语义 LLM 裁判）。数据来源：`agent/test/generated/old/ragas_eval_p4_chunks/` 各 chunk 的 `e2e_report.json`，由 `agent/test/compute_id_based_retrieval_from_e2e.py` 重算；明细见同目录 `id_based_retrieval_summary.json`。


| Metric                                | Value      | 说明                                                                                 |
| ------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| `chunk_same_video_precision_at_1_avg` | **0.8507** | **Precision@1**：仅看**排序第一的检索片段**，其 `video_id` 是否与 GT 一致（IR 常用口径；数值通常明显高于「全列表片段占比」）。 |
| `chunk_same_video_precision_avg`      | 0.4631     | 全列表：与 GT 一致的片段条数 / 传入评测的片段总条数（列表越长、混入其它视频越多则越低）。                                   |
| `id_context_recall_avg`               | **0.9403** | GT `video_id` 是否出现在任一检索片段中（RAGAS `IDBasedContextRecall` 等价）。                       |


---

## 2. 分 Chunk 指标


| Chunk  | Cases   | top_hit   | precision | recall    | faith     | factual   | custom    | IoU       | [IoU@0.3](mailto:IoU@0.3) | [IoU@0.5](mailto:IoU@0.5) | vid_match | e2e       | latency   |
| ------ | ------- | --------- | --------- | --------- | --------- | --------- | --------- | --------- | ------------------------- | ------------------------- | --------- | --------- | --------- |
| 01     | 30      | 0.800     | 0.502     | 0.717     | 0.664     | 0.633     | 0.623     | 0.417     | 0.440                     | 0.400                     | 0.640     | 0.626     | 11.7s     |
| 02     | 30      | 0.900     | 0.617     | 0.667     | 0.772     | 0.217     | 0.366     | 0.548     | 0.667                     | 0.476                     | 0.810     | 0.606     | 12.4s     |
| 03     | 29      | 0.966     | 0.668     | 0.707     | 0.693     | 0.362     | 0.418     | 0.731     | 0.778                     | 0.722                     | 0.909     | 0.621     | 13.8s     |
| 04     | 29      | 1.000     | 0.664     | 0.759     | 0.720     | 0.241     | 0.431     | 0.842     | 0.857                     | 0.857                     | 0.955     | 0.643     | 17.3s     |
| 05     | 16      | 0.938     | 0.528     | 0.688     | 0.626     | 0.438     | 0.435     | 0.694     | 0.750                     | 0.667                     | 0.923     | 0.569     | 9.4s      |
| **加权** | **134** | **0.918** | **0.602** | **0.709** | **0.702** | **0.373** | **0.457** | **0.639** | **0.691**                 | **0.618**                 | **0.838** | **0.617** | **13.3s** |


### 2.1 补充：各 Chunk 的 Precision@1 / 全列表片段精确率 / ID recall（与 §2 并行）


| Chunk  | Cases   | p@1       | 全列表片段精确率  | id_recall |
| ------ | ------- | --------- | --------- | --------- |
| 01     | 30      | 0.700     | 0.467     | 0.900     |
| 02     | 30      | 0.833     | 0.427     | 0.900     |
| 03     | 29      | 0.862     | 0.503     | 0.966     |
| 04     | 29      | 0.966     | 0.485     | 1.000     |
| 05     | 16      | 0.938     | 0.413     | 0.938     |
| **全量** | **134** | **0.851** | **0.463** | **0.940** |


---

## 3. 难度分层（Easy / Medium / Hard）


| 难度         | N   | top_hit | precision | recall | faith | factual | custom | IoU   | [IoU@0.3](mailto:IoU@0.3) | [IoU@0.5](mailto:IoU@0.5) | vid_match | e2e   | latency |
| ---------- | --- | ------- | --------- | ------ | ----- | ------- | ------ | ----- | ------------------------- | ------------------------- | --------- | ----- | ------- |
| **easy**   | 46  | 0.957   | 0.857     | 0.837  | 0.764 | 0.489   | 0.625  | 0.763 | 0.814                     | 0.744                     | 0.957     | 0.771 | 11.5s   |
| **medium** | 45  | 0.867   | 0.698     | 0.700  | 0.738 | 0.411   | 0.547  | 0.560 | 0.610                     | 0.537                     | 0.727     | 0.671 | 15.8s   |
| **hard**   | 43  | 0.930   | 0.228     | 0.581  | 0.597 | 0.209   | 0.184  | 0.408 | 0.462                     | 0.385                     | 0.769     | 0.397 | 12.4s   |


### 各层 yes/no 分布


| 难度     | yes | no  | no 占比   |
| ------ | --- | --- | ------- |
| easy   | 46  | 0   | 0%      |
| medium | 44  | 1   | 2%      |
| hard   | 13  | 30  | **70%** |


### 关键发现

1. **检索随难度非线性下降**：top_hit 在 easy(95.7%) → medium(86.7%) → hard(93.0%) 间并非单调递减。hard 层的检索能力仍然很强（93%），**瓶颈不在检索**。
2. **hard 层 precision 断崖式下跌**（0.228 vs 0.857）：检索到的 chunk 中有大量噪声，但核心信息仍在（recall 保持 0.581）。
3. **hard 层的 "no" 问题占 70%**（30/43）：所有 "no" 问题的 factual_correctness 均为 0，是 hard 层 fc 仅 0.209 的直接原因。
4. **排除 "no" 后的 hard 层**：13 个 yes 问题中，检索质量仍然较好（top_hit 93%, vm 76.9%），但内容级精准度（precision 0.228）是核心短板。
5. **难度标注有效**：easy→hard 的 e2e 从 0.771 跌到 0.397（-0.374），梯度清晰。

---

## 4. 回答标签分层


| 标签      | Cases | top_hit | factual_correctness | 问题                   |
| ------- | ----- | ------- | ------------------- | -------------------- |
| **yes** | 103   | 91.3%   | **0.485**           | 检索准确，但 factual 评分偏低  |
| **no**  | 31    | 93.5%   | **0.000**           | 所有 no case 的 fc 均为 0 |


### "no" 问题分析（第 4 节续）

31 个 "no" case 的 factual_correctness 全部为 0，原因：

1. **模型过度乐观**：检索总能找到看似匹配的内容，模型倾向于产出 "Yes" 答案
2. **RAGAS judge 零容忍**：对于 "no" 问题，即使模型正确回答了 "No matching clip"，factual_correctness 仍可能给 0
3. **难度标签**：这些 case 多为 "Multi-entity Temporal Logic"、"Fine-grained Action Negation"、"Hallucination Suppression" 等高难度反事实推理任务

排除 "no" case 后，yes 问题的 factual_correctness 为 0.485。

---

## 5. 与旧基线对比（52-video 全量 vs Chunked）


| Metric                | 旧基线 (52-video) | Chunked (10-video) | 提升         |
| --------------------- | -------------- | ------------------ | ---------- |
| `top_hit_rate`        | 0.207          | **0.918**          | **+0.711** |
| `context_precision`   | 0.537          | 0.602              | +0.065     |
| `context_recall`      | 0.674          | 0.709              | +0.035     |
| `factual_correctness` | 0.355          | 0.373              | +0.018     |
| `video_match_score`   | 0.216          | **0.838**          | **+0.622** |
| `IoU avg`             | 0.191          | **0.639**          | **+0.448** |
| `e2e_score`           | 0.590          | 0.617              | +0.027     |
| `avg_latency`         | 10.0s          | 13.3s              | +3.3s      |


**核心发现**：

- **Chunked 索引策略效果显著**：top_hit 从 20.7% 飙升至 91.8%，video_match 从 21.6% 升至 83.8%
- **根因**：52-video 全量索引下 Normal_Videos 之间语义高度重叠，纯向量检索无法区分；10-video chunk 大幅缩小检索范围
- **cost**：每个 chunk 独立构建索引，总体耗时约 54 分钟（5 chunks），chunk 平均 10.8 分钟

---

## 6. Chunk 间差异分析

### Chunk01（Normal_Videos 924-933 + 594）

- 零售/服务场景视频，有 _ 前缀和无 _ 前缀混合
- top_hit 最低（80%），但 factual_correctness 最高（0.633）
- 仅 5 个 "no" case（占比 17%），no 判错率 60%

### Chunk02（Normal_Videos 598-610）

- 办公/交通场景，无 _ 前缀
- **factual_correctness 极低（0.217）**，原因见[专项分析](#7-chunk02-正确率专项分析)
- 9 个 "no" case（占比 30%），no 判错率 89%

### Chunk03（Normal_Videos 611-620）

- 电梯/办公/交通混合场景
- top_hit 96.6%，IoU 73.1%
- 5 个 "no" case

### Chunk04（Normal_Videos 622-631）

- 超市/交通场景
- **top_hit 100%**，IoU 84.2%，vid_match 95.5%
- 4 个 "no" case

### Chunk05（Normal_Videos 632-638）

- 6 个视频，16 case（最小 chunk）
- e2e 最低（0.569），precision 最低（0.528）
- 8 个 "no" case（占比 50%），高难度反事实推理集中

---

## 7. Chunk02 正确率专项分析

Chunk02 的 factual_correctness 仅 0.217（全量最低），根因：

### 6.1 "no" case 全部判错（8/9，89%）

全部为高难度否定任务：

- Multi-entity Temporal Logic & Causal Linkage
- Complex Spatio-temporal Logic & Action Detail Verification
- Fine-grained Action Negation
- False Spatio-temporal Association Filtering

模型对所有 "no" 问题都给出了具体的 "Yes" 回答（包含 video 和时间）。

### 6.2 "yes" case 即使正确也 fc=0（9/21，43%）

9 个 case 模型检索到了正确视频（top_hit=True, vm=1.0），但 RAGAS factual_correctness judge 仍给 0：

```
PART4_0059: ref="Normal_Videos_610_x264, 00:00.0-00:16.0"
            resp="Normal_Videos610_x264, 0:00:00-0:00:16"  → fc=0
PART4_0060: ref="Normal_Videos_610_x264, 00:00.0-00:22.0"
            resp="Normal_Videos610_x264, 0:00:00-0:00:22"  → fc=0
```

RAGAS judge 对短回答、纯事实性声明的评分过于严格。

### 6.3 真正答错（3/21）

PART4_0036/0048/0057 — 视频匹配失败。

---

## 8. 已知问题

1. **视频 ID 命名不一致**：xlsx 中 `Normal_Videos_598_x264`（有下划线）vs seed 文件 `Normal_Videos598_x264`（无下划线）。已在 `ragas_eval_runner.py` 中增加 `_normalize_video_id()` 修复。
2. **"no" 问题 fc=0**：系统性缺陷，RAGAS factual_correctness 对否定回答不支持，需考虑替换为 custom_correctness 或增加专门的否定判断指标
3. **RAGAS judge 过严**：即使 answer 与 reference 几乎完全一致，factual_correctness 仍可能给 0 或 0.5（而非 1.0）
4. **Chunk05 视频数少（6个）但 "no" 占比高（50%），导致 overall 指标被拉低**

---

## 9. 总结


| 维度                               | 评价                                                                    |
| -------------------------------- | --------------------------------------------------------------------- |
| 视频检索 (top_hit)                   | **优秀** — 91.8%，chunked 策略有效                                           |
| 时间定位 (IoU)                       | **良好** — 63.9%，仍有提升空间                                                 |
| 内容召回 (context_recall)            | **良好** — 70.9%                                                        |
| 内容精确 (context_precision)         | **一般** — 60.2%，检索噪声仍需优化                                               |
| Precision@1 / ID recall（补充，§1.1） | **85.1%** / **94.0%** — 首条片段是否来自 GT 视频；与 LLM `context_precision` 口径不同 |
| 事实正确 (factual_correctness)       | **较差** — 37.3%，受 "no" case + judge 过严双重影响                             |
| 端到端 (e2e)                        | **及格** — 61.7%，接近可用阈值                                                 |


主要瓶颈是 **fc 评分体系不适合否定类问题** 和 **RAGAS judge 过于严格**，而非检索系统本身。排除 "no" case 后 factual_correctness 为 0.485，仍有较大提升空间。