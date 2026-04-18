import json
import sqlite3
from pathlib import Path

def create_and_populate_db():
    json_path = Path("agent/mock_data/data/video_events_mock.json")
    db_path = Path("data/SQLite/episodic_events.sqlite")
    
    if not json_path.exists():
        print(f"Error: {json_path} does not exist.")
        return

    # Dictionary for translations
    color_map = {
        '红': 'Red', '紫': 'Purple', '银灰': 'Silver', '黑': 'Black', '黄': 'Yellow', 
        '绿': 'Green', '棕': 'Brown', '蓝': 'Blue', '不确定': 'Unknown', '粉': 'Pink', 
        '橙': 'Orange', '白': 'White'
    }
    
    zone_map = {
        '十字路口': 'Intersection', 
        '人行道': 'Sidewalk', 
        '后巷': 'Back Alley', 
        '停车场边缘步行区': 'Parking Lot Edge Walkway', 
        '停车场入口附近': 'Near Parking Lot Entrance', 
        '停车场边缘/车道旁': 'Parking Lot Edge/Driveway', 
        '停车场边缘靠近道路': 'Parking Lot Edge Near Road', 
        '停车位区域': 'Parking Space Area', 
        '绿化带旁': 'Near Greenbelt', 
        '草坪': 'Lawn', 
        '停车场内侧': 'Inner Parking Lot', 
        '大楼入口': 'Building Entrance', 
        '道路中央': 'Middle of Road', 
        '马路对侧停车位': 'Parking Space Across Street'
    }

    # Helper function to translate complex notes
    def translate_note(note):
        # Basic translations based on observed patterns
        note = note.replace('路过并进入', 'Passed by and entered ')
        note = note.replace('快速驶入后趋于停靠', 'Drove in quickly and parked')
        note = note.replace('行人在', 'Pedestrian at ')
        note = note.replace('转向并进入', 'Turned and entered ')
        note = note.replace('倒车并进入', 'Reversed and entered ')
        note = note.replace('缓慢驶出并进入', 'Drove out slowly and entered ')
        note = note.replace('加速驶离并进入', 'Sped away and entered ')
        note = note.replace('快速驶入并进入', 'Drove in quickly and entered ')
        
        note = note.replace('徘徊', 'wandered')
        note = note.replace('搬运物品', 'carried items')
        note = note.replace('使用手机', 'used mobile phone')
        note = note.replace('快步走过', 'walked quickly')
        note = note.replace('短暂停留', 'stayed briefly')
        note = note.replace('奔跑', 'ran')
        note = note.replace('交流', 'communicated')
        note = note.replace('推车', 'pushed a cart')
        
        note = note.replace('远距离行人，颜色细节不清', 'Distant pedestrian, color details unclear')
        note = note.replace('静止停放，几乎无明显位移', 'Stationary parking, almost no movement')
        note = note.replace('摩托车推行', 'Pushed motorcycle')
        note = note.replace('摩托车骑行通过', 'Rode motorcycle through')
        note = note.replace('摩托车停放', 'Motorcycle parked')
        note = note.replace('摩托车突然转向', 'Motorcycle turned suddenly')
        note = note.replace('自行车停放', 'Bicycle parked')
        note = note.replace('自行车推行', 'Pushed bicycle')
        note = note.replace('自行车骑行通过', 'Rode bicycle through')
        note = note.replace('自行车突然转向', 'Bicycle turned suddenly')
        note = note.replace('短暂停留，几乎无移动', 'Stayed briefly, almost no movement')
        note = note.replace('远处行人，动作明显，可能在步行/驶入停车场区域', 'Distant pedestrian with obvious movements, possibly walking/entering parking area')
        note = note.replace('快速移动并转入停车位附近', 'Moved quickly and turned near parking space')
        note = note.replace('驶入后基本停稳', 'Parked steadily after entering')
        note = note.replace('快速驶入并进入停车区域', 'Drove in quickly and entered parking area')

        # Translate zone parts within notes
        for k, v in zone_map.items():
            note = note.replace(k, v.lower())

        return note.capitalize()

    # Ensure target directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
        
    print(f"Creating new English database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table WITHOUT time fields
    cursor.execute("""
    CREATE TABLE episodic_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT,
        camera_id TEXT,
        track_id TEXT,
        object_type TEXT,
        object_color_en TEXT,
        scene_zone_en TEXT,
        appearance_notes_en TEXT,
        event_summary_en TEXT
    )
    """)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    all_events = []
    for video in data:
        for event in video.get("events", []):
            track_id = event.get("entity_hint", "").replace("track_id=", "")
            
            obj_type = event.get("object_type", "")
            obj_color_cn = event.get("object_color_cn", "")
            scene_zone_cn = event.get("scene_zone_cn", "")
            appearance_notes_cn = event.get("appearance_notes_cn", "")
            
            # Translate
            obj_color_en = color_map.get(obj_color_cn, "Unknown")
            scene_zone_en = zone_map.get(scene_zone_cn, "Unknown Area")
            appearance_notes_en = translate_note(appearance_notes_cn)
            
            # Reconstruct English Summary
            event_summary_en = f"A {obj_color_en.lower()} {obj_type.lower()} was at {scene_zone_en.lower()}. Action: {appearance_notes_en.lower()}"
            
            all_events.append((
                event.get("video_id", ""),
                event.get("camera_id", ""),
                track_id,
                obj_type,
                obj_color_en,
                scene_zone_en,
                appearance_notes_en,
                event_summary_en
            ))
            
    print(f"Inserting {len(all_events)} records...")
    cursor.executemany("""
        INSERT INTO episodic_events (
            video_id, camera_id, track_id, 
            object_type, object_color_en, scene_zone_en, 
            appearance_notes_en, event_summary_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, all_events)
    
    conn.commit()
    conn.close()
    print("Database generation complete!")

if __name__ == "__main__":
    create_and_populate_db()
