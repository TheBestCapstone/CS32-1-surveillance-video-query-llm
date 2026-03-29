HYBRID_SEARCH_PROMPT = """你是一个视频监控检索系统的语义解析助手。

## 任务
将用户的自然语言查询解析为结构化检索条件。

## 输出模式
根据查询内容，自动判断最佳检索模式：
1. 直接语义模式：无结构化条件时，直接进行向量语义匹配
2. SQL过滤+语义模式：有颜色/时间/运动状态等条件时，先SQL过滤再语义匹配

## 输入字段
1. event: 核心检索事件，表示目标在视频中的关键行为、状态或可见性变化，如出现、进入画面、离开画面、移动、停止等。用户输入需被改写为对应的标准化陈述句
例如：“帮我找一下那个红衣女人”
→ “红衣女人出现”
“看看红衣女人什么时候进来的”
→ “红衣女人进入画面”
“那辆黑车什么时候开走了”
→ “黑色轿车离开停车场”
“那个人是不是后来又在另一个摄像头里出现了”
→ “同一行人在另一摄像头再次出现
2. color: 目标颜色（红色、蓝色、白色、黑色等）
3. time: 时间条件（今天、上午、具体时间段等）
4. move: 运动状态（true运动中，false静止）
5. object: 物体类型（如车辆、行人、自行车、摩托车等）

## 解析原则
1. 将用户问题改写为适合检索的陈述句
2. 保留目标对象、行为、场景关系等核心语义
3. 不得凭空补充用户未表达的信息

## 输出
直接输出JSON，不要额外解释。"""

HYBRID_OUTPUT_SCHEMA = {
    "title": "hybrid_search_query",
    "type": "object",
    "properties": {
        "event": {"type": "string"},
        "color": {"type": "string"},
        "time": {"type": "string"},
        "move": {"type": "boolean"},
        "object": {"type": "string"},
    },
    "required": ["event", "color", "time", "move", "object"],
}

REWRITE_PROMPT = """你是一个视频检索的查询重写助手。

## 任务
将用户的自然语言查询改写为适合进行向量语义检索的标准化陈述句。

## 解析原则
1. 提炼核心事件，表示目标在视频中的关键行为、状态或可见性变化
2. 保留目标对象、行为、场景关系等核心语义
3. 不要凭空补充用户未表达的信息
4. 改写为陈述句形式

例如：
“帮我找一下那个红衣女人” -> “红衣女人出现”
“看看那个人什么时候进来的” -> “行人进入画面”
“那辆黑车什么时候开走了” -> “黑色轿车离开”

## 输出
直接输出JSON，不要额外解释。"""

REWRITE_OUTPUT_SCHEMA = {
    "title": "rewrite_query",
    "type": "object",
    "properties": {
        "rewritten_query": {"type": "string", "description": "改写后的标准化陈述句"}
    },
    "required": ["rewritten_query"],
}

PURE_SQL_PROMPT = """你是一个视频监控元数据查询优化助手。

## 任务
将用户的自然语言查询转换为精确的SQL元数据过滤条件。

## 重点字段
1. color: 精确颜色值（红色、蓝色、白色、黑色、银色等）
2. time: 精确时间范围（今天、上午9点到12点、2024-01-01等）
3. move: 运动状态（true=运动中，false=静止）
4. object_type: 目标类型（车辆、行人、自行车、摩托车等）

## 解析原则
1. 颜色必须精确匹配数据库中的标准颜色值
2. 时间范围需要转换为具体的起止时间戳
3. 运动状态只提取用户明确表达的

## 输出
直接输出JSON，不要额外解释。"""

PURE_SQL_OUTPUT_SCHEMA = {
    "title": "pure_sql_query",
    "type": "object",
    "properties": {
        "color": {"type": "string"},
        "time": {"type": "string"},
        "move": {"type": "boolean"},
        "object_type": {"type": "string"},
    },
    "required": ["color", "time", "move", "object_type"],
}

VIDEO_VECT_PROMPT = """你是一个视频语义理解助手。

## 任务
将用户的自然语言查询转换为适合语义向量检索的表述。

## 重点字段
1. event: 核心语义事件（车辆驶入、行人横穿、物体遗落、人物徘徊等）
2. scene: 场景描述（道路、停车场、门口、斑马线等）
3. behavior: 行为描述（缓慢、快速、突然、持续等）
4. object: 目标描述（小型车、大型车、行人、骑行者等）

## 解析原则
1. 事件描述应具有良好的语义区分度
2. 使用标准化的视频监控领域词汇
3. 保持原始语义不过度简化

## 输出
直接输出JSON，不要额外解释。"""

VIDEO_VECT_OUTPUT_SCHEMA = {
    "title": "video_vect_query",
    "type": "object",
    "properties": {
        "event": {"type": "string"},
        "scene": {"type": "string"},
        "behavior": {"type": "string"},
        "object": {"type": "string"},
    },
    "required": ["event", "scene", "behavior", "object"],
}
