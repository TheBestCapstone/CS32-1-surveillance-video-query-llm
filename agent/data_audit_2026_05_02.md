# Data Audit 2026-05-02：父子索引结构有效性验证

> 触发原因：P1-7 v2.2-Plus 调研期间发现 UCFCrime eval 子库的 `child` 与 `event` collection 数量完全相等（235 / 235），怀疑父子索引结构设计未真正发挥作用。本报告基于全数据集 audit 给出结论与建议。

## 1. 调研方法

- 抽样：UCFCrime 全 310 videos / 4331 events 的 `*_events_vector_flat.json`；Basketball 全 2 videos / 269 events 的 `*_events.json`
- 统计：events per video 分布、events per (video_id, entity_hint) 分布、entity_hint 取值与命名模式
- 代码 review：`agent/db/chroma_builder.py:208-257` `_build_child_records()`、`agent/db/chroma_builder.py:356+` `_build_event_records()`

## 2. 核心数据

### UCFCrime（310 videos）

| 指标 | 数值 |
|---|---|
| 总 events | **4331** |
| Events / video | min=1, max=486, mean=14.0, median=6 |
| Events / (video, entity_hint) | **min=1, max=1, mean=1.00, median=1** |
| 含 ≥2 events 的 track 数 | **0 / 4331 (0.00%)** |
| Unique entity_hint 总数 | 486（segment_1 ~ segment_486 顺序编号）|

#### entity_hint 命名样本

```
['segment_1', 'segment_10', 'segment_100', 'segment_101', 'segment_102',
 'segment_103', 'segment_104', 'segment_105', 'segment_106', 'segment_107']
```

→ entity_hint 在 source data 里是 **event 顺序编号**，不是真正的 entity（人 / 物 track ID）。

#### 验证：Abuse040_x264 真实 events

7 个 events 各自独占一个 entity_hint：

| entity_hint | start | end | event_text 摘要 |
|---|---|---|---|
| segment_1 | 9.2 | 23.4 | 进屋关灯 |
| segment_2 | 26.6 | 40.3 | 推轮椅 |
| segment_3 | 40.3 | 44.4 | 打头 |
| segment_4 | 46.4 | 58.7 | 打头 + 推 |
| segment_5 | 58.7 | 69.1 | 打白发女人 |
| segment_6 | 70.1 | 85.8 | 推轮椅 |
| segment_7 | 84.8 | 103.3 | 掴白发女人 |

→ chroma_builder 按 `(video_id, entity_hint)` 分组时每组就 1 个 event。

### Basketball（2 videos）

| 文件 | events | tracks | events/track | 分布 |
|---|---|---|---|---|
| basketball_1 | 81 | 80 | mean=1.01 | `{1: 79, 2: 1}` |
| basketball_2 | 188 | 149 | mean=1.26 | `{1: 127, 2: 14, 3: 2, 4: 3, 5: 3}` |

→ basketball_1 几乎全 1:1，basketball_2 有少量真实聚合（22/149 ≈ 15% tracks 含多 events）。

## 3. 根因分析

`agent/db/chroma_builder.py:208-212`：

```python
def _build_child_records(self, events):
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for event in events:
        key = (event["video_id"], event["entity_hint"])
        grouped.setdefault(key, []).append(event)
```

**逻辑无误**，但依赖 `entity_hint` 是真正的 entity 标识（多个 events 共享同一 entity_hint → 聚合成一个 child）。然而：

- **UCFCrime**：source data 的 `entity_hint` 是 `segment_<event_index>` 顺序编号，每 event 一个独立 hint → **child level 完全失效**
- **Basketball**：`entity_hint` 是数字（1, 2, 3, ...），可能源于实际的 entity tracking，所以有少量聚合（15%）

## 4. 三层架构在 UCFCrime 上实际只有两层

| 设计意图 | UCFCrime 实际 |
|---|---|
| `parent` (video 级) | 17 videos ✅ 生效 |
| `child` ((video, entity) 聚合) | 4331 records ❌ 等价于 event |
| `event` (单事件) | 4331 records ✅ 生效（与 child 100% 重合）|

→ event collection 不带来"细粒度"优势（在 UCFCrime 上），但也不带来损失（占 235 records ≈ 几 MB）。

## 5. 决策矩阵（基于本次发现）

