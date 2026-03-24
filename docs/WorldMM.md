下面只基于你这次给的两篇论文和我刚查到的论文/项目页/源码来回答，不参照以往记忆。

## 先给结论

2512.02425 这篇是 **WorldMM: Dynamic Multimodal Memory Agent for Long Video Reasoning**。它的核心不是“一个统一数据库”，而是把长视频拆成三类互补记忆：

* **情景记忆 / episodic memory**：记录“某一段时间里发生了什么”，而且是**多时间尺度**的；
* **语意记忆 / semantic memory**：把很多片段中的事实逐步抽象成**长期知识与习惯模式**；
* **视觉记忆 / visual memory**：保留可直接回看的视觉证据，用于细粒度物体、外观、场景核实。 ([arXiv][1])

它的检索也不是固定 pipeline，而是一个 **adaptive retrieval agent**：每一轮先判断“继续搜还是回答”，如果继续搜，就只选一个 memory type（episodic / semantic / visual）和对应查询语句，再把本轮结果加入历史，进入下一轮，直到决定信息足够。源码里这个循环就在 `WorldMemory.answer()` 里。 ([worldmm.github.io][2])

---

# 1. 三类记忆的构建过程

## 1.1 情景记忆 Episodic Memory：怎么建

### 论文层面的定义

WorldMM 的 episodic memory 用来索引**事实性事件 - 指在某个具体时间段内真实发生、可被明确描述和定位的行为、交互或状态变化。**，而且是 **multi-scale textual event graphs**，来源是从细到粗的视频片段 caption。项目页明确写了：episodic memory 是“从 fine-to-coarse video segments 构建的多尺度文本事件图”，用于同时支持局部细节和长程时序理解。 ([worldmm.github.io][2])

### 源码里的实际建库流程

从脚本 `script/3_build_memory.sh` 看，episodic memory 的构建分三步：

1. **生成 30 秒一级的第一人称 caption**

   * `preprocess/episodic_memory/generate_fine_caption.py`
2. **把 30 秒 caption 再生成多尺度记忆**

   * `python -m worldmm.memory.episodic.multiscale`
3. **对 caption 做 OpenIE，抽三元组**

   * `preprocess/episodic_memory/extract_episodic_triples.py` ([GitHub][3])

### 第一步：先把同步后的 caption/transcript 变成第一人称 caption

`generate_fine_caption.py` 的逻辑很清楚：

* 输入来自 `EgoLifeCap/Sync` 的同步文件；
* 把同一视频文件里连续的 caption/transcript 片段聚成 segment；
* 用 `gpt-5-mini` 按 prompt 重写成**第一人称、简洁、面向物体与动作**的 caption；
* 输出结构包含：

  * `start_time`
  * `end_time`
  * `text`
  * `date`
  * `video_path` ([GitHub][4])

它的 prompt 甚至给了很明确的要求：
把 `Jake: ...` 转成 `I ...`，突出 objects / tools / interactions，并保持时间顺序。 ([GitHub][4])

### 第二步：生成多尺度事件记忆

`worldmm.memory.episodic.multiscale` 里，作者没有自己从零写一个多尺度聚合器，而是直接复用了 **EgoRAG** 的组件：

* `RagAgent`
* `Chroma`
* `gen_event`

流程是：

* 先 `agent.create_database_from_json(json_path)` 用 30 秒 JSON 建数据库；
* 再 `gen_event(...)` 生成更粗粒度事件。 ([GitHub][5])

再结合 `eval/eval.py` 可以看出它最终会加载四个粒度：

* `30sec`
* `3min`
* `10min`
* `1h` ([GitHub][6])

也就是说，episodic memory 的实际载体不是只有一层 caption，而是一个 **30s / 3min / 10min / 1h 的多尺度事件文本集合**。

### 第三步：给每个细粒度 caption 抽取 episodic triples

`extract_episodic_triples.py` 的做法是：

