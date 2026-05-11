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

## MEVID Evaluation Flow

The MEVID multi-camera test path is split into reusable video modules plus two stable evaluation wrappers.

### Added Video Modules

- `video.factory.person_crop_sampler`
  - Samples person crops from tracked bbox events.
  - Used by appearance refinement and QA evidence sampling.
- `video.factory.appearance_refinement_runner`
  - Runs crop-based person/global-entity appearance refinement for multi-camera output.
  - Also supports single-camera track-level refinement with `entity_hint=track_<id>`.
  - Writes into existing fields only: `object_color`, `appearance_notes`, `keywords`, `event_text`, `entity_hint`.
  - Does not require a schema migration.
- `video.indexing.search_enrichment`
  - Normalizes clothing/color tokens for RAG.
  - Adds retrieval-friendly keywords such as `light_grey_hoodie`, `hood_up`, `cross_camera`, and `same_person`.

### Video-Only QA

Use this to test YOLO + OSNet + topology + matching + optional appearance refinement before involving the agent:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe scripts\run_mevid_video_eval.py --slot 13-50 --limit 40
```

Equivalent direct command:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe tests\test_mevid_full.py --slot 13-50 --limit 40 --no-refine --appearance-refine
```

Useful options:

```powershell
--force-appearance-refine
--with-clip-refine
--video-dir _data/mevid_slots
```

### Single-Camera Appearance Refinement

For a normal single-camera pipeline output, run detection/tracking first:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe -m video.factory.coordinator video path\to\video.mp4 --out-dir pipeline_output
```

Then run track-level crop appearance refinement on the generated `*_events.json`:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe -m video.factory.coordinator appearance --events pipeline_output\your_video_events.json
```

This creates:

```text
*_events_appearance_refined.json
```

The result is shaped like vector refinement events and can be merged/exported for RAG without changing the event schema.

### Video + Agent E2E

Before running the agent, regenerate vector seeds if the pipeline/refinement cache changed:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe scripts\generate_mevid_vector_flat.py --slot 13-50 --force
```

Then run the balanced agent evaluation:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe scripts\run_mevid_agent_eval.py --slot 13-50 --limit 40
```

Equivalent direct command:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe tests\test_mevid_video_agent_e2e.py --slot 13-50 --limit 40 --sample-mode balanced
```

Results are written under:

```text
results/mevid_full_*.json
results/mevid_agent_e2e/<slot>_<timestamp>/
```

The agent report includes answer accuracy, top-hit rate, category breakdown, and per-case predictions. Negative/cross-camera cases should be inspected separately because a model that answers `yes` for every case can still look strong on positive-heavy samples.

### Module Smoke Tests

Run the fast tests for the new MEVID video helpers:

```powershell
C:\Users\17809\anaconda3\envs\capstone\python.exe -m pytest tests\test_mevid_video_modules.py
```

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
