# FastAPI 中的 agent 相关接口说明

本文档整理当前 `fastapi` 目录下与 `agent` 调用、数据库切换、查询返回相关的接口定义，基于当前代码实现编写。

## 1. 接口总览

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/healthz` | 查看服务与 `agent` 运行状态 |
| `GET` | `/api/v1/databases` | 列出当前可供 `agent` 使用的数据库 |
| `GET` | `/api/v1/databases/current` | 查看当前是否已选择数据库 |
| `POST` | `/api/v1/databases/select` | 为 `agent` 切换当前查询数据库 |
| `POST` | `/api/v1/query` | 调用 `agent` 执行一次普通查询 |
| `POST` | `/api/v1/query/stream` | 以 `SSE` 方式流式返回 `agent` 查询过程与最终结果 |
| `POST` | `/api/v1/video/upload` | 上传视频并建库，建库成功后可自动切换到新数据库 |

## 2. 接口关系

- `agent` 查询前，通常需要先调用 `/api/v1/databases/select` 选择数据库。
- `/api/v1/query` 是标准同步查询接口，返回完整结果。
- `/api/v1/query/stream` 是流式查询接口，返回中间节点进度和最终结果。
- `/api/v1/video/upload` 在 `import_to_db=true` 且建库成功时，会自动调用数据库选择逻辑，把新库切成当前库。
- `/healthz` 可以用来确认当前运行目标库、`execution_mode` 和图状态。

## 3. 数据模型

### 3.1 QueryRequest

用于 `/api/v1/query` 和 `/api/v1/query/stream`。

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `query` | `str` | 无 | 用户查询文本，长度 `1-500` |
| `thread_id` | `str \| null` | `null` | 可选线程标识；为空时服务端自动生成 |
| `user_id` | `str` | `fastapi-user` | 传给图配置的用户标识 |
| `include_rows` | `bool` | `false` | 是否返回召回到的结果行 |
| `include_node_trace` | `bool` | `true` | 是否返回执行节点轨迹 |
| `top_k_rows` | `int` | `5` | 返回结果行上限，范围 `1-20` |

### 3.2 QueryResponse

`/api/v1/query` 的标准返回结构，以及 `/api/v1/query/stream` 最终 `final` 事件里的数据主体。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query` | `str` | 原始查询文本 |
| `answer` | `str` | 去掉 `Sources:` 后的简化回答 |
| `final_answer` | `str` | 最终回答全文 |
| `raw_final_answer` | `str` | 原始最终回答 |
| `thread_id` | `str` | 本次查询使用的线程标识 |
| `user_id` | `str` | 本次查询使用的用户标识 |
| `elapsed_ms` | `float` | 耗时，单位毫秒 |
| `answer_type` | `str` | 回答类型 |
| `node_trace` | `list[str]` | 执行过的节点轨迹 |
| `citations` | `list[dict]` | 引用信息 |
| `verifier_result` | `dict` | 匹配校验结果 |
| `classification_result` | `dict` | 查询分类结果 |
| `routing_metrics` | `dict` | 路由指标 |
| `fusion_meta` | `dict` | 融合相关调试信息 |
| `rows` | `list[dict]` | 返回给前端的检索结果行 |

### 3.3 DatabaseOptionResponse

数据库列表和当前选中数据库都会用到该结构。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | `str` | 数据库唯一标识 |
| `label` | `str` | 展示给前端的名称 |
| `sqlite_path` | `str` | `SQLite` 路径 |
| `chroma_path` | `str` | `Chroma` 路径 |
| `chroma_namespace` | `str` | `Chroma namespace` |
| `source` | `"uploaded" \| "configured"` | 数据库来源 |
| `selected` | `bool` | 当前是否被选中 |

## 4. 详细接口

### 4.1 `GET /healthz`

用于检查服务当前状态，以及 `agent` 实际运行配置。

#### 返回字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | `str` | 当前固定为 `ok` |
| `graph_ready` | `bool` | 图对象是否已初始化 |
| `execution_mode` | `str` | 当前执行模式，默认是 `parallel_fusion` |
| `sqlite_path` | `str` | 当前生效的 `SQLite` 路径 |
| `chroma_path` | `str` | 当前生效的 `Chroma` 路径 |
| `chroma_namespace` | `str` | 当前生效的 `namespace` |
| `chroma_child_collection` | `str` | 子集合名 |
| `chroma_parent_collection` | `str` | 父集合名 |
| `chroma_event_collection` | `str` | 事件集合名 |
| `selected_database_id` | `str \| null` | 当前选中的数据库 `id` |
| `database_selected` | `bool` | 是否已显式选择数据库 |