* 读取刚才生成的 caption JSON；
* 提取每条 `text`；
* 调用 `OpenIE.batch_openie(...)`；
* 先做 NER，再做 triple extraction 先识别句子里的关键实体，再抽取这些实体之间的动作或关系三元组。；
* 用 `date[-1] + end_time.zfill(8)` 作为 timestamp key；
* 生成：

  * `episodic_triples[timestamp] = ...`
  * `raw_video[timestamp] = video_path` ([GitHub][7])

`OpenIE` 源码里还能看到它内部调用了两个 prompt：

* `ner`
* `triple_extraction` ([GitHub][8])

### episodic 的一个源码级例子

假设某 30 秒同步片段原始内容是：

* caption: “Reach down and open the drawer.”
* caption: “Grab the scissors.”
* transcript: “Jake: These should work.”

在 `generate_fine_caption.py` 的 prompt 例子里，它会被改写成：

> I open the drawer and grab the scissors. "These should work," I say. ([GitHub][4])

随后 `extract_episodic_triples.py` 会对这段文本做 OpenIE，可能得到类似：

* `(I, open, drawer)`
* `(I, grab, scissors)`
  这类 timestamp 对齐的事件三元组，再写入 episodic triple 结果文件。这里后三元组内容是我根据代码逻辑做的**示意性例子**，不是论文里逐字给出的真实输出。支撑点是：代码确实把 caption 逐条送入 OpenIE，并为每个 timestamp 保存 triple 列表。 ([GitHub][7])

---

## 1.2 语意记忆 Semantic Memory：怎么建

### 论文层面的定义

项目页写得很直白：semantic memory 是一个 **continuously updated knowledge graph**，不断累积视频全程中的高层关系与习惯。它解决的是 episodic memory 难以表示“跨多个事件反复出现的模式”这个问题。 ([worldmm.github.io][2])

### 源码里的构建流程

`3_build_memory.sh` 里 semantic 分两步：

1. `extract_semantic_triples.py`
2. `consolidate_semantic_memory.py` ([GitHub][3])

### 第一步：从 episodic triples 批量抽 semantic triples

`extract_semantic_triples.py` 的关键逻辑是：

* 先读取 30 秒 caption；
* 再读取之前 episodic 阶段产出的 `openie_results_gpt-5-mini.json`；
* 按 `period = 10`，把 caption **每 10 条分成一组**；
* 对每组收集对应的 episodic triples；
* 然后交给 `SemanticExtraction.batch_semantic_extraction(...)`。 ([GitHub][9])

也就是说，semantic memory 不是直接从原始视频抽，而是：

**视频 → caption → episodic triples（事件三元组） → 每 10 条组块 → semantic triples（语意三元组）**

这是一个很明确的“从事件到概念”的抽象链。

`SemanticExtraction` 的输入不是视频，而是格式化后的 episodic triples；它调用 prompt `semantic_extraction`，输出两部分：

* `semantic_triples`
* `episodic_evidence` ([GitHub][10])

其中 `episodic_evidence` 非常重要，因为它保留了“这个语义知识是从哪些 episodic triples 归纳来的”。

### 第二步：按时间连续做 semantic consolidation 语意合并

`consolidate_semantic_memory.py` 是这篇论文最关键的“记忆累积”步骤之一。

它会：

* 读取 `semantic_extraction_results_gpt-5-mini.json`；
* 按 timestamp 顺序遍历；
* 维护两个不断增长的列表：

  * `accumulated_semantic_triples`
  * `accumulated_episodic_evidence`
* 对每个新时间点的 triples，调用 `SemanticConsolidation.batch_semantic_consolidation(...)`；
* 返回：

  * `consolidated_triples`
  * `consolidated_evidence`
  * `triples_to_remove`
    然后更新累计状态，再把当前时刻的 consolidated state 存下来。 ([GitHub][11])
可以。你可以把 **semantic consolidation** 理解成：

