# Recall Diagnosis — 2026-05-02

> 触发：四次 50-case eval（fts5_bm25 baseline → no_verifier sanity → P1-Next-A bail-out fix → P1-7 v2.3 reselect）context_recall 长期卡在 **0.30 ~ 0.39**，最近一次 v2.3 还回退到 **0.297**。本报告纯诊断，回答"recall 为何低 + 怎么改"，不动代码、不重跑 eval。
>
> 输入数据：`agent/test/generated/ragas_eval_e2e_n50_p1_next_a_v1/e2e_report.json`（基线，`reference_source=rich`，n=50），辅以另外三份 50-case 报告横向对比。
> RAGAS 版本：0.4.3，安装在 `/home/yangxp/anaconda3/lib/python3.13/site-packages/ragas/`。

---

## 0. TL;DR

1. **RAGAS context_recall 不是 retrieval 的传统召回**，它是用 LLM 把 **`reference` 答案** 拆成一组陈述句（statements），再判断每句是否能被 `retrieved_contexts` 支撑。分母是参考答案的句子数，不是 retrieval 数据集的真实正例数。算法见 `ragas/metrics/_context_recall.py:114-156`。
2. 在我们的 pipeline 上，分子（被支撑的句子数）持续偏低有 **三个独立原因叠加**，都不是"retrieval 没召回到正例"：
   - **A. 评测注释污染参考答案**：`reference_answer_rich` 的尾部 `scene_description` 实际是数据集作者的 *recall_challenge 备注*（"Minimal", "Must link X to Y", "Bystander has no actions; easily overlooked in action-based retrieval"…）。RAGAS 把这些备注当成事实拆出来，必然判不可归因。
   - **B. 进入 RAGAS 的 chunk 文本一半丢失了 video_id 头**：56% 的 context（84/150）只有裸的 `From Xs to Ys, ...` 事件句，没有 `Video <video_id>. Track <segment>.` 前缀；导致参考里的 `In <video_id> around <time>` 这条事实无从对齐。
   - **C. RAGAS 看到的 chunk 数被人为限制为 3**（`--ragas-max-contexts=3`），即使 retrieval 的 `rerank_top_k=5`；并且 v2.3 reselect 里 verifier 选的"最相关 1 个 chunk"反而把多 fact 答案需要的多个 chunks 排出窗口。
3. 真实"retrieval 召不到正例"的 case 只有少数（如 `top_hit=False` 的 3/50 case，或时段错位的 PART1_0008/0010 这种长视频中段被错过）。**剩下大量 recall=0 ~ 0.5 的 case 其实是评测/接口/格式工程问题，不是检索质量问题。**
4. 最佳"先做"投资 = **修参考答案 + 修传给 RAGAS 的 context 形态 + 把 RAGAS 看到的 chunk 数提到 5**（一份 PR 内全完成，不动 retrieval/index）。预计 context_recall 从 ~0.36 提升到 0.55~0.65。
5. 真实检索质量改进（更大 top-K、更好 reranker、长视频分段、query 改写）应在第二步独立 A/B；过早动它会被评测噪声掩盖，无法判断真实收益。

---

## 1. RAGAS context_recall 算法精确解析

### 1.1 默认 metric = `LLMContextRecall`

源码：`ragas/metrics/_context_recall.py:88-156`。算法步骤：

1. 输入：`user_input`（query）、`retrieved_contexts: list[str]`、`reference: str`。
2. **把 `retrieved_contexts` 用 `\n` 拼成一个大字符串**，作为单一 `context` 传给 LLM。`_ascore` 第 140 行：
   ```python
   context="\n".join(row["retrieved_contexts"]),
   ```
3. **把 `reference` 整段当成 `answer` 传给 LLM**（不是 user response，是 reference！）。
4. LLM prompt：`ContextRecallClassificationPrompt`（line 45-84），instruction 原文：
   > "Given a context, and an answer, analyze each sentence in the answer and classify if the sentence can be attributed to the given context or not. Use only 'Yes' (1) or 'No' (0) as a binary classification. Output json with reason."
5. LLM 返回每个 sentence 的 `attributed: 1|0`。`_compute_score`：
   ```python
   numerator = sum(1 if item.attributed else 0 for item in responses)
   denom = len(responses)
   score = numerator / denom
   ```
6. 多次 sample 后会通过 `ensembler.from_discrete(...)` 做 ensemble（line 152）。

### 1.2 关键含义

