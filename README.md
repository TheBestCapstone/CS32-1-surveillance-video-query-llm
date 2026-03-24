Capstone/
├── README.md
├── data/ # 外挂数据库
│ ├── raw/
│ └── annotations/
├── config/
│ ├── trackers/
│ ├── models/
│ └── retrieval/
├── src/
│ ├── core/ # 底层模型封装与统一数据协议
│ │ ├── models/ # YOLO / embedding / LLM / VLM 封装
│ │ └── schema/ # Event / Track / Clip / Query / Evidence
│ │
│ ├── ingestion/ # 视频 / JSON 输入适配
│ │ ├── video\_loader.py
│ │ └── json\_loader.py
│ │
│ ├── factory/ # 离线视频理解流水线协调层
│ │ ├── processors/
│ │ │ ├── vision.py # 检测、跟踪、基础视觉特征
│ │ │ ├── captioner.py # 可选：片段描述 / 多模态描述
│ │ │ └── analyzer.py # 事件抽取、动作逻辑判定
│ │ └── coordinator.py # Video -> Event/Clip/Metadata 编排
│ │
│ ├── indexing/ # 知识构建与索引持久化
│ │ ├── document\_builder.py # Event doc / Summary doc 构造
│ │ ├── embedder.py # Text / Image embedding
│ │ ├── graph\_builder.py # 时序 / 实体 / 关系图构建
│ │ └── store\_manager.py # vector / graph / metadata 一致性写入
│ │
│ ├── retrieval/ # 纯检索层
│ │ ├── event\_retriever.py # 事件级向量检索
│ │ ├── summary\_retriever.py # 时间窗/全局摘要检索
│ │ ├── graph\_retriever.py # 图关系检索
│ │ ├── metadata\_filter.py # 结构化过滤
│ │ ├── multi\_modal.py # 跨模态匹配
│ │ ├── reranker.py # 召回结果精排
│ │ └── fusion.py # 多路证据融合
│ │
│ ├── agent/ # LangGraph 编排层（必须保留）
│ │ ├── state.py # 全局状态 / 上下文 / 中间结果
│ │ ├── graph.py # 主决策图
│ │ ├── nodes/ # parse / route / retrieve / answer
│ │ └── tools/ # 搜索、核查、回放、总结等 Tool 封装
│ │
│ └── common/ # 通用配置、日志、路径、工具函数
│
├── outputs/
│ ├── video\_understanding/ # events.json / clips.json / tracked.mp4
│ ├── indexing/ # docs / embeddings / 中间索引产物
│ ├── vector\_store/
│ ├── graph\_store/
│ └── cache/
├── scripts/
├── docs/
└── tests/
严格按照这个修改我的capstone 不需要的可以删除