**新来的语义知识不会直接追加，而是先和旧知识比相似、再合并重写，最后删掉被新知识覆盖的旧表达。** 这正是代码里“先找相近旧 triples，再让 LLM 输出 `updated_triple` 和 `triples_to_remove`，并把证据合并”的流程。([GitHub][1])

## 例子：按时间连续累积“清洁习惯”知识

假设前面两个时间点，系统已经从视频里抽到了这些 semantic triples。

### 时间点 T1

当前已有累计语义记忆：

* `["I", "use", "a towel to wipe dishes"]`
  evidence: `["T1_0", "T1_2"]`

这表示：在 T1 之前，系统已经总结出一条知识——
**我会用毛巾擦餐具。**

---

### 时间点 T2

又来了新的 semantic extraction 结果：

* `["I", "dry", "cups with a kitchen towel"]`
  evidence: `["T2_1"]`

这时不会直接把这条新 triple 生硬加入库里，而是会进入 consolidation：

### 第一步：找相似旧 triple

代码会先把新旧 triples 都转成文本做 embedding，相似度检索出相关旧 triple。
这里很可能会发现：

* 新 triple: `I dry cups with a kitchen towel`
* 旧 triple: `I use a towel to wipe dishes`

两者语义接近，都在表达“用毛巾清洁厨房器具”。([GitHub][2])

---

### 第二步：LLM 做语义合并

然后系统把：

* `new_triple`
* `existing_triples`

一起送给 `semantic_consolidation` prompt，让 LLM 决定要不要改写成一个更稳定、更泛化的新表达。([GitHub][2])

可能得到：

* `updated_triple`:

  * `["I", "use", "a kitchen towel to clean kitchenware"]`

* `triples_to_remove`:

  * 旧的 `["I", "use", "a towel to wipe dishes"]`

---

### 第三步：合并证据并更新累计状态

这时系统会：

1. 从累计记忆里删掉旧 triple；
2. 把旧 triple 的 evidence 和新 triple 的 evidence 合并；
3. 把新的 consolidated triple 放回累计记忆。([GitHub][1])

所以更新后的累计结果会变成：

* `["I", "use", "a kitchen towel to clean kitchenware"]`
  evidence: `["T2_1", "T1_0", "T1_2"]`

---

## 这个例子的本质

也就是：

* **T1** 只知道“我会用毛巾擦盘子”
* **T2** 又看到“我会用毛巾擦杯子”
* **consolidation 后** 不再保存两条分散、局部、重复的知识
* 而是变成一条更抽象、更稳定的长期知识：

**我通常会用厨房毛巾清洁餐具/厨房器具。**

### semantic consolidation 具体怎么做

源码里 semantic consolidation 是“嵌入召回 + LLM 合并”两阶段：

1. **先用 embedding 找相近旧 triple**

   * `embedding_model.encode(..., modality="text")`
   * cosine similarity
   * 取 top-k，阈值过滤 ([GitHub][12])

2. **再让 LLM 决定怎么合并**

   * prompt 名叫 `semantic_consolidation`
   * 输入：

     * `new_triple`
     * `existing_triples`
   * 输出：

     * `updated_triple`
     * `triples_to_remove` ([GitHub][12])

这说明 semantic memory 不是简单 append，而是会做：

* 去重
* 合并同义/近义知识
* 用新知识替换旧知识

### semantic 的一个直观例子

项目页给了一个典型 case：
episodic memory 很难单独表达“这个人平时经常拿什么来擦餐具”这类**习惯性行为**，但 semantic memory 可以把多次事件累计后形成长期知识。 ([worldmm.github.io][2])

按源码逻辑，你可以把它想成这样：

某 10 个 chunk 的 episodic triples 里多次出现：

* `(I, wipe, plate with towel)`
* `(I, dry, cup with towel)`
* `(I, clean, bowl using towel)`

`semantic_extraction` 可能抽成更抽象的知识：

* `(I, use, towel for cleaning kitchenware)`

