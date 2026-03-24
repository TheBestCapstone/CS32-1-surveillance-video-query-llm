# VideoRAG: Retrieval-Augmented Generation for Long Videos https://arxiv.org/abs/2502.01549 https://github.com/HKUDS/VideoRAG

优点（可采纳的地方）
1. 架构设计优秀，将视频分割为多个片段，并使用视频嵌入和向量检索来提高生成的准确性和效率。
2. rag shame 优秀可以照搬
3. 提供了合理的数据集以及评测标准。
缺点：
1. 视频分割的方法比较简单，可能会导致一些信息的丢失。
2. 视频分割的方式很单一，会导致冗余信息增多。
3. 全程用vllm进行切分，需要对耗时进行二次评估。

文章提出了一种方法，用于在长视频中进行检索增强生成（Retrieval-Augmented Generation，RAG）。该方法通过将视频分割为多个片段，并使用视频嵌入和向量检索来提高生成的准确性和效率。
索引框架:基于图结构的文本化 知识锚定,该组件将多模态信号转化为结构化的文本表示,同时保留语义关系与时间依赖性; 以及多模态上下文编码,该组件通过统一嵌入方式精细刻画视觉与文本信息间的跨模态交互。

.1.1 基于图结构的文本知识 grounding  本框架通过基于图结构的技术,将多模态视频内容转化为结构化的文本知识,从而提升索 引与检索效果。该转换过程涵盖两大关键模态:针对视觉内容,我们采用当前最先进的视 觉语言模型(VLM)生成全面的文本描述,以准确捕捉场景动态及上下文信息;针对音频 流,则利用高保真度的自动语音识别(ASR)技术提取带有时序对齐的语音内容。这种双 流处理机制确保了视觉语义与音频信息均被完整保留于我们的文本知识表征之中。
文本语义匹配。文本检索过程依托于我们构建的知识图谱 G,其中每个实体均包含一段源自相 关文本片段的描述性文字。该检索过程包含四个依次执行的步骤:(i)查询重构:在初始阶段, 我们利用大语言模型(LLM)将输入查询重写为陈述句形式,以优化其在后续实体匹配任务中 的表现。(ii)实体匹配:系统随后计算该重构后查询与知识图谱中各实体描述之间的相似度得 分,从而识别出最相关的实体及其关联的文本片段。(iii)片段筛选:在完成实体匹配后,我 们采用基于 GraphRAG [11]的方法对已检索到的文本片段进行排序,并甄选出最具相关性的片 段 Hq 。(iv)视频片段检索:最后,我们从所选文本片段中提取对应视频片段——由于每个文 本片段均描述了多个视频片段,因此最终形成我们的文本检索结果集 Sqt。







[17] Yanwei Li, Chengyao Wang, and Jiaya Jia. Llama-vid: An image is worth 2 tokens in large language models. In ECCV, pages 323–340. Springer, 2025.

[18] Yue Fan, Xiaojian Ma, Rujie Wu, Yuntao Du, Jiaqi Li, Zhi Gao, and Qing Li. Videoagent: A memory-augmented multimodal agent for video understanding. In ECCV, pages 75–92. Springer, 2025.

6 Weihan Wang, Zehai He, Wenyi Hong, Yean Cheng, Xiaohan Zhang, Ji Qi, Xiaotao Gu, Shiyu Huang, Bin Xu, Yuxiao Dong, et al. Lvbench: An extreme long video understanding benchmark. arXiv preprint arXiv:2406.08035, 2024.  
[7] Chaoyou Fu, Yuhan Dai, Yongdong Luo, Lei Li, Shuhuai Ren, Renrui Zhang, Zihan Wang, Chenyu Zhou, Yunhang Shen, Mengdan Zhang, et al. Video-mme: The first-ever comprehensive evaluation benchmark of multi-modal llms in video analysis. arXiv preprint arXiv:2405.21075, 2024.  
[8] Karttikeya Mangalam, Raiymbek Akshulakov, and Jitendra Malik. Egoschema: A diagnostic benchmark for very long-form video language understanding. NeurIPS, 36:46212–46244, 2023.
[11] Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, and Jonathan Larson. From local to global: A graph rag approach to query-focused summarization. arXiv preprint arXiv:2404.16130, 2024.  
[12] Zirui Guo, Lianghao Xia, Yanhua Yu, Tu Ao, and Chao Huang. Lightrag: Simple and fast retrieval-augmented generation. arXiv preprint arXiv:2410.05779, 2024.
[18] Yue Fan, Xiaojian Ma, Rujie Wu, Yuntao Du, Jiaqi Li, Zhi Gao, and Qing Li. Videoagent: A memory-augmented multimodal agent for video understanding. In ECCV, pages 75–92. Springer, 2025.  
[19] Hongjin Qian, Peitian Zhang, Zheng Liu, Kelong Mao, and Zhicheng Dou. Memorag: Moving towards next-gen rag via memory-inspired knowledge discovery. arXiv preprint arXiv:2409.05591, 2024.  
[20] Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, and Haofen Wang. Retrieval-augmented generation for large language models: A survey. arXiv preprint arXiv:2312.10997, 2023.
[26] Md Adnan Arefeen, Biplob Debnath, Md Yusuf Sarwar Uddin, and Srimat Chakradhar. irag: Advancing rag for videos with an incremental approach. In CIKM, pages 4341–4348, 2024.  
[27] Haoning Wu, Dongxu Li, Bei Chen, and Junnan Li. Longvideobench: A benchmark for long-context interleaved video-language understanding. arXiv preprint arXiv:2407.15754, 2024.  
[28] Keshigeyan Chandrasegaran, Agrim Gupta, Lea M Hadzic, Taran Kota, Jimming He, Cristóbal Eyzaguirre, Zane Durante, Manling Li, Jiajun Wu, and Li Fei-Fei. Hourvideo: 1-hour videolanguage understanding. arXiv preprint arXiv:2411.04998, 2024.  
[29] Yan Shu, Peitian Zhang, Zheng Liu, Minghao Qin, Junjie Zhou, Tiejun Huang, and Bo Zhao. Video-xl: Extra-long vision language model for hour-scale video understanding. arXiv preprint arXiv:2409.14485, 2024.
[32] Xiaohan Wang, Yuhui Zhang, Orr Zohar, and Serena Yeung-Levy. Videoagent: Long-form video understanding with large language model as agent. In ECCV, pages 58–76. Springer, 2025.  
[33] Yongdong Luo, Xiawu Zheng, Xiao Yang, Guilin Li, Haojia Lin, Jinfa Huang, Jiayi Ji, Fei Chao, Jiebo Luo, and Rongrong Ji. Video-rag: Visually-aligned retrieval-augmented long video comprehension. arXiv preprint arXiv:2411.13093, 2024.