# RAGAS 评估与任务原生指标的错配

> 这篇文档是一次 50 例端到端评测后的总结，用于记录 **"系统其实在工作、但被 RAGAS 的错误目标误导"** 这一现象，并把达成一致的改动方案落进代码。

---

## 1. 现象

在 `agent_test.xlsx` 的 Part1 / Part4 上跑 `ragas_eval_runner.py --limit 50 --prepare-subset-db`，结果如下：


| 指标                    | 值             | 性质      |
| --------------------- | ------------- | ------- |
| `top_hit_rate`        | **1.0 / 0.9** | 系统找对了视频 |
| `factual_correctness` | 0.49 – 0.90   | 事实是对的   |
| `context_precision`   | 0.18 – 0.45   | 长期偏低    |
| `context_recall`      | 0.15 – 0.30   | 长期偏低    |
| `faithfulness`        | 0.19 – 0.40   | 长期偏低    |
| `time_range_iou`      | **0.13**      | 真正的瓶颈   |


`top_hit_rate = 1.0`、`factual_correctness` 偏高，两者说明 **检索与事实判断本身是成立的**；但 `context_precision / recall / faithfulness` 却持续偏低。

---

## 2. 诊断：问题出在 reference 的形态

`agent_test_importer.py` 里 `_build_reference_answer` 产出的 `reference_answer` 是 **指针式** 答案：

> "Yes. The relevant clip is in Abuse037_x264, around 0:00:06 - 0:00:22."

这种 reference 只包含视频 ID + 时间戳，**不含场景内容**。RAGAS 的 LLM judge 按如下方式计算每项指标：

- `**context_recall`**：判断 reference 里的"信息"在 context 里能否找到。reference 文本里只有视频名和时间戳，context 里描述的是"灰狗拽尾巴"，judge 当然觉得"信息没覆盖"。→ **永远低**
- `**context_precision`**：判断 context 里的句子和 reference 的相关性。同理，judge 看不出相关性。→ **永远低**
- `**faithfulness`**：判断答案是否"基于" context。答案是"Yes. The relevant clip is in X, around Y-Z"，几乎没有 atomic claim 可追溯回 context。→ **永远低**
- `**factual_correctness`**：判断答案在事实上对不对。你说对了视频和时间，这一项就会是高的。→ **能正确反映系统真实质量**

**结论**：`top_hit = 1.0 + factual_correctness` 偏高说明系统是 work 的，是 RAGAS 的其他三个指标 **系统性低估**了实际质量。

---

## 3. 不该做的事

**不要**盯着 `context_precision` 和 `context_recall` 调系统。这两个指标在本任务上不可靠，优化它们等于在错误的目标上做梯度下降——很可能损害真实质量。

例子：要拉高 `context_precision` 最简单的办法是只返回 top-1。但这会让 verifier 失去多 chunk 上下文（是之前 0008 / 0009 / 0010 失败的根因），真实质量下降。

---

## 4. 真正该看的指标


| 状态        | 指标                                     | 说明                  |
| --------- | -------------------------------------- | ------------------- |
| ✅ 对的指标    | `top_hit_rate`                         | 已 1.0               |
| ✅ 对的指标    | `factual_correctness`                  | 0.7 → 0.9，真实在涨      |
| ✅ **最该盯** | `time_range_iou`                       | **0.133 太低，是真正的瓶颈** |
| ❌ 任务不匹配   | `context_precision` / `context_recall` | 先别管                 |
| ❌ 答案太短    | `faithfulness`                         | 指标失真                |


`top_hit = 1.0`、`IoU = 0.13` 的组合是非常明确的一句话：**系统找对了视频，但找错了时间段**。

---

## 5. 本次改动方案（已达成一致）

### 5.1 丰富 reference：给 RAGAS 一个有"语义内容"的 ground truth

给 importer 额外产出一份 **富 reference**：

```
"Yes. In Abuse037_x264 between 0:00:06 and 0:00:22, <scene description>."
```

其中 `<scene description>` 取自 `recall_challenge`（如果有），否则回退到 `question` 本身（去掉"Is there..."之类的疑问包装）。

落地：

- `agent_test_importer.py` 每个 case 新增两个字段：
  - `reference_scene_description`：原始的场景描述短文；
  - `reference_answer_rich`：把 scene description 拼进视频/时间锚点的自然句。
- `reference_answer` 仍保留指针式（历史脚本与 summary 模板依然可用）。
- `ragas_eval_runner._score_case_with_ragas` 优先用 `reference_answer_rich` 作为 RAGAS 的 reference，使 `context_recall / context_precision / faithfulness` 有真实内容可对齐。