后续几轮 consolidation 再把类似表达合并成稳定 triple。
这条具体 triple 是我根据论文给的“habitual behaviors”案例和代码逻辑做的示意，不是源码里现成样例；但“从 episodic 抽 semantic、再跨时间 consolidate”的过程是源码明确实现了的。 ([worldmm.github.io][2])

---

## 1.3 视觉记忆 Visual Memory：怎么建

### 论文层面的定义

项目页把 visual memory 定义为：
一个 **hybrid visual store**，同时包含

* feature embeddings，用于语义检索；
* timestamped frames，用于精确视觉 grounding。 ([worldmm.github.io][2])

### 源码里的构建流程

`3_build_memory.sh` 里 visual memory 就一步：

* `preprocess/visual_memory/extract_visual_features.sh` ([GitHub][3])

它内部又调用：

* `extract_visual_features.py` 提取每个视频片段 embedding；
* 如果多 GPU，就分 split 并行处理；
* 最后 merge 成一个 `visual_embeddings.pkl`。 ([GitHub][13])

### visual feature 的具体提取方式

`extract_visual_features.py` 很关键，里面写得非常明白：

* 输入是 `A1_JAKE_30sec.json` 里的 `video_path`；
* 模型是 `VLM2Vec/VLM2Vec-V2.0`；
* `embedding_model.load_model(model_type="vision")`
* 每个视频片段调用 `encode_video([path], num_frames=num_frames, batch_size=1)`；
* 默认 `num_frames=16`；
* 输出是：

  * `Dict[video_path, np.ndarray]`
  * 最终存成 `visual_embeddings.pkl`。 ([GitHub][14])

所以 visual memory 的底层单元其实是：

**30 秒 clip + 该 clip 的视觉 embedding**

### visual memory 在运行时怎么组织

`VisualMemory` 里会：

* 先从 pickle 载入 `video_path -> embedding`
* 再载入 30 秒 clip 元数据
* 构造成 `VideoClipEntry`
* 按时间排序
* 在 `index(until_time)` 时，把 `end_time <= until_time` 且有 embedding 的 clip 放进 indexed set
* 构建 GPU tensor 作为检索库。 ([GitHub][15])

### visual 检索有两种模式

这是这篇论文非常实用的点，代码里写得很明确：

#### 模式 A：文本查询 → 视觉 embedding 检索

如果 query 是自然语言，就：

* `encode_vis_query(query)`
* 跟 clip embeddings 做 cosine similarity
* 取 top-k clip
* 再从这些 clip 里抽 frame。 ([GitHub][15])

#### 模式 B：时间范围查询 → 直接回看对应帧

如果 query 形如：

`DAY1 11:09:43 - DAY1 11:09:58`

就进入 `_retrieve_by_time_range(...)`：

* 找所有和这个时间段重叠的 clip；
* 只抽 overlap 区间内的帧；
* 默认按 1fps 抽；
* 超过上限则 uniform sampling。 ([GitHub][15])

这个设计非常关键：
它意味着 visual memory 不只是“向量库”，还保留了**可回溯的视觉证据通道**。

### visual 的一个例子

项目页 case study 提到一个典型错误：
仅依赖 episodic memory 时，模型可能只能知道“有 baked item”，但不知道到底是什么；这时 retrieval agent 会进一步去 visual memory，取回对应视频帧，帮助识别更细粒度的对象属性。 ([worldmm.github.io][2])

按源码流程，这件事会是：

1. 文本 query：
   “What baked item is on the table?”
2. visual memory 用 `encode_vis_query(query)` 做跨模态检索；
3. 找到最相近的 30 秒 clip；
4. 从 clip 中提取 1fps frame；
5. 把图像送给最终 QA 模型。 ([GitHub][15])

---

# 2. 检索智能体是如何生成的

## 2.1 不是训练出来一个单独 policy network，而是“LLM 驱动的迭代决策器”