| 选项 | 描述 | 收益 | 工作量 | 推荐度 |
|---|---|---|---|---|
| **A. 不动数据，承认现状** | 接受 ucfcrime 上 child=event；P1-7 v2.2-Plus 仍按原方案做（让 verifier 拉 same-video top-K event chunks） | P1-7 仍有效，PART1_0011 案例能修；零数据迁移成本 | 0 | ⭐ **推荐** |
| B. 删 event collection | 既然 ucfcrime 上 child=event，为何要建两份？只保留 child，节省 build 时间 + 存储 | 简化架构 (-1 collection)，build 时间略减 | 中（改 chroma_builder + 重建库 + 改 retrieval level 配置）| 不推荐：basketball 上 event 仍有 15% 增益，跨数据集要兼容 |
| C. 重做 source data 的 entity_hint | 用真正的 entity track（人物 ID / 物体 ID）替代 segment_N，让 child 真正按 entity 聚合 | child level 真正发挥作用，每个 child 含 2-5 events，secondary fetch 收益更大 | **大**（改 ucfcrime_transcript_importer.py 和 source 生成流程，全量重建库）| 长期方向，但不阻塞 P1-7 |
| D. 重新设计 chunk 切分（按时间窗）| 不用 entity_hint 做 child 维度，改按时间窗（如每 30s）聚合多 events | 父子关系真实存在；不依赖 source data 的 entity_hint 质量 | 大（改 chroma_builder + 重建库）| 长期备选 |

## 6. 推荐：A + 文档化

### 6.1 立刻执行
1. **不修改 chunk 架构**：保留三层 collection（parent/child/event），承认 ucfcrime 上 child=event
2. **P1-7 v2.2-Plus 按原方案启动**：核心价值是"让 verifier 看 same-video 的 top-K candidates"，而不是"event 比 child 细"
3. **secondary fetch 时用 event collection**（在 ucfcrime 上等价于 child，但保留对 basketball 等数据集的灵活性）

### 6.2 文档化
- 在 `agent/architecture.md` 加一节"chunk granularity by dataset"，说明：
  - basketball 数据集：child 真正聚合 ~15% tracks 含多 events
  - ucfcrime 数据集：child=event 100% 等价，因为 source data 的 entity_hint 是 event 顺序编号
- 在 `agent/db/README.md` 提示 source data 制作者：如果想 child 真正聚合，`entity_hint` 应当是 entity track ID 而非 event 顺序

### 6.3 长期跟进（独立 todo，不阻塞 P1-7）
- **新增 P3-4（暂定）**：重新设计 source data 生成流程，让 ucfcrime 的 entity_hint 真正反映 entity 而非 event 索引；或改 chunk 切分策略改用时间窗

## 7. 对 P1-7 v2.2-Plus 的具体指导

### 7.1 不变的部分
- 改造文件、prompt、env flag 设计完全照原方案
- single-shot LLM 在 multi-chunk 候选里挑 best span 的逻辑不变

### 7.2 调整的部分
- secondary fetch 的"价值表述"调整：
  - 原表述："让 verifier 看 event 级（更细）的 chunks"
  - 实际表述："让 verifier 看 same-video 的 top-K candidates，不再只看 retrieval top-1"
- top_k 默认值从 5 提到 **8**（在 ucfcrime 上 events/video 中位数 6，提到 8 能基本覆盖整个视频的关键事件）

### 7.3 验收标准（更新）
| 指标 | before | after |
|---|---|---|
| PART1_0011 重选 span | 0:00:46-0:00:59（segment_2 推轮椅）| 0:00:58-0:01:09（segment_5 打白发女人头）|
| PART1_0020 重选 span | 0:01:38-0:02:00（yellow hat 揍人）| 期望选含 "police officer" 的 chunk（如有）|
| 5 个 verifier=mismatch case 中 ≥3 个变 exact/partial | 0/5 | ≥3/5 |
| localization_score_avg | 0.228 | ≥ 0.40 |
| top_hit_rate | 0.94 | 0.94（不变）|
| 50-case eval 时间 | 23min | ≤ 30min（多 ~7min event fetch + LLM）|

## 8. 结论

- ✅ 父子索引结构在代码层面**无 bug**，逻辑正确
- ⚠️ UCFCrime source data 的 `entity_hint` 字段语义错位，导致 child level 在 ucfcrime 上**实际等价于 event level**
- ✅ Basketball 上 child 仍有 15% 真实聚合，跨数据集架构仍合理
- ✅ **P1-7 v2.2-Plus 不受影响**，按原方案执行；价值核心是"verifier 多 chunk 候选"而非"event 比 child 细"
- 📋 长期可考虑重做 ucfcrime source data 的 entity_hint 生成（独立 todo P3-4）

---

**调研完成时间**：2026-05-02
**调研者**：cursor agent
**输出**：本文档；`agent/todo.md` 中 P1-Next-D 标 DONE；建议下一步直接启动 P1-Next-C + P1-7 v2.2-Plus