#### 使用场景

- 服务启动后做健康检查。
- 调试当前 `agent` 实际连到哪个数据库。
- 检查图是否已经准备完成。

### 4.2 `GET /api/v1/databases`

列出当前所有可供 `agent` 使用的数据库。

#### 数据来源

- 当前配置数据库，固定 `id` 为 `configured-default`。
- `fastapi/data/video_jobs/` 下已生成的上传数据库。
- 如果当前已有已选数据库，会优先放在列表前面。

#### 返回结构

```json
{
  "databases": [
    {
      "id": "configured-default",
      "label": "当前配置数据库",
      "sqlite_path": "...",
      "chroma_path": "...",
      "chroma_namespace": "...",
      "source": "configured",
      "selected": false
    }
  ]
}
```

#### 说明

- 服务内部会按 `id` 和目标路径去重。
- 如果当前已选数据库与配置数据库或上传数据库路径重复，只保留一份。

### 4.3 `GET /api/v1/databases/current`

返回当前选中的数据库状态。

#### 返回结构

```json
{
  "selected_database": {
    "id": "video-xxxx",
    "label": "demo.mp4 (video-xxxx)",
    "sqlite_path": "...",
    "chroma_path": "...",
    "chroma_namespace": "...",
    "source": "uploaded",
    "selected": true
  },
  "database_selected": true
}
```

#### 说明

- 如果当前还没选库，`selected_database` 为 `null`，`database_selected` 为 `false`。

### 4.4 `POST /api/v1/databases/select`

切换 `agent` 当前使用的数据库。

#### 请求体

```json
{
  "database_id": "configured-default"
}
```

#### 返回结构

```json
{
  "status": "ok",
  "selected_database": {
    "id": "configured-default",
    "label": "当前配置数据库",
    "sqlite_path": "...",
    "chroma_path": "...",
    "chroma_namespace": "...",
    "source": "configured",
    "selected": true
  }
}
```

#### 服务端行为

- 校验 `database_id` 非空。
- 在当前数据库列表中查找目标库。
- 找到后调用运行时切换逻辑，更新：
  - `AGENT_SQLITE_DB_PATH`
  - `AGENT_CHROMA_PATH`
  - `AGENT_CHROMA_NAMESPACE`
- 清空 `BM25` 缓存。
- 重置图对象，让后续查询按新目标重新初始化。

#### 失败情况

- `400`: `database_id must not be empty`
- `400`: `unknown database_id: xxx`

### 4.5 `POST /api/v1/query`

标准同步查询接口。

#### 请求体示例

```json
{
  "query": "find the clip with two police cars",
  "thread_id": null,
  "user_id": "fastapi-user",
  "include_rows": true,
  "include_node_trace": true,
  "top_k_rows": 3
}
```

#### 服务端处理流程

1. 清洗 `query` 文本。
2. 校验 `query` 非空。
3. 校验当前已经选择数据库；未选库会直接报错。
4. 若没有传 `thread_id`，自动生成形如 `fastapi-xxxxxxxxxxxx` 的线程号。
5. 读取短期对话历史并拼接到消息列表。
6. 调用图的 `stream(..., stream_mode="values")` 执行查询。
7. 收集最后一个状态块，提取：
   - `final_answer`
   - `raw_final_answer`
   - `answer_type`
   - `summary_result.citations`
   - `verifier_result`
   - `classification_result`
   - `routing_metrics`
   - `sql_debug.fusion_meta`
   - 最终结果行
8. 把本轮问答写入短期记忆。
9. 返回 `QueryResponse`。

#### 返回特点

- `answer` 是去掉 `Sources:` 段后的纯回答。
- `rows` 只有在 `include_rows=true` 时才返回。
- `rows` 最多返回 `top_k_rows` 条。
- `node_trace` 只有在 `include_node_trace=true` 时才会持续累积。

#### 失败情况

- `400`: `query must not be empty`
- `400`: `请先选择数据库后再查询`
- `500`: 其它未捕获异常

### 4.6 `POST /api/v1/query/stream`

流式查询接口，返回类型为 `text/event-stream`，适合前端边看过程边拿最终结果。

#### 请求体