论文页说的是：
retrieval agent 会**迭代地**决定该访问哪个 memory、发什么 query，并根据已有检索历史继续细化，直到判断信息足够。 ([worldmm.github.io][2])

源码里这个 agent 不是单独模型文件，而是嵌在 `WorldMemory.answer()` 里的决策循环。它依赖：

* `respond_llm_model`
* `PromptTemplateManager`
* prompt 模板 `memory_reasoning`。 ([GitHub][16])

## 2.2 检索智能体的输入是什么

每一轮它会给 LLM 一个 user message，大意是：

* 当前问题 `Query`
* 若是选择题，还会加 `Choices`
* 历史 round history
* 当前任务说明：

  * Step 1: decide search or answer
  * Step 2: if search, choose one memory and one search query ([GitHub][16])

所以 agent 的状态包含三部分：

1. **原问题**
2. **选项**
3. **之前轮次搜过什么、拿到了什么**

这已经是一个很标准的“带 history 的 agent state”。

## 2.3 它每轮输出什么

LLM 输出需要被 `_parse_reasoning_response()` 解析成 JSON，对应 dataclass 是：

* `ReasoningOutput`

  * `decision`: `"search"` or `"answer"`
  * `selected_memory`

    * `memory_type`
    * `search_query`
  * `reason`（可选） ([GitHub][16])

换句话说，每轮 policy 的动作空间就是：

* **动作 1：answer**
* **动作 2：search(memory_type, search_query)**

而 `memory_type` 必须是三选一：

* episodic
* semantic
* visual ([GitHub][16])

## 2.4 检索执行过程

如果 decision 是 `search`，代码会：

* `episodic` → `retrieve_from_episodic(...)`
* `semantic` → `retrieve_from_semantic(...)`
* `visual` → `retrieve_from_visual(...)` ([GitHub][16])

并且每个 memory 都有去重机制：

* episodic：按 `entry.text`
* semantic：按 `entry.id`
* visual：按 clip display key ([GitHub][16])

然后把本轮结果写入 `round_history`，再进入下一轮。

## 2.5 最终怎么回答

当 agent 决定 `answer`，或者达到最大轮数，就把前面累计的 context 发给 QA prompt：

* 文本型记忆（episodic / semantic）作为 text content；
* visual memory 作为 image content；
* 再让 `respond_llm_model.generate(...)` 给最终答案。 ([worldmm.github.io][2])

## 2.6 一个完整例子

假设问题是：

> What does Jake usually use to wipe kitchenware?

一个可能的 agent 过程会是：

### Round 1

* 决策：`search`
* 选 memory：`episodic`
* query：`wipe kitchenware`
  因为 agent 先想看看有没有直接事件证据。
  episodic 返回几条局部片段，比如某次拿 towel 擦盘子。 ([GitHub][16])

### Round 2

* 决策：`search`
* 选 memory：`semantic`
* query：`habit of wiping kitchenware`
  因为第一轮只找到某次局部事件，不足以回答“usually”。
  semantic memory 返回长期 consolidated triple，比如“Jake 通常用 towel 清洁餐具”。这正对应项目页说的 habitual behavior 场景。 ([worldmm.github.io][2])

### Round 3

* 决策：`answer`
* 用 episodic + semantic 一起回答。 ([GitHub][16])

再举一个视觉型问题：

> What kind of baked item is on the table?

可能的过程是：

### Round 1

* `search episodic`：先看文本里怎么描述

### Round 2

* 发现文本不够细
* `search visual`：拿对应 clip frame

### Round 3

* `answer`：利用图像回答具体是哪种 baked item。
  这和项目页 case study 完全一致。 ([worldmm.github.io][2])

## 2.7 它和“传统 RAG 检索器”的本质区别

传统 RAG 检索通常是：

* 先 encode query
* 再对一个固定库 top-k 检索
* 可能一次完成

WorldMM 的 retrieval agent 不是固定一步 top-k，而是：

