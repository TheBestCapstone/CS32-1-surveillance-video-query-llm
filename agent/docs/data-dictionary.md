# 数据字典与字段语义说明

## 目的
- 这份文档用于统一 `SQLite`、`Chroma`、以及运行态检索结果中的字段语义。
- 目标是减少 schema 漂移、字段误读、以及 SQL/Hybrid 双路径输出不一致。
- 当字段定义发生变化时，优先更新代码真源，再同步更新本文档。

## 单一可信口径
- `SQLite` 表结构真源：`agent/db/schema.py`
- `SQLite` 入库映射真源：`agent/db/sqlite_builder.py`
- `Chroma` 检索输出真源：`agent/tools/db_access.py`
- 运行态结果契约真源：`agent/node/retrieval_contracts.py`

## 一、主表：`episodic_events`

### 表定位
- 表名：`episodic_events`
- 用途：作为结构化检索主表，同时保存语义检索的伴随字段
- 主键：`event_id INTEGER PRIMARY KEY AUTOINCREMENT`

### 字段分组

#### 1. 身份标识字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `event_id` | `INTEGER` | SQLite 行级主键，结构化侧稳定主键 | 数据库自动生成 |
| `video_id` | `TEXT` | 视频文件标识 | 种子事件或外层 payload 的 `video_id` |
| `camera_id` | `TEXT` | 摄像头标识 | 可为空 |
| `track_id` | `TEXT` | 目标轨迹标识 | 种子事件中的 `track_id`，入库时转字符串 |
| `entity_hint` | `TEXT` | 实体提示信息 | 语义 / 实体辅助字段，可为空 |

#### 2. 时间范围字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `clip_start_sec` | `REAL` | 原始片段起始秒数 | 可为空 |
| `clip_end_sec` | `REAL` | 原始片段结束秒数 | 可为空 |
| `start_time` | `REAL` | 事件开始时间 | 结构化和引用最常用时间字段 |
| `end_time` | `REAL` | 事件结束时间 | 结构化和引用最常用时间字段 |
| `duration_sec` | `REAL` | 事件持续时长 | 构建时由 `end_time - start_time` 推导 |

#### 3. 结构化检索字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `object_type` | `TEXT` | 目标类型，如 `person`、`car` | SQL 过滤核心字段 |
| `object_color_en` | `TEXT` | 目标颜色英文值 | 优先使用英文标准值 |
| `scene_zone_en` | `TEXT` | 场景区域英文值 | 如 `left bleachers`、`parking` |
| `motion_level` | `TEXT` | 运动强度描述 | 可为空 |
| `event_type` | `TEXT` | 事件类别 | 可为空 |
| `is_stationary` | `INTEGER` | 是否静止，`1/0` | 当前依据 `appearance_notes_en` 里是否包含 `stationary` 推导 |

#### 4. 几何字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `start_bbox_x1/y1/x2/y2` | `REAL` | 起始帧 bbox | 可为空 |
| `end_bbox_x1/y1/x2/y2` | `REAL` | 结束帧 bbox | 可为空 |

#### 5. 语义检索伴随字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `appearance_notes_en` | `TEXT` | 外观描述 | 语义补充字段 |
| `event_text_en` | `TEXT` | 事件原始英文描述 | 优先取 `event_text_en`，否则从其他文本字段兜底 |
| `event_summary_en` | `TEXT` | 事件摘要英文描述 | 结果展示和回答层常用字段 |
| `keywords_json` | `TEXT` | 关键词列表 JSON | 构建时统一转为 JSON 字符串 |
| `semantic_tags_json` | `TEXT` | 语义标签 JSON | 当前最小实现为 `{"keywords": [...]}` |
| `vector_doc_text` | `TEXT` | 写入向量库的文本文档 | 当前优先取 `event_text_en`，否则用 `event_summary_en` |
| `vector_ref_id` | `TEXT` | 向量侧引用 ID | 格式：`video_id:entity_hint_or_track_id:start:end` |

#### 6. 溯源与演化字段
| 字段 | 类型 | 含义 | 来源 / 说明 |
|---|---|---|---|
| `source_format` | `TEXT` | 原始数据格式来源 | 当前常见值：`events_vector_flat` |
| `schema_version` | `TEXT` | schema 版本 | 当前 builder 默认：`v2_hybrid_sql_vector_complementary` |
| `metadata_json` | `TEXT` | 原始事件 JSON 快照 | 用于回溯和调试 |
| `created_at` | `TEXT` | 创建时间 | 默认当前时间 |
| `updated_at` | `TEXT` | 更新时间 | 默认当前时间 |

## 二、入库映射规则

### 文本字段映射
- `event_text_en`：
  - 优先 `event.event_text_en`
  - 否则 `event.event_text_cn`
  - 否则 `event.event_text`
- `event_summary_en`：
  - 优先 `event.event_summary_en`
  - 否则 `event.event_summary_cn`
  - 否则 `event.event_summary`
  - 再否则回退到 `event_text_en`

### 颜色与区域映射
- `object_color_en`：
  - 优先 `event.object_color_en`
  - 否则 `event.object_color`
- `scene_zone_en`：
  - 优先 `event.scene_zone_en`
  - 否则 `event.scene_zone`

### 派生字段
- `duration_sec = end_time - start_time`
- `is_stationary = 1` 当 `appearance_notes_en` 中包含 `stationary`
- `vector_doc_text = event_text_en or event_summary_en`

## 三、索引字段

### 已建立索引
- `video_id`
- `camera_id`
- `track_id`
- `object_type`
- `object_color_en`
- `scene_zone_en`
- `event_type`
- `motion_level`
- `start_time`
- `end_time`