与 `/api/v1/query` 完全一致，使用同一个 `QueryRequest`。

#### 事件类型

##### `chunk`

每经过一次图状态更新，就会输出一个 `chunk` 事件。

```text
event: chunk
data: {"index":1,"query":"...","thread_id":"...","user_id":"...","current_node":"self_query_node","elapsed_ms":123.45,"node_trace":["self_query_node"]}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `index` | 当前块序号，从 `1` 开始 |
| `query` | 查询文本 |
| `thread_id` | 线程标识 |
| `user_id` | 用户标识 |
| `current_node` | 当前节点名 |
| `elapsed_ms` | 当前累计耗时 |
| `node_trace` | 到当前为止的节点轨迹 |

##### `final`

图执行结束后输出一次 `final` 事件，其 `data` 结构与 `QueryResponse` 基本一致。

```text
event: final
data: {"query":"...","answer":"...","final_answer":"..."}
```

##### `error`

出现异常时输出 `error` 事件。

```text
event: error
data: {"detail":"..."}
```

#### 当前实现说明

- 该接口会把最终问答写入短期记忆。
- 该接口内部没有像 `/api/v1/query` 一样在入口处显式校验“是否已选择数据库”，当前行为主要依赖运行时环境与图执行过程。

### 4.7 `POST /api/v1/video/upload`

这个接口本质上是视频上传与建库接口，但它和 `agent` 的数据库切换直接联动，因此一并记录。

#### 表单字段

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `files` | 多文件 | 无 | 批量上传文件入口 |
| `file` | 单文件 | 无 | 单文件上传入口 |
| `tracker` | `str` | `botsort_reid` | 跟踪器配置 |
| `model_path` | `str` | `11m` | 模型配置 |
| `conf` | `float` | `0.25` | 检测阈值 |
| `iou` | `float` | `0.25` | `IOU` 阈值 |
| `target_classes` | `str \| null` | `null` | 目标类别 |
| `camera_id` | `str \| null` | `null` | 相机标识 |
| `refine_mode` | `str` | `none` | 只允许 `none`、`vector`、`full` |
| `refine_model` | `str` | `gpt-5.4-mini` | 精修模型 |
| `import_to_db` | `bool` | `true` | 是否导入数据库 |
| `sqlite_path` | `str \| null` | `null` | 可选自定义 `SQLite` 路径 |
| `chroma_path` | `str \| null` | `null` | 可选自定义 `Chroma` 路径 |
| `chroma_namespace` | `str \| null` | `null` | 可选自定义 `namespace` |

#### 关键逻辑

- 支持 `files` 和 `file` 两种上传方式，服务端会合并成统一列表。
- 没有文件时返回 `400`。
- `refine_mode` 不在 `none/vector/full` 中时返回 `400`。
- 若 `video_ingest_service.process_uploads(...)` 返回 `imported_to_db=true`，服务端会继续调用数据库选择逻辑，把 `job_id` 对应的新数据库设为当前数据库。

#### 返回主体

返回 `VideoUploadResponse`，主要字段包括：

| 字段 | 说明 |
| --- | --- |
| `status` | 处理状态 |
| `job_id` | 本次上传任务标识 |
| `filename` | 主文件名 |
| `filenames` | 所有上传文件名 |
| `file_count` | 文件数量 |
| `refine_mode` | 实际使用的精修模式 |
| `imported_to_db` | 是否已导入数据库 |
| `pipeline_meta` | 流水线元信息 |
| `events_count` | 事件数 |
| `clip_count` | 片段数 |
| `artifacts` | 产物路径列表 |
| `database_import` | 数据库导入结果 |
| `selected_database` | 如果已自动选库，这里会带上选中的数据库信息 |

## 5. 当前接口约束

- `/api/v1/query` 调用前必须先选库。
- `/api/v1/query` 与 `/api/v1/query/stream` 共用同一套请求体字段。
- 当前同步查询和流式查询都会把问答写入短期记忆。
- 数据库切换不是只改前端状态，而是会直接改 `agent` 运行时环境变量和图实例。
- 上传建库成功后，新库会被自动切到当前运行目标。

## 6. 代码位置

- 接口定义：`fastapi/main.py`
- 请求与响应模型：`fastapi/models.py`
- `agent` 调用与数据库切换逻辑：`fastapi/service.py`
- 视频上传与建库逻辑：`fastapi/video_service.py`