* **先决定要不要继续搜**
* **再决定搜哪种记忆**
* **再决定用什么查询形式**
* **把结果作为下一轮决策上下文**

所以它更接近一个 **LLM-based controller / planner**，而不是普通 retriever。 ([worldmm.github.io][2])

---

# 3. WorldMM 与 VideoRAG（2502.01549）异同表

| 维度      | WorldMM (2512.02425)                                                  | VideoRAG (2502.01549)                                                                             | 相同点 / 关键差异                                                                                             |
| ------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 核心目标    | 面向长视频 QA，引入多记忆 + adaptive retrieval agent                             | 面向极长视频 RAG，强调 dual-channel 检索与无限长度视频处理                                                            | 都是长视频理解/问答框架，但 WorldMM 更“agentic”，VideoRAG 更“RAG infrastructure”。 ([arXiv][1])                         |
| 记忆/索引结构 | 三类记忆：episodic、semantic、visual                                         | 双通道：graph-based textual knowledge grounding + multimodal context encoding                         | WorldMM 是“三记忆分工”，VideoRAG 是“双通道索引”。 ([worldmm.github.io][2])                                           |
| 文本侧建模   | episodic 是多尺度 caption/event；semantic 是持续 consolidation 的知识图谱          | 文本侧重点是 graph-based textual knowledge grounding，强调跨视频语义关系                                          | 两者都有图/结构化文本层，但 WorldMM 更强调“长期记忆演化”，VideoRAG 更强调“跨视频知识索引”。 ([worldmm.github.io][2])                     |
| 视觉侧建模   | visual memory 保存 clip embedding + timestamped frames，可直接回看证据          | multimodal context encoding 保留视觉特征，用于多模态检索                                                        | 都保留视觉信息；WorldMM 更强调“回帧核实”，VideoRAG 更强调“多模态上下文编码”。 ([worldmm.github.io][2])                             |
| 时间建模    | episodic 明确使用 30s / 3min / 10min / 1h 多尺度；semantic 还会沿时间持续累积          | 论文摘要强调 extreme long-context 和 specialized multimodal retrieval，但公开摘要没有像 WorldMM 这样明确的“三类时间记忆演化”设计 | WorldMM 的时间层次更显式。 ([GitHub][6])                                                                        |
| 检索方式    | LLM 迭代决策：每轮决定 search / answer，再选 episodic / semantic / visual 与 query | 以 RAG 为核心，按 dual-channel 机制做多模态检索                                                                 | WorldMM 是“多轮 agent 检索”，VideoRAG 更偏“一体化检索框架”。 ([worldmm.github.io][2])                                  |
| 检索粒度    | 可以按问题动态切到事件、长期知识或视觉证据                                                 | 主要从文本图谱和多模态上下文中检索相关信息                                                                             | WorldMM 的检索粒度选择更灵活、更显式。 ([worldmm.github.io][2])                                                       |
| 检索控制器   | 明确有 retrieval agent                                                   | 公开摘要里未强调这种逐轮 memory-selection agent                                                               | 这是两篇最本质的区别之一。 ([worldmm.github.io][2])                                                                 |
| 源码依赖风格  | 复用了 EgoRAG / HippoRAG / VLM2Vec；episodic 用 HippoRAG，多尺度生成用 EgoRAG 组件  | 官方 repo 展示为完整 VideoRAG algorithm，README 强调 PyTorch 实现与多模态视频 RAG                                   | WorldMM 更像“组合多个成熟模块形成 agent memory system”；VideoRAG 更像“统一框架工程”。 ([GitHub][17])                         |
| 数据与任务   | README 当前主要展示 EgoLife / EgoLifeQA 处理流程                                | 论文提出 LongerVideos benchmark，160+ 视频、134+ 小时                                                       | 都做长视频 QA，但数据设定不同：WorldMM 更偏 egocentric life video；VideoRAG 更偏 general long-form videos。 ([GitHub][17]) |
| 优势场景    | 需要区分“局部事件 / 长期习惯 / 视觉细节证据”的复杂问题                                       | 超长视频、多视频统一索引与检索                                                                                   | WorldMM 适合多跳、需切 memory 的问题；VideoRAG 适合大规模长视频统一 RAG。 ([worldmm.github.io][2])                           |
| 潜在代价    | 多记忆构建更复杂，检索时有多轮 agent 开销                                              | 索引工程更集中，但对统一图谱/多模态编码质量依赖很高                                                                        | 两者都不轻量；WorldMM 更复杂在推理控制，VideoRAG 更复杂在底层统一索引。这个结论带有推断成分，但与两篇公开设计一致。 ([worldmm.github.io][2])            |

