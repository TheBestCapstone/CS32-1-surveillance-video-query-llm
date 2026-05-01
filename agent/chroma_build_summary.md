# Chroma 建立总结

## 目的
- 为监控视频混合检索提供语义向量召回层
- 与 SQL 检索形成互补：
- SQL 负责结构化精确过滤
- Chroma 负责自然语言语义召回

## 当前建库对象
- Chroma 路径：`/home/yangxp/Capstone/data/chroma/basketball_tracks`
- Child Collection：`basketball_tracks`
- Parent Collection：`basketball_tracks_parent`
- 输入数据：
- `/home/yangxp/Capstone/data/basketball_output/basketball_1_events_vector_flat.json`
- `/home/yangxp/Capstone/data/basketball_output/basketball_2_events_vector_flat.json`

## Embedding 配置
- 模型：`text-embedding-v3`
- 维度：`1024`
- 相似度：`cosine`

## 文本与元数据设计
- child document（向量化文本）：
```text
Video {video_id}. Track {entity_hint}. Time range {start_time}s to {end_time}s.
Appearance notes: {appearance_notes}
Located in: {scene_zone}
Events: {event_text}
Keywords: {keywords}
```
- child metadata（用于过滤与父子关联）：
- `video_id`
- `parent_id`
- `object_type`
- `object_color`
- `keywords`（英文逗号拼接字符串）
- `entity_hint`
- `start_time`
- `end_time`
- `scene_zone`

- parent document（视频级聚合文本）：
```text
Video {video_id}. Video time range {start_time}s to {end_time}s.
This parent record summarizes {child_count} child tracks.
Object types: {object_types}
Object colors: {object_colors}
Scene zones: {scene_zones}
Child track summaries: {child_documents}
```
- parent metadata：
- `video_id`
- `child_count`
- `start_time`
- `end_time`
- `scene_zones`
- `object_types`
- `object_colors`
- `child_ids_json`

## 切片方式（重点）
- 当前采用：`parent-child` 双层切片
- child 规则：按 `{video_id}_{entity_hint}` 聚合成一条 Chroma 记录
- parent 规则：按 `video_id` 聚合成一条 Chroma 记录
- child 保留当前 `track-level` 语义检索能力
- parent 提供 `video-level` 粗召回与后续层级路由入口

### child 切片示例
- 源事件：
- `video_id=basketball_2.mp4`
- `entity_hint=track_id_2`
- 对应 2 条连续运动事件（例如 `40.6s->44.9s` 与 `46.9s->51.0s`）
- child 聚合后：
- 生成 1 条 child 记录，id=`basketball_2.mp4_track_id_2`
- 时间范围合并为该轨迹覆盖区间（最小 start 到最大 end）

### parent 切片示例
- 同一 `video_id=basketball_2.mp4` 下的所有 child 记录
- parent 聚合后：
- 生成 1 条 parent 记录，id=`basketball_2.mp4`
- metadata 中保存 `child_ids_json`
- document 中拼接该视频下多个 child 的摘要信息

## 当前结果解读
- 原始事件数：`27`
- child 记录数：`26`
- parent 记录数：按 `video_id` 数量生成
- child 与原始事件数差异原因：同轨迹多事件被合并（track-level child 切片导致）

## 检索策略测试结论
- `cosine`：语义检索稳定，尤其对模糊描述有效
- `BM25`：英文文本下有效；中文 query 在当前英文文档语料下效果弱
- `cosine + BM25`：适合作为融合策略（英文场景收益更明显）

## 建议
- 若后续查询主要是中文，可增加中文描述字段并参与向量化文本拼接
- 保持 child track-level 用于轨迹检索
- 使用 parent video-level 作为粗召回入口
- 若要更细粒度时序定位，可在 child 之外继续增加 event-level 并行 collection

## 父子索引说明
- **当前采用：`parent-child` 双层索引**
- `child-level` 特点：同一 `video_id + entity_hint` 的多条事件会聚合成一条记录
- `parent-level` 特点：同一 `video_id` 下所有 child 汇总为一条视频级记录

### 什么时候优先用 Child-level
- 目标是“找这个目标轨迹整体在做什么”
- 更关心目标级别召回，不追求每个时间片精确区分
- 需要保留现有语义检索质量与 metadata filter 能力

### 什么时候优先用 Parent-level
- 目标是“先定位哪个视频更相关，再下钻到具体轨迹”
- 需要视频级粗召回，减少直接在全部 child 上搜索的范围
- 后续要做层级检索、先父后子重排或跨视频聚合分析

### 当前落地规则
1. `child record id`  
- `{video_id}_{entity_hint}`

2. `parent record id`  
- `{video_id}`

3. `child -> parent` 关联  
- child metadata 中保存 `parent_id=video_id`

4. collection 划分  
- child collection：默认在线检索入口
- parent collection：用于视频级粗召回与后续层级检索扩展

### 风险与收益
- 收益：保留现有 track-level 语义检索效果，同时补齐 video-level 召回层
- 收益：为后续先父后子检索、层级 rerank、跨视频归并提供结构基础
- 风险：parent document 更长，需关注 embedding 成本与检索噪声
- 风险：若后续在线链路同时引入 parent 检索，需要重新评估融合策略