### 说明
- 当前索引主要服务 `SQL` 结构化过滤。
- 未定义关系型外键；当前数据模型是单表事件库。

## 四、Chroma / Hybrid 输出字段

### `ChromaGateway.search()` 输出
| 字段 | 含义 | 说明 |
|---|---|---|
| `event_id` | Chroma 文档 ID | 不保证等于 SQLite 自增 `event_id` |
| `video_id` | 视频标识 | 来自 metadata |
| `track_id` | 轨迹 / 实体提示 | 当前取 metadata 中的 `entity_hint` |
| `start_time` | 开始时间 | 来自 metadata |
| `end_time` | 结束时间 | 来自 metadata |
| `object_type` | 目标类型 | 来自 metadata |
| `object_color_en` | 目标颜色 | 当前由 metadata `object_color` 映射 |
| `scene_zone_en` | 场景区域 | 当前由 metadata `scene_zone` 映射 |
| `event_summary_en` | 文本摘要 | 当前直接使用 Chroma document |
| `event_text` | 文本内容 | 与 `event_summary_en` 基本同源 |
| `_distance` | 向量距离 | 原始距离值，越小越近 |
| `_hybrid_score` | 混合检索分数 | 由 `alpha * cosine_norm + (1-alpha) * bm25_norm` 计算 |
| `_bm25` | BM25 分数 | 仅用于混合检索内部排序和调试 |

### 重要说明
- `Hybrid` 侧的 `event_id` 当前更接近“文档标识”，不是数据库行主键。
- 因此 citation 中若来源是 `hybrid`，`event_id` 代表向量文档 ID，不应误解为 SQLite 主键。

## 五、运行态统一检索契约

### 统一结果字段
运行态默认要求 SQL / Hybrid 两路尽量输出以下统一字段：

| 字段 | 用途 |
|---|---|
| `event_id` | 结果标识 / citation |
| `video_id` | 视频溯源 |
| `track_id` | 轨迹或实体标识 |
| `start_time` | 时间溯源 |
| `end_time` | 时间溯源 |
| `object_type` | 结构化过滤与展示 |
| `object_color_en` | 结构化过滤与展示 |
| `scene_zone_en` | 结构化过滤与展示 |
| `event_summary_en` | 最终展示 / 回答主文本 |
| `event_text_en` | 语义补充文本 |
| `_distance` | 相似度/距离观测 |
| `_hybrid_score` | Hybrid 分数观测 |
| `_bm25` | BM25 分数观测 |
| `_source_type` | `sql / hybrid / mixed` 来源标记 |

### 统一配置契约
运行态默认 `search_config`：

| 字段 | 默认值 | 含义 |
|---|---:|---|
| `candidate_limit` | `80` | 候选上限 |
| `top_k_per_event` | `20` | 每事件候选数 |
| `rerank_top_k` | `5` | 最终关注前 K |
| `distance_threshold` | `None` | 距离阈值 |
| `hybrid_alpha` | `0.7` | Hybrid 向量权重 |
| `hybrid_fallback_alpha` | `0.9` | Hybrid 放宽 fallback 权重 |
| `hybrid_limit` | `50` | Hybrid 返回上限 |
| `sql_limit` | `80` | SQL 返回上限 |

### `sql_plan` 字段语义
- `table`：当前固定为 `episodic_events`
- `fields`：预期查询字段列表
- `where`：结构化过滤条件列表
- `order_by`：默认 `start_time ASC`
- `limit`：与 `search_config.sql_limit` 对齐

## 六、常见易混字段

### `event_id`
- 在 `SQLite`：稳定主键，自增整数
- 在 `Hybrid/Chroma`：文档 ID，可能是 `video_track_time` 风格字符串
- 结论：不能跨系统直接假设二者同义

### `event_text_en` vs `event_summary_en`
- `event_text_en`：更接近原始描述
- `event_summary_en`：更适合展示与回答
- 当前回答层优先使用 `event_summary_en`

### `object_color_en` vs `object_color` vs `object_color_cn`
- 运行主链统一口径应使用 `object_color_en`
- `object_color` 多出现在原始种子数据
- `object_color_cn` 主要存在于旧 `SQLiteGateway` 路径，不应作为默认主链标准字段

### `scene_zone_en` vs `scene_zone`
- 运行主链统一口径应使用 `scene_zone_en`
- `scene_zone` 主要是种子 JSON 的原字段名

## 七、数据使用建议

### 开发建议
- 写新代码时，优先使用：
  - `event_summary_en`
  - `object_color_en`
  - `scene_zone_en`
  - `event_id + video_id + start_time + end_time`
- 不要把 `Hybrid` 的 `event_id` 直接当成 SQLite 主键做 join 假设。

### 测试建议
- 断言优先使用统一字段：
  - `video_id`
  - `event_summary_en`
  - `event_id`
  - `start_time / end_time`
- 若测试 `citation`，应同时容忍：
  - SQL 引用使用整数 `event_id`
  - Hybrid 引用使用字符串文档 ID

### 漂移治理建议
- 后续若新增字段，至少同步四处：
  - `schema.py`
  - `sqlite_builder.py`
  - `db_access.py`
  - `retrieval_contracts.py`
- 再同步本文档，避免实现和文档再次分叉。

## 八、当前已知限制
- 当前模型是单表事件库，不涉及复杂外键关系。
- `Hybrid` 引用已经可审计，但其 `event_id` 仍是向量文档口径，不是关系型主键口径。
- `SQLiteGateway` 仍保留部分旧字段口径（如 `object_color_cn`），不应被视为默认主链标准。