- **分母 = 参考答案被 LLM 拆出的句子数**，不是数据集的真实正例数。
- **分子 = 这些句子能在拼接 contexts 里找到支撑的数量**。判断由 LLM 自由心证，不是字面匹配。
- 因此 context_recall **强烈依赖参考答案的写法**：
  - 参考越短 / 句子越少 → 分母小，单句失误代价大（一句错就是 0.5 / 0.0）。
  - 参考混入"评测说明"（meta sentence）→ 这种句子在 contexts 里几乎不可能找到支撑，永远扣分。
  - 参考含 video_id / 时间戳 → contexts 必须显式出现这些 token 才能被归因。

### 1.3 不要混淆的两个邻居 metric

- `NonLLMContextRecall`（line 165-223）：基于 string similarity 的逐 reference_context 比对，需要 `reference_contexts: list[str]`，我们没用。
- `IDBasedContextRecall`（line 226-282）：纯 ID 集合比较，需要 `reference_context_ids`，我们也没用。

我们用的就是 `LLMContextRecall`（`ragas_eval_runner.py:524, 529-532`）。

---

## 2. 我们当前 pipeline 喂给 RAGAS 的"参考答案"长什么样

### 2.1 参考答案构造路径

`agent/test/agent_test_importer.py:509-538` 的 `_build_reference_answer_rich`：

```
英文 yes：f"Yes. In {video_id} around {expected_time_raw}, {scene_description}."
英文 no： "No matching clip is expected."
```

其中 `scene_description` 来自 `_build_reference_scene_description`（line 496-506），它直接把源 XLSX 的 `recall_challenge` 列原样塞进去（去掉句号）。

`recall_challenge` 是数据集作者填写的 **"这条 case 在召回上为什么难"** 备注，本身不是答案的一部分。50/50 case 都有非空的 `scene_description` 尾巴（实测）。

### 2.2 评测注释污染样例（来自 `e2e_report.json` 抽样）

| case | reference_answer_rich（实际传给 RAGAS） | recall |
|---|---|---|
| PART1_0008 | `Yes. In Abuse039_x264 around 0:03:03 - 0:04:40, Minimal.` | 0.00 |
| PART1_0012 | `Yes. In Abuse040_x264, Caregiving and violence coexist; contradiction must be recognized.` | 0.00 |
| PART1_0013 | `Yes. In Abuse040_x264, Focuses on preparatory actions only; 'hitting' and 'elderly' are entirely avoided.` | 0.00 |
| PART1_0015 | `Yes. In Abuse041_x264, Crouching to clean is secondary; its link to a childcare scene requires inference.` | 0.00 |
| PART1_0018 | `Yes. In Abuse042_x264, Neglect has no obvious action marker and is easy to miss.` | 0.00 |
| PART1_0021 | `Yes. In Arrest043_x264, Requires identifying implied 'excessive force' rather than just 'police present'.` | 0.00 |
| PART1_0024 | `Yes. In Arrest044_x264, Entry and departure with person are separated in time; must be retrieved as one event.` | 0.00 |
| PART1_0034 | `Yes. In Arrest049_x264, Bystander has no actions; easily overlooked in action-based retrieval.` | 0.00 |
| PART1_0048 | `Yes. In Arson022_x264, Failed attempts produce no visible change; pattern of repeated failure before success is hard to retrieve.` | 0.00 |

**这些"事实"在视频画面里根本不存在**，RAGAS LLM 当然判不可归因。

定量切片（基于 50 case，简单正则匹配 evaluator-note 关键词，见 `agent/test/_recall_diag_extract.py`）：

| 切片 | n | avg context_recall |
|---|---|---|
| 含评测备注词的参考 | 35 | **0.333** |
| 不含评测备注词（"Minimal" 等仍算 clean） | 15 | **0.422** |

直接差异 0.09 absolute。这只是文本启发式的下界，真实污染影响更大（有些 case 的备注用了不会被正则触发的措辞）。

### 2.3 即使"clean" 的 case，参考答案结构也不利于 recall

clean ref 长这样：`"Yes. In Arrest050_x264 around 0:01:00 - 0:01:30, Minimal."` 或 `"No matching clip is expected."`。

RAGAS LLM 通常会拆成：
- `"Yes"` → 几乎总能挂上"context 提到了相关事件"。
- `"In Arrest050_x264 around 0:01:00 - 0:01:30"` → **要求 context 同时显式提到 video_id + 这段时间**。如果 chunk 文本里没有 `Arrest050_x264` 字样，LLM 就判 0。
- `"Minimal"` / 任何尾部备注 → 判 0。

→ 参考答案的"事实粒度"和"事实数量"被一个固定模板锁死，且模板里就硬塞了一个不可归因句。

