# Part4 全量测试

> 数据源：`agent/test/generated/ragas_eval_p4_chunks/`

> 评测方式：Chunked（5 chunks）

> 有效 case：60

## 总体指标（加权）


| Metric                       | Value  |
| ---------------------------- | ------ |
| `top_hit_rate`               | 0.5000 |
| `context_precision_avg`      | 0.5232 |
| `context_recall_avg`         | 0.7000 |
| `faithfulness_avg`           | 0.6822 |
| `factual_correctness_avg`    | 0.4583 |
| `custom_correctness_avg`     | 0.4902 |
| `time_range_overlap_iou_avg` | 0.5192 |
| `IoU hit@0.3`                | 0.5772 |
| `IoU hit@0.5`                | 0.4819 |
| `video_match_score_avg`      | 0.7685 |
| `ragas_e2e_score_avg`        | 0.5989 |
| `avg_latency_s`              | 13.9s  |


## 分 Chunk 指标


| Chunk | Cases | top_hit | precision | recall | factual | custom | IoU   | vid_match | e2e   | latency |
| ----- | ----- | ------- | --------- | ------ | ------- | ------ | ----- | --------- | ----- | ------- |
| 01    | 30    | 0.100   | 0.456     | 0.717  | 0.633   | 0.607  | 0.443 | 0.680     | 0.600 | 12.2s   |
| 02    | 30    | 0.900   | 0.590     | 0.683  | 0.283   | 0.373  | 0.595 | 0.857     | 0.598 | 15.6s   |
