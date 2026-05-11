# UCA 转录 Part4 全量评测

> **数据源（seed）**：`data/part4_pipeline_output/uca_vector_flat/`（由 `*_events_uca.json` 经 `scripts/convert_uca_to_vector_flat.py` 转为 `*_events_vector_flat.json`）

> **结果目录**：`agent/test/generated/ragas_eval_p4_full/`

> **评测方式**：`run_chunks.py` 分 5 批（每批按 `video_id` 分组，默认每批 10 个视频；最后一批 6 个视频）

> **RAGAS 配置**：`--retrieval-metrics-backend id_based`，`--ragas-contexts-filter same_expected_video`

> **有效 case**：**134**（Part4 过滤垃圾行后按视频分块；各批 case 数见下表）

### 检索：`context_precision` / `context_recall` 与粗排补充指标（均保留）

- `**context_precision_avg` / `context_recall_avg`**：仍采用 RAGAS 报告字段名，对应 **id_based** 后端在 **「同视频过滤后、参与打分的 chunk」** 上的精度与 `IDBasedContextRecall`。本跑汇总为 **1.0 / 1.0**，表示评分用语境在视频 ID 上与 GT 一致且 recall 判据满足；**不**等价于未过滤 Top‑5 的跨视频难度。
- `**top_hit_rate`**：Top‑5 中是否出现 GT 视频（ID 与 `ragas_eval_runner._normalize_video_id` 一致）。
- `**top5_gt_video_slot_share_avg`**：在未做同视频过滤的 `**top_video_ids**` 上，GT 视频所占槽位比例（每题 0～1）再对 134 题取平均，用于观察「进榜后同视频 chunk 浓度」，与上两项互补。

## 总体指标（按各批 case 数加权平均）


| Metric                         | Value  |
| ------------------------------ | ------ |
| `top_hit_rate`                 | 0.8507 |
| `top5_gt_video_slot_share_avg` | 0.4358 |
| `context_precision_avg`        | 1.0000 |
| `context_recall_avg`           | 1.0000 |
| `faithfulness_avg`             | 0.8144 |
| `factual_correctness_avg`      | 0.4851 |
| `custom_correctness_avg`       | 0.5869 |
| `time_range_overlap_iou_avg`   | 0.5842 |
| `IoU hit@0.3`                  | 0.6083 |
| `IoU hit@0.5`                  | 0.5464 |
| `video_match_score_avg`        | 0.7699 |
| `ragas_e2e_score_avg`          | 0.7812 |
| `avg_latency_s`                | 11.2s  |


加权说明：`top_hit`、`context_precision_avg`、`context_recall_avg`、`factual_corr`、`custom_corr`、`e2e`、`iou_avg`、`vid_match_avg`、`latency_s` 取自各批 `results.csv`，按该批 **cases** 加权；`faithfulness_avg` 与各批 **IoU hit@*** 由对应 `chunkNN/summary_report.json` 中的 `faithfulness_avg`、`time_range_overlap_iou_hit_rate_at_`* 与 `time_range_overlap_iou_case_count` 做 eligible 题数加权。`top5_gt_video_slot_share_avg` 由 `chunkNN/e2e_report.json` 逐题按上节定义聚合。

## 分难度指标（xlsx `difficulty_level`）

自各批 `dataset_part1_part4/agent_test_normalized.json` 读取难度，与 `e2e_report.json` 按 `case_id` 对齐（134 题：easy 46 / medium 45 / hard 43）。**precision / recall**（RAGAS 字段 `context_precision` / `context_recall`）仍列出：共 **20** 题在过滤后无可用 context，RAGAS 未返回这两项，表中均值仅对 **有值** 题计算（本题集内有值题均为 1.0）。


| 难度     | Cases | top_hit | top5_slot_share | precision | recall | e2e    | custom | factual | faith  | IoU    |
| ------ | ----- | ------- | --------------- | --------- | ------ | ------ | ------ | ------- | ------ | ------ |
| easy   | 46    | 0.8478  | 0.4652          | 1.0       | 1.0    | 0.7880 | 0.5672 | 0.4239  | 0.9487 | 0.7151 |
| medium | 45    | 0.8222  | 0.3778          | 1.0       | 1.0    | 0.7394 | 0.5182 | 0.3889  | 0.8005 | 0.5102 |
| hard   | 43    | 0.8837  | 0.4651          | 1.0       | 1.0    | 0.8178 | 0.6799 | 0.6512  | 0.6874 | 0.3063 |


**top5_slot_share**：与总表 `top5_gt_video_slot_share_avg` 同定义。**IoU**：`time_range_overlap_iou` 在该难度下有值题上的平均。

## 分 Chunk 指标


| Chunk | Cases | top_hit | precision | recall | factual | custom | IoU    | vid_match | e2e    | latency |
| ----- | ----- | ------- | --------- | ------ | ------- | ------ | ------ | --------- | ------ | ------- |
| 01    | 30    | 0.8000  | 1.0       | 1.0    | 0.6833  | 0.6673 | 0.4032 | 0.6000    | 0.7927 | 10.3s   |
| 02    | 30    | 0.8333  | 1.0       | 1.0    | 0.3667  | 0.4996 | 0.5567 | 0.7619    | 0.7442 | 12.0s   |
| 03    | 29    | 0.9310  | 1.0       | 1.0    | 0.5517  | 0.6651 | 0.7308 | 0.8636    | 0.8664 | 11.4s   |
| 04    | 29    | 0.8276  | 1.0       | 1.0    | 0.3448  | 0.5188 | 0.6536 | 0.8182    | 0.7323 | 11.9s   |
| 05    | 16    | 0.8750  | 1.0       | 1.0    | 0.4688  | 0.5813 | 0.5833 | 0.8462    | 0.7633 | 9.7s    |


（与 `results.csv` 列名一致：`precision` / `recall` 即 RAGAS 汇总中的 `context_precision_avg` / `context_recall_avg`。）

## 运行说明与缺 seed 告警

全量日志中各批曾出现 **源目录无对应 seed 文件** 的告警（该视频仍可能出现在检索候选中，但子库未从该视频 seed 建表）：


| Chunk | 缺 seed 的 `video_id`                               |
| ----- | ------------------------------------------------- |
| 01    | `Normal_Videos_924_x264`                          |
| 04    | `Normal_Videos_630_x264`                          |
| 05    | `Normal_Videos_633_x264`、`Normal_Videos_638_x264` |


补齐方式：在 `uca_vector_flat`（或上游 UCA 产物）中生成并放入对应 `*_events_vector_flat.json` 后，对受影响批次重跑即可。

## 复现实验命令（节选）

在 `agent/test` 下：

```bash
conda activate capstone
python run_chunks.py \
  --seed-dir ../../data/part4_pipeline_output/uca_vector_flat \
  --output-root generated/ragas_eval_p4_full \
  --retrieval-metrics-backend id_based \
  --ragas-contexts-filter same_expected_video \
  --no-progress
```

逐批明细与逐题结果见：`generated/ragas_eval_p4_full/chunkNN/summary_report.md`、`summary_report.json`。