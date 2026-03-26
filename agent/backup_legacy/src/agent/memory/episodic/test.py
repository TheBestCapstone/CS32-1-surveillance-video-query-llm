import os
import sys
from pathlib import Path
import lancedb

# 添加项目根目录到 Python Path
# __file__ = Capstone/agent/backup_legacy/src/agent/memory/episodic/test.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
CAPSTONE_DIR = BASE_DIR.parent.parent
sys.path.append(str(CAPSTONE_DIR))

from video.indexing.embedder import get_qwen_embedding

class EventRetriever:
    def __init__(self):
        # LanceDB 路径
        db_path = str(BASE_DIR / "src" / "agent" / "memory" / "episodic" / "lancedb")
        self.db = lancedb.connect(db_path)
        self.table_name = "episodic_events"
        
    def get_table(self):
        if self.table_name in self.db.list_tables():
            return self.db.open_table(self.table_name)
        return None

    def structured_search(self, 
                          video_id: str = None, 
                          object_type: str = None,
                          scene_zone_cn: str = None,
                          min_duration: float = None,
                          start_time_after: float = None,
                          limit: int = 10):
        tbl = self.get_table()
        if not tbl:
            return []
            
        filters = []
        if video_id:
            filters.append(f"video_id = '{video_id}'")
        if object_type:
            filters.append(f"object_type = '{object_type}'")
        if scene_zone_cn:
            filters.append(f"scene_zone_cn = '{scene_zone_cn}'")
        if min_duration is not None:
            filters.append(f"duration >= {min_duration}")
        if start_time_after is not None:
            filters.append(f"start_time >= {start_time_after}")
            
        query = tbl.search()
        if filters:
            query = query.where(" AND ".join(filters))
            
        try:
            results = query.limit(limit).to_list()
            # Sort by start_time ascending as in original SQLite logic
            results.sort(key=lambda x: x.get('start_time', 0))
            return results
        except Exception as e:
            print(f"Structured search error: {e}")
            return []

    def hybrid_event_search(self, 
                            query_text: str, 
                            top_k: int = 5,
                            video_id: str = None,
                            object_type: str = None,
                            scene_zone_cn: str = None,
                            start_time_after: float = None,
                            end_time_before: float = None):
        try:
            query_vector = get_qwen_embedding(query_text)
        except Exception as e:
            print(f"获取 Query Embedding 失败: {e}")
            return []

        tbl = self.get_table()
        if not tbl:
            return []

        filters = []
        if video_id:
            filters.append(f"video_id = '{video_id}'")
        if object_type:
            filters.append(f"object_type = '{object_type}'")
        if scene_zone_cn:
            filters.append(f"scene_zone_cn = '{scene_zone_cn}'")
        if start_time_after is not None:
            filters.append(f"start_time >= {start_time_after}")
        if end_time_before is not None:
            filters.append(f"end_time <= {end_time_before}")
            
        query = tbl.search(query_vector)
        if filters:
            query = query.where(" AND ".join(filters))
            
        try:
            results = query.limit(top_k).to_list()
            # LanceDB adds _distance field automatically
            for r in results:
                if '_distance' in r:
                    r['distance'] = r['_distance']
            return results
        except Exception as e:
            print(f"Hybrid search error: {e}")
            return []