---

# 4. 你可以怎么理解 WorldMM 的整体流程

你可以把它概括成下面这个版本，这个概括基本是对的，而且比单纯“RAG + vector DB”更贴近论文：

**视频 / transcript / caption**
→ 生成 30 秒第一人称 caption
→ 构建多尺度 episodic memory（30s / 3min / 10min / 1h）
→ 从细粒度 caption 抽 episodic triples
→ 每 10 个 chunk 做 semantic extraction
→ 按时间做 semantic consolidation，形成持续更新的长期知识
→ 对每个 30 秒视频片段提 visual embedding，并保留回帧能力
→ 提问时，retrieval agent 多轮决定搜 episodic / semantic / visual 哪一类
→ 累积证据后生成答案。 ([GitHub][3])

---

# 5. 一句点评：它相对 VideoRAG 的真正新意在哪里

一句话说，**WorldMM 的创新点不只是“多数据库”，而是“把长视频记忆拆成事件、知识、视觉证据三种功能性记忆，并用 LLM agent 动态选择访问路径”**；而 VideoRAG 更像是一个把超长视频压缩进统一 RAG 索引体系的框架。 ([arXiv][1])

你下一步如果要做调研报告，我建议直接把这篇的系统图整理成这四层：

1. **预处理层**：caption / OpenIE / embedding
2. **记忆层**：episodic / semantic / visual
3. **控制层**：retrieval agent
4. **回答层**：multimodal QA

这样会比按“模块名堆砌”更清楚。

[1]: https://arxiv.org/abs/2512.02425 "[2512.02425] WorldMM: Dynamic Multimodal Memory Agent for Long Video Reasoning"
[2]: https://worldmm.github.io/ "WorldMM: Dynamic Multimodal Memory Agent for Long Video Reasoning"
[3]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/script/3_build_memory.sh "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/episodic_memory/generate_fine_caption.py "raw.githubusercontent.com"
[5]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/episodic/multiscale.py "raw.githubusercontent.com"
[6]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/eval/eval.py "raw.githubusercontent.com"
[7]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/episodic_memory/extract_episodic_triples.py "raw.githubusercontent.com"
[8]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/episodic/openie.py "raw.githubusercontent.com"
[9]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/semantic_memory/extract_semantic_triples.py "raw.githubusercontent.com"
[10]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/semantic/semantic_extraction.py "raw.githubusercontent.com"
[11]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/semantic_memory/consolidate_semantic_memory.py "raw.githubusercontent.com"
[12]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/semantic/semantic_consolidation.py "raw.githubusercontent.com"
[13]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/visual_memory/extract_visual_features.sh "raw.githubusercontent.com"
[14]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/preprocess/visual_memory/extract_visual_features.py "raw.githubusercontent.com"
[15]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/visual/memory.py "raw.githubusercontent.com"
[16]: https://raw.githubusercontent.com/wgcyeo/WorldMM/main/src/worldmm/memory/memory.py "raw.githubusercontent.com"
[17]: https://github.com/wgcyeo/WorldMM "GitHub - wgcyeo/WorldMM: [CVPR 2026] WorldMM: Dynamic Multimodal Memory Agent for Long Video Reasoning · GitHub"