---

## 3. 我们当前 pipeline 喂给 RAGAS 的"context"长什么样

### 3.1 入口：`ragas_eval_runner.py:594-599`

```python
rows = _select_final_rows(last_chunk)        # rerank_result 优先，否则 hybrid_result / sql_result
contexts = []
for row in rows[:top_k]:                     # top_k = rerank_top_k = 5
    text = _row_context_text(row)            # ← 关键
    if text and text not in contexts:
        contexts.append(text)
```

而 `_row_context_text`（line 120-127）只返回单字段：

```python
return str(
    row.get("event_summary_en")
    or row.get("event_text_en")
    or row.get("event_text_cn")
    or row.get("event_text")
    or ""
).strip()
```

**它丢弃了 row 上的 `video_id` / `track_id` / `start_time` / `end_time` / `scene_zone` / `keywords`**。

接着在 `_compact_contexts`（line 300-318）里再砍：默认 `--ragas-max-contexts=3`、`--ragas-max-context-chars=700`、`--ragas-max-total-context-chars=1800`。

### 3.2 实际效果（50 case 实测）

| 指标 | 数值 |
|---|---|
| 进入 RAGAS 的 context 总数 | 50 × 3 = 150 |
| 含 `Video <video_id>. Track <segment>.` 前缀 | **66 / 150 (44%)** |
| 仅含裸 `From Xs to Ys, ...` 事件句 | **84 / 150 (56%)** |
| Case 中**所有** 3 个 context 都缺 video_id 前缀 | **6 / 50 (12%)** |
| Reference 字符数 min/mean/max | 29 / 81.8 / 133 |

### 3.3 为什么 56% 的 context 缺前缀？

Chroma 里 child / event 两种 record 都有完整的结构化文档（`agent/db/chroma_builder.py:260-283, 441-473`）。但 retrieval 落到 `rows` 里时，不同 path 会把不同的字段叫做 `event_summary_en`：

- **child 级 hit**：normalize 后 `event_summary_en` 接近完整 chunk doc（带 `Video … Track …` 前缀）。
- **event 级 / SQL hit**：`normalize_hybrid_rows` / `normalize_sql_rows`（`agent/node/retrieval_contracts.py:146-168, 123-143`）给的 `event_summary_en` 优先用 `event_text` / `event_text_en`，那是单句裸事件文本。
- **mixed pool（rerank 后）**：top-K 里 child + event + SQL 三种 row 混合 → 一半是裸事件句。

→ RAGAS 看到的 context 列表里，约一半 chunk 完全没有 `Abuse037_x264` 字样，参考答案里的 `In Abuse037_x264` 这条事实直接归因失败。

### 3.4 案例对照（`reference vs retrieved_contexts_for_ragas`）

#### PART1_0008（recall=0.00, top_hit=True, ctx_chars=290）

```
Q  : Is there a video of two staff members conducting a full-body search on a detained woman in a closed room?
REF: Yes. In Abuse039_x264 around 0:03:03 - 0:04:40, Minimal.
CTX:
  [0] From 19.5s to 26.3s, the man in black standing at the door walked into the room...
  [1] From 87.6s to 96.5s, a bald man in black came and walked next to the two men in the room.
  [2] From 16.9s to 20.2s, the woman in pink clothes walked to the other side of the room.
```

失败模式叠加：(a) 3 个 chunk 全部缺 `Abuse039_x264` 前缀；(b) 真实正确时段在 183-280s，retrieval 给的全在 16-96s；(c) `Minimal` 是评测备注。**即使 chunks 里 `video_id` 写出来，RAGAS 仍会因为时间错位扣分。**

#### PART1_0034（recall=0.00, top_hit=True, precision=1.00）

```
Q  : A blonde woman stood watching the entire time without taking part in any physical action.
REF: Yes. In Arrest049_x264, Bystander has no actions; easily overlooked in action-based retrieval.
CTX:
  [0] Video Arrest049_x264. Track segment_15. ... The blond woman came over to talk to a man in police uniform.
  [1] Video Arrest049_x264. Track segment_9.  ... A blond woman came and stood beside him.
  [2] Video Abuse039_x264. Track segment_3.  ... The yellow-haired woman walked to the black-haired woman...
```

完全相反的 case：chunks 几乎完美命中（"blond woman… stood beside"），video_id 也写出来了，**但 reference 里 "Bystander has no actions; easily overlooked in action-based retrieval" 不可归因 → 整体 recall 仍然 0**。precision=1.0 与 recall=0.0 共存就是这种 case 的指纹。