def run_tests():
    # 尝试加载 .env
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
    except Exception:
        pass
        
    # 确保环境变量存在
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("❌ 错误：请先设置环境变量 DASHSCOPE_API_KEY")
        print("执行: export DASHSCOPE_API_KEY='你的百炼API_KEY'")
        return

    print("✅ 环境变量检查通过，初始化检索器...")
    retriever = EventRetriever()

    # =================================================================
    # 场景 1: 纯结构化数据检索测试 (不经过大模型，极快)
    # =================================================================
    print("\n" + "="*50)
    print("场景 1: 纯结构化数据检索测试 (Structured Search)")
    print("="*50)
    
    # 1.1 找出停留时间超过 100 秒的事件
    print("\n--- 1.1 查找长时间事件 (duration >= 100) ---")
    long_events = retriever.structured_search(min_duration=100.0, limit=3)
    for res in long_events:
        print(f"ID: {res['event_id']:<5} | 时长: {res['duration']:.1f}s | 摘要: {res['event_summary_cn']}")

    # 1.2 在特定场景 (十字路口) 找卡车
    print("\n--- 1.2 组合条件查找 (scene_zone='十字路口', object_type='truck') ---")
    truck_events = retriever.structured_search(scene_zone_cn="十字路口", object_type="truck", limit=3)
    for res in truck_events:
        print(f"ID: {res['event_id']:<5} | 场景: {res['scene_zone_cn']} | 摘要: {res['event_summary_cn']}")

    # 1.3 指定视频、指定时间点之后的事件
    print("\n--- 1.3 时间轴查找 (video_id='VIRAT_S_000001_00_000000_000500.mp4', start_time >= 1000) ---")
    timeline_events = retriever.structured_search(
        video_id="VIRAT_S_000001_00_000000_000500.mp4", 
        start_time_after=1000.0, 
        limit=3
    )
    for res in timeline_events:
        print(f"ID: {res['event_id']:<5} | 发生时间: {res['start_time']}s | 摘要: {res['event_summary_cn']}")


    # =================================================================
    # 场景 2: 纯向量语义检索测试 (跨模态意图匹配)
    # =================================================================
    print("\n" + "="*50)
    print("场景 2: 纯向量语义检索测试 (Semantic Search)")
    print("="*50)
    
    query_1 = "寻找停放的绿色的汽车"
    print(f"\n--- 查询词: '{query_1}' ---")
    results = retriever.hybrid_event_search(query_1, top_k=3)
    for idx, res in enumerate(results):
        print(f"[{idx+1}] 距离: {res['distance']:.4f} | 视频: {res['video_id']}")
        print(f"    摘要: {res['event_summary_cn']}")


    # =================================================================
    # 场景 3: 混合检索测试 (SQL结构化过滤 + Vector相似度排序)
    # =================================================================
    print("\n" + "="*50)
    print("场景 3: 复杂条件混合检索测试 (Hybrid Search)")
    print("="*50)
    
    # 3.1 在特定视频里，寻找“奔跑”的“人”
    query_2 = "有人在跑得很急"
    vid_filter = "VIRAT_S_000006_00_000000_000500.mp4"
    print(f"\n--- 3.1 视频级定位 ---")
    print(f"查询词: '{query_2}'")
    print(f"过滤条件: object_type='person', video_id='{vid_filter}'")
    
    results = retriever.hybrid_event_search(
        query_2, 
        top_k=3, 
        object_type="person",
        video_id=vid_filter
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] 距离: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    摘要: {res['event_summary_cn']}")

    # 3.2 在“停车场入口”区域，寻找“红色”的“异常徘徊行为”
    # 注意：我们这里故意用比较模糊的查询词 "一直走来走去"，配合结构化限定区域
    query_3 = "一直走来走去"
    zone_filter = "停车场入口附近"
    print(f"\n--- 3.2 区域级行为分析 ---")
    print(f"查询词: '{query_3}'")
    print(f"过滤条件: scene_zone_cn='{zone_filter}'")
    
    results = retriever.hybrid_event_search(
        query_3, 
        top_k=3, 
        scene_zone_cn=zone_filter
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] 距离: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    摘要: {res['event_summary_cn']}")

    # 3.3 结合时间窗口的向量检索
    query_4 = "有人骑自行车经过"
    vid_time_filter = "VIRAT_S_000001_00_000000_000500.mp4"
    start_t = 500.0
    end_t = 1500.0
    print(f"\n--- 3.3 时间窗口级语义检索 ---")
    print(f"查询词: '{query_4}'")
    print(f"过滤条件: video_id='{vid_time_filter}', 时间区间: {start_t}s - {end_t}s")
    
    results = retriever.hybrid_event_search(
        query_4, 
        top_k=3, 
        video_id=vid_time_filter,
        start_time_after=start_t,
        end_time_before=end_t
    )
    for idx, res in enumerate(results):
        print(f"[{idx+1}] 距离: {res['distance']:.4f} | ID: {res['event_id']}")
        print(f"    发生时间: {res['start_time']}s - {res['end_time']}s")
        print(f"    摘要: {res['event_summary_cn']}")

if __name__ == "__main__":
    run_tests()
