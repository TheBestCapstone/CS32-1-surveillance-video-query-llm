# CS32 Capstone Week 3 技术调研任务分配

## 本周目标

完成技术方向调研与论文阅读。每个小组需要阅读推荐论文，理解核心方法，总结技术路线，并提出潜在改进点。周五会议每组进行约 5 分钟分享。

---

## 第一组：视频事件检测与 Tracking Pipeline（难度：中等）

### 任务

1. 调研 CCTV 视频中常见的目标检测与跟踪 pipeline。  
2. 理解 `detection → tracking → event extraction` 的完整流程。  
3. 总结如何从视频生成结构化 metadata（事件、对象、时间戳等）。  
4. 思考这些 metadata 如何支持后续的语义检索。  
5. 设计一个适合监控视频的基础事件 schema。  

### 推荐论文

- **YOLOv8: Real-Time Object Detection**  
  https://arxiv.org/abs/2304.00501

- **ByteTrack: Multi-Object Tracking by Associating Every Detection Box**  
  https://arxiv.org/abs/2110.06864

- **ActionFormer: Localizing Moments of Actions with Transformers**  
  https://arxiv.org/abs/2204.12762

---

## 第二组：Temporal Reasoning 与视频时间理解（难度：中高）

### 任务

1. 调研视频问答中的时间推理问题（before / after / during）。  
2. 阅读 Temporal Video QA 相关论文。  
3. 理解如何建模事件顺序与时间关系。  
4. 分析如何在检索系统中加入时间约束。  
5. 设计一个 temporal-aware retrieval pipeline。  

### 推荐论文

- **NExT-QA: Next Phase of Question Answering to Explaining Temporal Actions**  
  https://arxiv.org/abs/2105.08276

- **TimeChat: Video Temporal Reasoning with Large Language Models**  
  https://arxiv.org/abs/2312.02068

- **VideoChatGPT: Towards Detailed Video Understanding via LLMs**  
  https://arxiv.org/abs/2306.05424

---

## 第三组：Video Retrieval 与 Video RAG（难度：中等）

### 任务

1. 调研 Video Retrieval 和 Video Question Answering 系统。  
2. 理解视频片段分割（video chunking）方法。  
3. 研究视频 embedding 与向量检索。  
4. 分析 RAG 如何应用在视频数据中。  
5. 总结适合 CCTV 视频的 Hybrid Retrieval 架构。  

### 推荐论文

- **VideoRAG: Retrieval-Augmented Generation for Long Videos**  
  https://arxiv.org/abs/2502.01549

- **VRAG: Retrieval-Augmented Video Question Answering**  
  https://arxiv.org/abs/2503.00578

- **Video-RAG: Visually-aligned Retrieval Augmented Video QA**  
  https://arxiv.org/abs/2411.13093

---

## 第四组：Benchmark 与数据集调研（难度：较低）

### 任务

1. 调研监控视频相关数据集。  
2. 分析不同数据集的规模、annotation 类型和适用场景。  
3. 总结每个 benchmark 的评估指标。  
4. 对比不同数据集的优缺点。  
5. 推荐最适合 CS32 项目的数据集。  

### 推荐数据集 / 论文

- **MEVA Dataset: Multiview Extended Video with Activities**  
  https://mevadata.org/

- **VIRAT Video Dataset for Surveillance Event Recognition**  
  https://viratdata.org/

- **MTMMC: Multi-Target Multi-Camera Tracking Dataset**  
  https://arxiv.org/abs/2402.00605

- **MSAD: Multi-Scene Anomaly Detection Dataset**  
  https://arxiv.org/abs/2507.02074

---

## 周五会议汇报要求

每个小组需要准备：

1. 一页 PPT 总结论文核心方法。  
2. 一张技术 pipeline 示意图。  
3. 一个潜在改进方向。  
4. 如果是 benchmark 组，需要给出推荐数据集。  