#### PART1_0035（recall=0.00, top_hit=True, precision=1.00）

```
Q  : Is there a video of a police car chasing a sedan that eventually crashed into a roadside building?
REF: Yes. In Arrest050_x264, Minimal.
CTX:
  [0] From 68.1s to 70.8s, a black car hit a building on the side of the road and stopped.
  [1] From 133.6s to 206.5s, three cars were parked on the roadside, two white and one black...
  [2] From 38.0s to 45.4s, the car on the roadside got off the front row...
```

(a) 3 个 chunk 全是裸事件句无 `Arrest050_x264` → `In Arrest050_x264` 归因失败；(b) chunks 描述了"撞建筑"和"路边警车"，但没"chase"动作 → 参考里的 yes 主体勉强通过，但 video_id 句和 `Minimal` 全输 → 0/3 ≈ 0.

#### PART1_0003（recall=0.00, top_hit=True，时段对齐略偏）

```
Q  : A vehicle injured an animal on the road, and other animals approached the injured one afterward.
REF: Yes. In Abuse037_x264 around 0:00:30 - 0:00:43, Must link 'other dogs approaching' to the main collision event.
CTX:
  [0] Video Abuse038_x264. Track segment_1. Time range 0.3s to 10.4s. (错的视频)
  [1] Video Arrest050_x264. Track segment_4. Time range 68.1s to 70.8s. (错的视频)
  [2] Video Abuse037_x264. Track segment_2. Time range 8.4s to 25.3s. (对的视频, 时段不重叠 30-43)
```

真实正确 chunk 是同视频 segment_3 (25.3-48.5s, 提到"black dog… walked to the middle of the road next to the dog that had just been crushed")，**它进了 candidate pool 但没进 top-3**。属于"reranker 没把对的 chunk 推上来"。同时 `Must link 'other dogs approaching' to the main collision event` 又是评测备注。两层失败叠加。

#### PART1_0018（recall=0.00, top_hit=True，参考是"无动作"反而被 chunks 反证）

```
Q  : A baby lay alone on the floor for a long time while the caregiver was away.
REF: Yes. In Abuse042_x264, Neglect has no obvious action marker and is easy to miss.
CTX:
  [0] From 390.5s to 409.5s, the woman patted the baby's back with one hand and began to caress the baby. (反例)
  [1] From 66.7s to 79.0s, the three people next to the blue car lay on the ground.                       (无关)
  [2] Video Abuse042_x264. Track segment_23. ... The woman patted the baby's back...                       (反例)
```

这是"negative behavior"问句的典型坑：question 问的是"无动作（neglect）"，但 chroma 里没有"什么也没发生"的事件 chunk，retrieval 只能召回带动作的 chunk，反而和 question 语义相反。属于真实的检索局限（chunk 设计不覆盖 negative space）。

#### PART1_0024（recall=0.00, top_hit=True, precision=0.83，多事实分散）

```
Q  : Several uniformed officers entered a house and shortly after brought a person down from upstairs and left.
REF: Yes. In Arrest044_x264, Entry and departure with person are separated in time; must be retrieved as one event.
CTX:
  [0] Video Arrest044_x264. Track segment_7. (80.3-97.7s) Two men in police uniforms and a man in a black coat came down from upstairs and left the room.
  [1] Video Arrest049_x264. Track segment_16. (293.7-301.3s) A woman in police uniform... (干扰视频)
  [2] Video Arrest044_x264. Track segment_5. (42.2-54.7s) Three people in police uniforms ascended to the second floor one after another.
```

CTX[0]+[2] 实际上完美覆盖了 question 的"上楼+下楼带人"两段，但 reference 那一句 `Entry and departure with person are separated in time; must be retrieved as one event` 是评测说明，归因失败。

### 3.5 失败模式归类

| 模式 | 典型 case | 估计占比（50 case）| 是 retrieval 锅？ |
|---|---|---|---|
| **F1. 评测备注污染参考** | 0008, 0012, 0013, 0015, 0018, 0021, 0024, 0034, 0048 | ~30/50（60%）有可见污染句 | ❌ 评测/数据集制作 |
| **F2. context 缺 video_id 前缀** | 0008, 0035, 0036 等（6/50 全裸；84/150 chunk 部分裸） | 直接拉低参考里 `In <video>` 句的归因 | ❌ Eval runner 接口 |
| **F3. RAGAS-max-contexts=3 截掉** | 多事实 case 如 0024, 0010 | 系统性 | ❌ Eval runner 配置 |
| **F4. 长视频中段被 retrieval 错过** | 0008（reference 0:03:03-0:04:40, retrieval 全在 0:00:16-0:01:36） | 3-5/50 | ✅ 真 retrieval |
| **F5. Reranker 把对的 chunk 排出 top-K** | 0003（同视频 segment_3 在 candidate 里但被 segment_2 抢位） | 3-5/50 | ✅ 真 retrieval |
| **F6. Negative-behavior 问句无对应 chunk** | 0018（neglect）, 0034（不参与） | 3-5/50 | ⚠️ 数据/chunk 设计 |
| **F7. top_hit=False（视频都搞错了）** | 0031, 0032, 0043 | 3/50 | ✅ 真 retrieval |

