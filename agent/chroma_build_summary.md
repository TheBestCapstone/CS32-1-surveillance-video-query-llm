# Chroma 建立总结

## 目的
- 为监控视频混合检索提供语义向量召回层
- 与 SQL 检索形成互补：
- SQL 负责结构化精确过滤
- Chroma 负责自然语言语义召回

## 当前建库对象
- Chroma 路径：`/home/yangxp/Capstone/data/chroma/basketball_tracks`
- Collection：`basketball_tracks`
- 输入数据：
- `/home/yangxp/Capstone/data/basketball_output/basketball_1_events_vector_flat.json`
- `/home/yangxp/Capstone/data/basketball_output/basketball_2_events_vector_flat.json`

## Embedding 配置
- 模型：`text-embedding-v3`
- 维度：`1024`
- 相似度：`cosine`

## 文本与元数据设计
- document（向量化文本）：
```text
{appearance_notes} Located in {scene_zone}. {event_text}
```
- metadata（用于过滤）：
- `video_id`
- `object_type`
- `object_color`
- `keywords`（英文逗号拼接字符串）
- `entity_hint`
- `start_time`
- `end_time`
- `scene_zone`

## 切片方式（重点）
- 当前采用：`track-level` 聚合切片
- 规则：按 `{video_id}_{entity_hint}` 聚合成一条 Chroma 记录
- 不是 `event-level`（一条事件一条记录）

### 切片示例 1（单事件轨迹）
- 源事件：
- `video_id=basketball_1.mp4`
- `entity_hint=track_1`
- 只有 1 条事件
- 聚合后：
- 生成 1 条记录，id=`basketball_1.mp4_track_1`

### 切片示例 2（多事件同轨迹）
- 源事件：
- `video_id=basketball_2.mp4`
- `entity_hint=track_id_2`
- 对应 2 条连续运动事件（例如 `40.6s->44.9s` 与 `46.9s->51.0s`）
- 聚合后：
- 仍生成 1 条记录，id=`basketball_2.mp4_track_id_2`
- 时间范围合并为该轨迹覆盖区间（最小 start 到最大 end）

## 当前结果解读
- 原始事件数：`27`
- Chroma 记录数：`26`
- 差异原因：有轨迹发生了多事件合并（track-level 切片导致）

## 检索策略测试结论
- `cosine`：语义检索稳定，尤其对模糊描述有效
- `BM25`：英文文本下有效；中文 query 在当前英文文档语料下效果弱
- `cosine + BM25`：适合作为融合策略（英文场景收益更明显）

## 建议
- 若后续查询主要是中文，可增加中文描述字段并参与向量化文本拼接
- 保持 track-level 用于轨迹检索；若要更细粒度时序定位，可增加 event-level 并行 collection

## 切换为 Event-level 切片（改造说明）
- **当前采用：`track-level` 切片**（本项目现状）
- `track-level` 特点：同一 `video_id + entity_hint` 的多条事件会聚合成一条记录
- `event-level` 特点：每条事件单独入库，时间定位更细，但记录数量更大

### 什么时候用 Track-level
- 目标是“找这个目标轨迹整体在做什么”
- 更关心目标级别召回，不追求每个时间片精确区分
- 数据量需要可控，优先减少 Chroma 记录数

### 什么时候用 Event-level
- 目标是“找某个时间段内的具体动作事件”
- 需要精确回到事件粒度（start_time/end_time）
- 后续要做事件级重排、事件级高亮、事件级回放

### 从 Track-level 切到 Event-level 的改造点
1. `record id` 规则改造  
- 由：`{video_id}_{entity_hint}`  
- 改为：`{video_id}_{entity_hint}_{start_time}_{end_time}`  
- 目的：避免同轨迹不同事件被覆盖

2. 切片逻辑改造  
- 由：按 `video_id + entity_hint` 聚合后再写入  
- 改为：每条 event 直接写入一条 Chroma record（不聚合）

3. metadata 保留事件时间边界  
- 必须保留：`start_time/end_time/scene_zone/object_type/object_color`  
- 推荐增加：`event_index`（同轨迹内序号）便于排序

4. 检索后融合策略调整  
- 现有 track-level 结果可直接作为“目标轨迹”返回  
- event-level 下建议新增一步：
- 同一 `video_id + entity_hint` 的近邻事件可选做窗口合并，减少碎片化展示

### 风险与收益
- 收益：时序定位更精确，能更好支持“某动作发生在何时”
- 风险：记录量上涨，索引构建与检索耗时增加，需关注 topK 和过滤条件
