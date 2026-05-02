# Capstone Project Structure

```text
Capstone/
├── README.md
├── data/                         # 外挂数据库
│   ├── raw/
│   └── annotations/
├── config/
│   ├── trackers/
│   ├── models/
│   └── retrieval/
├── video/
│   ├── core/                     # 底层模型封装与统一数据协议
│   │   ├── models/               # YOLO / embedding / LLM / VLM 封装
│   │   └── schema/               # Event / Track / Clip / Query / Evidence
│   │
│   ├── ingestion/                # 视频 / JSON 输入适配
│   │   ├── video_loader.py
│   │   └── json_loader.py
│   │
│   ├── factory/                  # 离线视频理解流水线协调层
│   │   ├── processors/
│   │   │   ├── vision.py         # 检测、跟踪、基础视觉特征
│   │   │   ├── captioner.py      # 可选：片段描述 / 多模态描述
│   │   │   └── analyzer.py       # 事件抽取、动作逻辑判定
│   │   └── coordinator.py        # Video -> Event/Clip/Metadata 编排
│   │
│   ├── indexing/                 # 知识构建与索引持久化
│   │   ├── document_builder.py   # Event doc / Summary doc 构造
│   │   ├── embedder.py           # Text / Image embedding
│   │   ├── graph_builder.py      # 时序 / 实体 / 关系图构建
│   │   └── store_manager.py      # vector / graph / metadata 一致性写入
│   │
│   └── common/                   # 通用配置、日志、路径、工具函数
│
├── agent/                        # LangGraph 编排层（必须保留）
│   ├── state.py                  # 全局状态 / 上下文 / 中间结果
│   ├── graph.py                  # 主决策图
│   ├── nodes/                    # parse / route / retrieve / answer
│   ├── tools/                    # 搜索、核查、回放、总结等 Tool 封装
│   │
│   ├── retrieval/                # 纯检索层
│   │   ├── event_retriever.py    # 事件级向量检索
│   │   ├── summary_retriever.py  # 时间窗/全局摘要检索
│   │   ├── graph_retriever.py    # 图关系检索
│   │   ├── metadata_filter.py    # 结构化过滤
│   │   ├── multi_modal.py        # 跨模态匹配
│   │   ├── reranker.py           # 召回结果精排
│   │   └── fusion.py             # 多路证据融合
│   │
│   └── common/                   # 通用配置、日志、路径、工具函数
│
├── outputs/
│   ├── video_understanding/      # events.json / clips.json / tracked.mp4
│   ├── indexing/                 # docs / embeddings / 中间索引产物
│   ├── vector_store/
│   ├── graph_store/
│   └── cache/
├── scripts/
├── docs/
└── tests/
```

## Current Chroma Chunk Strategy

- The vector index now uses a parent-child layout.
- Child index keeps the current track-level chunking:
  - record id: `{video_id}_{entity_hint}`
  - granularity: one child record per track
  - purpose: semantic retrieval over track-level behavior
- Parent index is grouped by `video_id`:
  - record id: `{video_id}`
  - granularity: one parent record per video
  - purpose: coarse video-level recall and parent-child routing
- Child metadata stores `parent_id=video_id` so parent and child records stay linked.
- Current online retrieval still reads the child collection by default, while the parent collection is built for hierarchical retrieval expansion.

## FastAPI Service

- The Web UI and API service now live under `fastapi/`.
- Quick local startup:

```bash
./quick_start.sh
```

- Manual startup:

```bash
source ~/.bashrc
conda activate capstone
uvicorn main:app --app-dir /home/yangxp/Capstone/fastapi --host 127.0.0.1 --port 8001
```

- Default local entry:
  - `http://127.0.0.1:8001/`
- Deployment guide:
  - See `deploy.md`