> F1+F2+F3 是评测/接口问题，影响约 **35-40 个 case**，不动 retrieval 也能修。
> F4+F5+F7 是真 retrieval 问题，影响约 **8-10 个 case**。
> F6 是 chunk-coverage 问题（"什么都没发生"事件没 chunk），影响 ~5 个 case。

---

## 4. 横向对比四份 50-case eval

由 `agent/test/_recall_diag_extract.py` 风格脚本聚合：

| run | recall | precision | faithfulness | factual | top_hit |
|---|---|---|---|---|---|
| `fts5_bm25` (P0+P1-1/-2 baseline) | 0.360 | 0.585 | 0.690 | 0.480 | 0.94 |
| `no_verifier` sanity | **0.383** | 0.585 | 0.704 | 0.620 | 0.94 |
| `p1_next_a` baseline (verifier bail-out 修好后) | 0.360 | 0.583 | 0.712 | 0.600 | 0.94 |
| `p1_7_v23` reselect (grounder OFF) | **0.297** | 0.593 | 0.713 | 0.580 | 0.94 |

**关键观察**：

- `no_verifier` 反而 recall 最高（0.383）。verifier 一旦工作就会 trim 掉一些 chunk，把 chunk 池里"和 question 弱相关但和 reference 重叠"的 chunk 挤出去。
- `p1_7_v23` 最低（0.297）。v2.3 reselect 让 verifier 在多 chunk 候选里重选 single best span，这与 RAGAS 喂多 chunk 后期望"能多覆盖参考事实"的目标矛盾。**v2.3 优化的是 task-native 时段对齐（localization），它对 recall 是负优化。**
- precision 在 0.585~0.593 几乎不动 → retrieval 的"挑中视频"能力没变化，变化都在 chunk 取舍上。
- top_hit 0.94 全程不变 → top-1 video 选对的能力很稳，瓶颈在"选哪些 chunk 喂 RAGAS"和"参考答案怎么写"。

**推论**：四次 eval 的 recall 抖动 ±0.04 主要来自 verifier / reselect 对 top-K chunk 的扰动，**底层 retrieval 没动过的事实，让我们看到 recall 上限被参考答案+context 形态封死在 0.36 ± 0.04 区间**。

---

## 5. 真 retrieval 哪一环节才是元凶？

按问题列表逐项判定：

### Q1. retrieval 召回数量不够（top-K 太小）？

- 当前 `candidate_limit=80, hybrid_limit=50, sql_limit=80, rerank_candidate_limit=20, rerank_top_k=5`（`agent/node/retrieval_contracts.py:9-19`）。
- 候选池 50-80 已经覆盖了大部分场景（per-video chunk 中位数 6，min=1, max=486 见 `agent/data_audit_2026_05_02.md`）。
- 真实瓶颈**不是召回数量**，而是 RAGAS 端只看 3 chunk + reranker 把对的挤出 top-5。

### Q2. reranker 把含 query-fact 的 chunks 排到 top-K 之外？

- 当前 reranker = `cross-encoder/ms-marco-MiniLM-L-6-v2`（`agent/tools/rerank.py:17`），22M 参数英文 cross-encoder，MS-MARCO 域。
- 对短 query + 长描述 chunk 排序还行，但 (a) 我们的 chunk 文本里夹了大量结构化 metadata（"Subject: white car. Located in: road. Keywords: white, car, double…"），噪声很重；(b) reranker 看到 chunk 时**也没拿到 query-side metadata 强化**。
- PART1_0003 是典型：candidate pool 里有 `segment_3 (25.3-48.5s)` 描述 "black dog left on the road, walked to the middle next to the dog that had just been crushed"，正好是 reference 想要的"其他狗靠近"，但被 reranker 排到了第 4-5 位之外。
- → reranker 是个 **真实可改但收益中等**的瓶颈。

### Q3. child-level chunk 文本本身缺 reference 期望的关键词？