这是对"评估协议"的修正，**不**改 retrieval 系统本身。

### 5.2 新增任务原生指标：让我们不再被 RAGAS 牵着鼻子走

在 `ragas_eval_runner._score_time_range_overlap` 的基础上扩展：

```python
def temporal_iou(pred_range, ref_range):
    if not pred_range or not ref_range:
        return 0.0
    p_s, p_e = pred_range
    r_s, r_e = ref_range
    inter = max(0.0, min(p_e, r_e) - max(p_s, r_s))
    union = max(p_e, r_e) - min(p_s, r_s)
    return inter / union if union > 0 else 0.0

def video_id_hit(pred_vid, ref_vid):
    return 1.0 if pred_vid == ref_vid else 0.0

def localization_score(pred, ref):
    return video_id_hit(pred.vid, ref.vid) * temporal_iou(pred.range, ref.range)
```

落地：

- 每条 case 的 `temporal` dict 额外写入 `video_match_score`（1.0 / 0.0）和 `localization_score`。
- `summary_report.json`：
  - `temporal_summary.localization_score_avg` —— 视频对 × IoU 的均值（主指标）。
  - `video_id_match_rate_top1` —— 预测的 top-1 视频 ID 是否等于 GT 视频 ID 的命中率。
- `top_hit_rate`（top-K 命中）继续保留。

### 5.4 `custom_correctness`（P1-Next-C，规则型、0 LLM）

与 RAGAS `factual_correctness`（LLM 裁判、仍有方差）**并行**：runner 同时输出两者；**合成 `ragas_e2e_score` 时用 `custom_correctness` 替代 `factual_correctness`**，避免端到端均值被 LLM 抖动拖垮。`factual_correctness_avg` 仍保留在报告里作对照参考。

- **预测标签**：从 `final_answer` 文本用启发式归类为 `yes` / `no`（对齐 `summary_node`：`No matching…`、`The most relevant clip…`、`Yes. The relevant clip…`）。
- **视频与时间**：`predicted_video_id` / `predicted_*_sec` 与现有 `temporal` 指标一致，取自 top 检索行（非从答句再解析）。
- **公式**（与 `agent/todo.md` 一致）：
  - 期望为 `yes` 且有时间窗：`0.4×yes_no + 0.4×video_id + 0.2×min(1, IoU + bonus)`，其中 `bonus=0.2` 当 `IoU≥0.5`。
  - 期望为 `yes` 且无时间：`0.5×yes_no + 0.5×video_id`。
  - 期望为 `no`：不比较 `video_id`；有时间窗时 `0.5×yes_no + 0.5×time_term`，无时间窗时仅 `yes_no`。
- **模糊时间**：`expected_time_is_approx=1` 时，将 GT 区间在 IoU 上按 **±5s** 扩张后再算重叠。

实现：`agent/test/ragas_eval_runner.py` 中 `_compute_custom_correctness`；单测：`agent/test/test_custom_correctness.py`。

**可读报告**：每次评测结束后在 `--output-dir` 生成 `REPORT_TABLES.md`（`agent/test/eval_report_tables.py`），汇总 **§2.3 自定义指标**、逐条 `custom_correctness_detail`、任务原生 IoU / video_match、以及 RAGAS 宽表；仅补跑报告：`python agent/test/scripts/regen_report_tables.py --output-dir <run 目录>`。

### 5.3 优先级

- **P0（本次）**：5.1 + 5.2。对齐评估协议，把主指标转到任务原生指标上。
- **P1（下一步）**：修 verifier 的多 chunk 输入策略，让它能看到同一 video_id 下时间相邻的 top-K event，抬 `factual_correctness` 和 `localization_score`。
- **P2（进一步）**：若 `factual_correctness` 不再提升，回到检索侧（re-rank / event-level chunk / 同视频相邻片段聚合）。

---

## 6. 分阶段验收

- **阶段 A（本次）**：
  - `context_precision` / `context_recall` / `faithfulness` 明显上升（因为 reference 现在有真实内容）；
  - `factual_correctness` 维持或上升；
  - 新指标 `localization_score_avg` 与 `time_range_iou_avg` 可解释 Top-hit=1.0 但 IoU 偏低的现象。
- **阶段 B（P1 完成）**：`localization_score_avg` ≥ 0.35（当前一眼估计 < 0.15）。
- **阶段 C（P2 完成）**：`factual_correctness_avg` ≥ 0.75（当前 0.49）。

---

## 7. 备注

- 本次改动**只改评估协议**，不动检索/路由/verifier/answer 节点。
- 一切 RAGAS 指标的波动在本次之后应**基于富 reference 的新基线**看，别再和旧跑分直接对比。

