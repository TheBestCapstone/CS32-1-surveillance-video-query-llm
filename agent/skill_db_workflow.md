# Agent 数据库操作 Skill 指南

## 目标
- 封装 `agent graph` 的数据库创建流程（建库、建表、建索引、初始化插入）
- 支持一键切换 `graph` 使用的数据库路径
- 提供统一的命令行操作方式，减少手工改代码风险

## 新增文件
- [config.py](file:///home/yangxp/Capstone/agent/db/config.py)
  - 统一读取/写入数据库路径配置
  - 支持从 `.env` 读取：
    - `AGENT_SQLITE_DB_PATH`
    - `AGENT_LANCEDB_PATH`
- [sqlite_builder.py](file:///home/yangxp/Capstone/agent/db/sqlite_builder.py)
  - 封装 SQLite 建库流程：
    - 连接配置（`PRAGMA`）
    - 表结构定义（`episodic_events`）
    - 索引创建
    - 初始化数据插入（支持多种 JSON 结构）
    - 构建时自动聚合并去重 `keywords / object_type / object_color`
    - 自动生成 Agent 初始化提示词文档（用于检索前快速判断）
  - 内置异常封装 `DatabaseBuildError`
  - 内置日志输出，便于失败定位
- [manage_graph_db.py](file:///home/yangxp/Capstone/agent/db/manage_graph_db.py)
  - 统一 CLI 入口，支持：
    - `build`：创建/重建数据库并插入初始数据
    - `switch`：一键切换 `graph` 读取的数据库路径

## 代码接入点
- [types.py](file:///home/yangxp/Capstone/agent/node/types.py)
  - `default_sqlite_db_path()` 改为读取 `db/config.py`
  - `default_db_path()` 改为读取 `db/config.py`
  - 这意味着 `graph` 下游节点与工具读取路径时自动走新配置

## 使用方式

### 1) 创建数据库（含表结构、索引）
```bash
cd /home/yangxp/Capstone
python -m agent.db.manage_graph_db build \
  --db-path /home/yangxp/Capstone/data/SQLite/episodic_events.sqlite
```

### 2) 创建数据库并导入初始数据
```bash
cd /home/yangxp/Capstone
python -m agent.db.manage_graph_db build \
  --db-path /home/yangxp/Capstone/data/SQLite/episodic_events.sqlite \
  --seed-json /path/to/seed_a.json /path/to/seed_b.json \
  --reset
```

### 2.1) 创建数据库并指定初始化提示词输出位置
```bash
cd /home/yangxp/Capstone
python -m agent.db.manage_graph_db build \
  --db-path /home/yangxp/Capstone/data/SQLite/episodic_events.sqlite \
  --seed-json /home/yangxp/Capstone/data/basketball_output/basketball_1_events_vector_flat.json \
              /home/yangxp/Capstone/data/basketball_output/basketball_2_events_vector_flat.json \
  --init-prompt-md /home/yangxp/Capstone/agent/init/agent_init_prompt.md \
  --init-prompt-json /home/yangxp/Capstone/agent/init/agent_init_profile.json \
  --reset
```

### 3) 一键切换 graph 使用的数据库路径
```bash
cd /home/yangxp/Capstone
python -m agent.db.manage_graph_db switch \
  --sqlite-path /home/yangxp/Capstone/data/SQLite/new_events.sqlite \
  --lancedb-path /home/yangxp/Capstone/data/lancedb_new
```

执行后会自动写入根目录 `.env`，并输出当前生效路径。

## seed JSON 支持格式
- 单事件对象：`{...}`
- 事件列表：`[{...}, {...}]`
- 视频包裹格式：
```json
{
  "video_id": "xxx.mp4",
  "events": [{...}, {...}]
}
```
- 多视频包裹格式：
```json
[
  {"video_id": "a.mp4", "events": [...]},
  {"video_id": "b.mp4", "events": [...]}
]
```

## `/data/data/events_vector_flat` 数据格式
- 推荐目录：`/home/yangxp/Capstone/data/data/events_vector_flat/`
- 文件建议：`{video_name}_events_vector_flat.json`
- 顶层结构：
```json
{
  "video_id": "basketball_2.mp4",
  "events": [
    {
      "video_id": "basketball_2.mp4",
      "clip_start_sec": 0.0,
      "clip_end_sec": 257.16,
      "start_time": 0.0,
      "end_time": 30.84,
      "object_type": "person",
      "object_color": "dark",
      "appearance_notes": "standing near left bleachers with little motion",
      "scene_zone": "left bleachers",
      "event_text": "From 0.00s to 30.84s, ...",
      "keywords": ["person", "static", "bleachers"],
      "start_bbox_xyxy": [429.75, 271.57, 469.97, 389.37],
      "end_bbox_xyxy": [449.96, 289.02, 481.30, 387.01],
      "entity_hint": "track_id_1"
    }
  ]
}
```
- 字段映射建议（导入 SQLite `episodic_events`）：
- `object_color -> object_color_en`
- `scene_zone -> scene_zone_en`
- `appearance_notes -> appearance_notes_en`
- `event_text -> event_text_en`
- `event_text -> event_summary_en`（若无单独 summary，可先复用）
- `metadata_json` 存原始 event（便于追溯）

## 常见问题排查
- `Seed file not found`
  - 检查 `--seed-json` 路径是否为绝对路径
- `Build failed for ...`
  - 查看终端日志中的原始异常栈（已在 `sqlite_builder.py` 记录）
- 切换后 `graph` 仍读取旧库
  - 检查根目录 `.env` 是否存在并包含 `AGENT_SQLITE_DB_PATH`
  - 重新启动执行进程，确保重新加载环境变量
- 初始化提示词没有生成
  - 检查 `build` 命令是否传了 `--no-init-prompt`
  - 检查 seed 文件中是否存在 `events[].keywords/object_type/object_color`