- 检查样例 chunk：
  ```
  Video Abuse037_x264. Track segment_3. Time range 25.3s to 48.5s. Appearance notes: High activity; There was a black dog left on the road. It walked to the middle of the road next to the dog that had just been crushed. Located in: road. Events: From 25.3s to 48.5s, ... Keywords: black, dog, left, road, walked, middle.
  ```
- chunk 文本本身**信息密度足够**，对应的 reference fact "其他狗靠近被压的狗" 是能在文本里找到原话的。
- 缺失主要发生在**长视频的中段**（PART1_0008 expected 0:03:03-0:04:40，对应 segment 应在 ~segment_15-25 区间，retrieval 没召回到）。
- → **chunk 内容质量不是核心问题**；问题是"对的 chunk 没进 top-K"。

### Q4. Chinese reference 含 scene 描述但 chunks 是英文？

- 实测 50 个 case 全是英文 question + 英文 reference + 英文 chunk（`question_language=en`，dataset 是 Part1 sheet）。
- 跨语言不是当前 50-case 的问题。如果未来上 Chinese 子集或 Part2-4，需要单独验证。

### Q5. Reference 的 fact 散落在多个 chunks 但 top-K 只取了 1？

- 这是 v2.3 reselect 的副作用（PART1_0024 "上楼+下楼" 分别在 segment_5 和 segment_7，需要两个 chunk 同时进 top-3 才能覆盖完）。
- **`--ragas-max-contexts=3` 直接限死了多 fact 答案能拿到的 chunk 数。**
- 修复优先级高，工作量低。

### Q6. retrieval 的 `event_summary_en` 字段失血

- 在 `_row_context_text`（`agent/test/ragas_eval_runner.py:120-127`）里只取一个字段，丢掉了 row 上的 `video_id` / `track_id` / `start_time` / `end_time`。
- 这是 **一个 5 行函数级别的接口 bug**，直接导致 56% chunk 缺 video_id 前缀。
- 修复成本极低，收益巨大。

---

## 6. 改造候选清单（按 ROI 排序）

> 兼容性栏：✅ 完全兼容 P1-7 v2.3 / P1-Next-A / P1-Next-C；⚠️ 需要轻微 hand-off；❌ 与已有改造冲突。

### R1. 修 `_row_context_text`，给 RAGAS 看到的 context 强制带上 video_id + 时段头 ⭐⭐⭐⭐⭐ (先做)

- **文件**：`agent/test/ragas_eval_runner.py:120-127`（仅 evaluator 端，**不动产品代码**）
- **改动思路**：把 `_row_context_text(row)` 改成
  ```
  f"Video {row['video_id']}. Time {row['start_time']:.1f}s-{row['end_time']:.1f}s. "
  f"{row.get('event_summary_en') or row.get('event_text_en') or row.get('event_text') or ''}"
  ```
  保证每条 context 开头一定写出 `video_id` 和时间窗口，让 RAGAS LLM 可以归因 `In <video> around <time>` 这条事实。
- **预期收益**：消灭 F2 失败模式，影响 ~30/50 case 的 recall 单句归因。粗估 +0.10 ~ +0.15 absolute recall。
- **工作量**：< 30 分钟。
- **兼容性**：✅ 纯 evaluator 端，不影响 retrieval / verifier / summary。

### R2. 修 `_build_reference_answer_rich`，把 evaluator note 从参考答案里剥离 ⭐⭐⭐⭐⭐ (先做)

- **文件**：`agent/test/agent_test_importer.py:509-538`
- **改动思路**：`scene_description` 不再无条件拼到 reference 尾部。两种可选实现：
  - (a) 默认走 clean ref：`f"Yes. In {video_id} around {time}."` + `"No matching clip is expected."`，把 `recall_challenge` 单独放进 metadata 字段供分析使用。
  - (b) 给 `recall_challenge` 加一层 sanitize（如果含 keywords like "must", "easy to", "minimal", "overlook" 等就丢弃）。
  - 推荐 (a)，因为 recall_challenge 本来就不是答案。
- **预期收益**：消灭 F1 失败模式，~30/50 case 受益。粗估 +0.05 ~ +0.10 absolute recall。
- **工作量**：< 1 小时（含重新生成 dataset）。
- **兼容性**：✅ 不影响产品 path；只影响 dataset rebuild 出来的 `reference_answer_rich`。需要重跑 importer，不需要重跑 retrieval。

