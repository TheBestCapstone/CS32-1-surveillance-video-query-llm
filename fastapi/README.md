<br />

# fastapi

## 目标

- 把现有 `agent/graph.py:create_graph()` 暴露为 HTTP 服务。
- 保持现有 LangGraph 检索与总结链路不变，只新增 API 封装层。
- 提供一个简洁的前端 Web 页面，完成数据库选择、视频上传和查询。
- 前端支持中英切换，默认英文界面。

## 接口

- `GET /`
  - 返回前端 Web 页面。
  - 页面能力：
  - 数据库列表刷新与切换。
  - 拖拽批量上传视频并显示进度。
  - 当前数据库状态展示。
  - 未选库时禁用查询按钮。
- `GET /api/v1/databases`
  - 返回可选数据库列表，包含当前配置数据库和历史上传生成的本地数据库。
- `GET /api/v1/databases/current`
  - 返回当前是否已选中数据库，以及当前选中的数据库详情。
- `POST /api/v1/databases/select`
  - 根据 `database_id` 显式切换数据库。

- `GET /healthz`
- `POST /api/v1/query`
  - 请求示例：

```json
{
  "query": "two white police cars flashing roof lights",
  "include_rows": true,
  "top_k_rows": 3
}
```

- `POST /api/v1/query/stream`
  - 返回 `SSE` 流。
  - 事件类型：
  - `chunk`：每经过一个 graph 节点推送一次当前进度。
  - `final`：最终完整响应。
  - `error`：执行中异常。
- `POST /api/v1/video/upload`
  - 接收 `multipart/form-data` 视频上传，支持单文件和批量文件。
  - 流程：保存上传文件 -> 逐个调用 `video` 单路 pipeline -> 产出各自的 `events/clips` JSON -> 可选 `vector refine` -> 同一批文件自动导入同一个新的 SQLite/Chroma。
  - 关键表单字段：
  - `file`：上传的视频文件。
  - `tracker`：默认 `botsort_reid`。
  - `model_path`：默认 `11m`。
  - `conf` / `iou`：检测参数。
  - `target_classes`：逗号分隔类别列表。
  - `camera_id`：可选摄像头 ID。
  - `refine_mode`：`none`、`vector` 或 `full`。
  - `refine_model`：默认 `gpt-5.4-mini`。
  - `import_to_db`：默认 `true`。
  - 每次新上传默认都会创建一套新的 SQLite/Chroma 目标，并把当前查询服务切到这套新库。
  - 如果一次上传多个视频，这批视频会共用同一个新数据库。
  - 服务端同时校验视频格式和文件大小，大小限制通过 `FASTAPI_MAX_UPLOAD_MB` 控制，默认 `512 MB`。

## 启动

在仓库根目录执行：

```bash
source ~/.bashrc
conda activate capstone
uvicorn main:app --app-dir /home/yangxp/Capstone/fastapi --host 127.0.0.1 --port 8001
```

或直接使用脚本：

```bash
./fastapi/run_uvicorn.sh
```

然后打开：

```text
http://127.0.0.1:8001/
```

## 脚本

- `smoke_test.py`
  - 直连已启动服务做轻量冒烟。
- `test_api_smoke.py`
  - `pytest` 轻量 API 冒烟，用 fake graph 验证接口协议，不依赖真实模型。
- `curl_examples.sh`
  - 同时演示普通查询和 `SSE stream` 查询。
- `run_uvicorn.sh`
  - 使用 `capstone` 环境里的 Python 启动服务。
- `capstone-agent-fastapi.service`
  - `systemd` 单元文件。
- `deploy_systemd.sh`
  - 一键安装并启动 `systemd` 服务。
- `Dockerfile`
  - 多阶段 Docker 构建文件。
- `docker-compose.yml`
  - 容器化部署编排配置。
- `.env.example`
  - Docker 与本地运行时环境变量模板。

## 用法

轻量 smoke：

```bash
source ~/.bashrc
conda activate capstone
python fastapi/smoke_test.py
python fastapi/smoke_test.py --stream
```

`pytest` 冒烟：

```bash
source ~/.bashrc
conda activate capstone
pytest fastapi/test_api_smoke.py -q
```

`curl` 示例：

```bash
./fastapi/curl_examples.sh
./fastapi/curl_examples.sh "find a person near the sidewalk"
```

视频上传示例：

```bash
curl -X POST http://127.0.0.1:8001/api/v1/video/upload \
  -F "files=@/absolute/path/to/demo1.mp4" \
  -F "files=@/absolute/path/to/demo2.mp4" \
  -F "tracker=botsort_reid" \
  -F "model_path=11m" \
  -F "conf=0.25" \
  -F "iou=0.25" \
  -F "refine_mode=none" \
  -F "import_to_db=true"
```

带 `vector refine` 的上传示例：

```bash
curl -X POST http://127.0.0.1:8001/api/v1/video/upload \
  -F "file=@/absolute/path/to/demo.mp4" \
  -F "refine_mode=vector" \
  -F "refine_model=gpt-5.4-mini"
```

带 `full refine` 的上传示例：

```bash
curl -X POST http://127.0.0.1:8001/api/v1/video/upload \
  -F "file=@/absolute/path/to/demo.mp4" \
  -F "refine_mode=full" \
  -F "refine_model=gpt-5.4-mini"
```

部署到 `systemd`：

```bash
chmod +x fastapi/run_uvicorn.sh fastapi/deploy_systemd.sh fastapi/curl_examples.sh
./fastapi/deploy_systemd.sh
```

Docker 部署：

```bash
cd fastapi
cp .env.example .env
docker compose up --build -d
```

如果你本地已经有完整的 `capstone` 依赖，也可以只用页面，不用 Docker：

```bash
source ~/.bashrc
conda activate capstone
uvicorn main:app --app-dir /home/yangxp/Capstone/fastapi --host 127.0.0.1 --port 8001
```

## 说明

- 代码会自动把 `agent/` 加入 `sys.path`，兼容当前仓库里大量 bare import。
- 服务层默认每次请求都生成独立 `thread_id`，避免不同 HTTP 请求互相污染状态。
- 前端使用 `Bootstrap + 原生 JavaScript + AJAX`，没有引入重型前端框架。
- 查询前必须先选库；后端也会做同样校验，直接调 `/api/v1/query` 时若未选库会返回错误。
- `stream` 接口格式是标准 `text/event-stream`，可直接被浏览器、前端 `EventSource` 风格客户端或 `curl -N` 消费。
- 上传视频任务会把中间产物写到 `fastapi/data/video_jobs/<job_id>/`，包含上传文件、`events.json`、`clips.json`、可选 `vector/full refine` 结果，以及该任务独立的 `runtime/` 数据库目录。
- 当前逻辑固定为：每次用户上传新视频，都创建并切换到一套新的 SQLite/Chroma；后续查询默认就是查这次上传对应的新库。
- Docker 部署依赖 `fastapi/requirements-docker.txt`，该文件是从当前 `capstone` 环境导出的 `pip freeze`，目的是尽量贴近你当前可运行环境。