> ⚠️ todo.md 里写过的 `challenge.md §5.1: default-on rich reference` 这条假设——"rich reference 比 pointer reference 信息量更高所以 RAGAS 更准"——**事实错误**。rich reference 多出来的信息恰恰是评测备注，反而把 recall 拉低了。建议把 `--ragas-no-rich-reference` 改成默认或单独 ablation 验证一次。

### R3. 把 `--ragas-max-contexts` 默认从 3 提到 5（与 `rerank_top_k=5` 对齐）⭐⭐⭐⭐ (先做)

- **文件**：`agent/test/ragas_eval_runner.py:822`
- **改动思路**：`default=3` → `default=5`；同步把 `--ragas-max-total-context-chars` 从 1800 提到 ~3000 以避免被 `_compact_contexts` 截断（line 314 一旦 projected > total 就 break）。
- **预期收益**：让多 fact 答案有机会被多 chunk 同时支撑，主要救 F4（reference fact 分散）。粗估 +0.03 ~ +0.05 absolute recall。
- **工作量**：< 5 分钟。
- **兼容性**：✅ 完全兼容；唯一代价是 RAGAS 调用 token 略增。

### R4. 把 reranker 升级 / 切换到带元数据感知的模型 ⭐⭐⭐ (二阶段)

- **文件**：`agent/tools/rerank.py:17, 20-33`
- **改动思路**：
  - (a) 换成 `BAAI/bge-reranker-v2-m3` 或 `BAAI/bge-reranker-large`（多语，对 metadata-rich 文本表现更好）；
  - (b) 或在 `_build_pair_text` 里把 metadata 段（`type`, `color`, `zone`）放到 query 侧而不是 doc 侧（cross-encoder 对 query 侧 token 更敏感）；
  - (c) 或把 `keywords` 段从 doc 文本里剥掉，避免 reranker 被关键词列表干扰。
- **预期收益**：救 F5（PART1_0003 类）。粗估 +0.02 ~ +0.05 absolute recall + 显著 localization 改善。
- **工作量**：(a) 1-2 天（新模型下载、显存评估、A/B）；(b)(c) 半天。
- **兼容性**：⚠️ 与 P1-7 v2.3 verifier 链路无冲突，但 verifier reselect 的"top-K candidate"质量会变，需要重跑 P1-7 验证。

### R5. 长视频按时间窗 hard split chunking（彻底解决长视频中段被错过）⭐⭐⭐ (二阶段)

- **文件**：`agent/db/chroma_builder.py:208-257, 356-438`
- **改动思路**：当前 child 按 `(video_id, entity_hint)` 聚合，在 UCFCrime 上 = event 等价（见 `agent/data_audit_2026_05_02.md`）。新增一种或替换一种 chunk 策略：按 30s 滑动窗口聚合多 events 成一个 child，让 chunk 在长视频上分布更均匀；同时保留 event-level 用于精细召回。
- **预期收益**：救 F4（PART1_0008 类，183-280s 中段被 16-96s 早段挤掉）。粗估 +0.05 absolute recall + localization_score 显著提升。
- **工作量**：中-大（改 builder + 重建索引 + 验证 retrieval 分数没崩）。
- **兼容性**：⚠️ 需要重建 Chroma 索引；旧的 `--ragas-eval` baseline 数据要标注。与 P1-7 v2.3 verifier 兼容（verifier 输入是 row list，不依赖 chunk 粒度）。
- **依赖**：建议先做 R1+R2+R3，把评测噪声降下来再来量化 R5 的收益。

### R6. Query 改写 / expansion（处理 negative behavior 与抽象描述）⭐⭐ (二阶段)

- **文件**：新增 `agent/node/query_rewriter_node.py` 或扩展 `self_query_node`
- **改动思路**：用 LLM 先把抽象 question（如 "neglect"、"bystander"、"excessive force"）改写成一组具体的可观察 chunk 关键词（"baby alone"、"no movement"、"watching"、"officer hits person on ground"），再 union 检索。
- **预期收益**：救 F6（negative-behavior / 抽象描述 case）。粗估 +0.02 ~ +0.04 absolute recall，且对 top_hit 也有正面贡献。
- **工作量**：中（新节点 + prompt 调试 + 与 self_query 的 fusion 逻辑）。
- **兼容性**：✅ 在现有 LangGraph 链路前面加一层节点即可，下游不变。

### R7. Hybrid alpha 调参 + dense vs sparse 权重 A/B ⭐⭐ (低投入实验)

- **文件**：`agent/node/retrieval_contracts.py:15-17`（`hybrid_alpha=0.7`, `hybrid_fallback_alpha=0.9`）
- **改动思路**：跑 0.5 / 0.7 / 0.9 三档 alpha 的 50-case 对比；同时尝试关闭 BM25 / 仅 dense 的 ablation。
- **预期收益**：可能 +0.01 ~ +0.03 absolute recall，但不确定。
- **工作量**：低（参数 sweep）。
- **兼容性**：✅ 完全兼容。

### R8. 给 RAGAS 切换到 `NonLLMContextRecall` 或 `IDBasedContextRecall` 做交叉验证 ⭐ (诊断辅助)

- **文件**：`agent/test/ragas_eval_runner.py:521-532`
- **改动思路**：额外跑一遍 `IDBasedContextRecall`（需要给 dataset 标 `reference_context_ids = [video_id]` 或 event_id），对比 LLM-based 与 ID-based 两种 recall 的相对趋势。
- **预期收益**：本身不提升数字，但能**确认上面 R1~R3 是否真的修对了"评测噪声"** — 如果 ID-based recall 一直高（如 0.94 与 top_hit 一致），LLM-based recall 提升后两者 gap 才有意义。
- **工作量**：低-中（dataset 加字段 + 新 metric 调用）。
- **兼容性**：✅ 完全独立。

---

## 7. 推荐"先做"

**做 R1 + R2 + R3 一起，作为一个 evaluator-only 的 PR**，理由：

1. **三个改动加起来 < 1 天工作量**，只动 evaluator 和 importer，**不动 retrieval / verifier / summary 任何一行代码**。
2. **预期 recall 从 ~0.36 提升到 0.55 ~ 0.65**（R1 +0.10~0.15、R2 +0.05~0.10、R3 +0.03~0.05；存在重叠所以总和折算）。
3. **修完之后 retrieval 真实瓶颈才会浮出水面**：现在所有 retrieval / verifier / chunk strategy 改动的"有没有用"都被评测噪声盖死（四次 eval recall 抖动 ±0.04 都在噪声里），R1+R2+R3 是把"信号 / 噪声比"拉起来的前置投资。
4. **不会回退任何已有功能**：P1-7 v2.3 verifier reselect、P1-Next-A bail-out fix、P1-Next-C 都是产品 path 改动，与 evaluator 改动正交。
5. **顺带可以验证 P1-7 v2.3 的真实价值**：当前看 v2.3 比 P1-Next-A recall 退步 0.06，但实际可能 v2.3 的 chunk 集中策略对 localization 有正面贡献而对 RAGAS 评测算法负面 — 用 clean reference + 5 chunks 后再测才能下结论。

第二步建议按 R5（长视频 chunking）→ R4（reranker 升级）→ R6（query rewrite）→ R7 顺序，每步独立 A/B 验证，避免互相掩盖。

---

## 8. 附：本次诊断用到的字段与代码位置（便于复核）

| 用途 | 位置 |
|---|---|
| RAGAS context_recall 算法 | `~/anaconda3/lib/python3.13/site-packages/ragas/metrics/_context_recall.py:88-156` |
| Reference 构造 | `agent/test/agent_test_importer.py:509-538`（`_build_reference_answer_rich`）|
| Context 抽取（去结构化） | `agent/test/ragas_eval_runner.py:120-127`（`_row_context_text`）|
| Context 截断 / max_contexts=3 | `agent/test/ragas_eval_runner.py:300-318, 822-824` |
| Reference 选 rich 还是 pointer | `agent/test/ragas_eval_runner.py:830-842, 919-927` |
| Retrieval 配置 | `agent/node/retrieval_contracts.py:9-19` |
| Reranker 模型 | `agent/tools/rerank.py:17, 59-100` |
| Child / event document 模板 | `agent/db/chroma_builder.py:260-283, 441-473` |
| 数据架构事实 | `agent/data_audit_2026_05_02.md` |
| 本次抽样方法 | 直接读 `agent/test/generated/ragas_eval_e2e_n50_p1_next_a_v1/e2e_report.json`，按 `cases[].ragas.retrieval.context_recall` 分桶（recall=0 / <0.5 / =0.5 / <1 / =1）后按 case_id 抽 15 例对照 `reference_answer_rich` 与 `retrieved_contexts_for_ragas` 的差异；定量切片用简单正则（"minimal/easily/easy to/must link/overlooked/hard to/keywords directly match…"）做 evaluator-note 检测。|

---

**调研完成时间**：2026-05-02
**调研者**：cursor agent
**输入数据**：`ragas_eval_e2e_n50_p1_next_a_v1` (主) + `_fts5_bm25_v1` / `_no_verifier_v1` / `_p1_7_v23_v1`（横向对比）
**输出**：本文档
