import json

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

def translate_note(note):
    note = note.replace('路过并进入', 'Passed by and entered ')
    note = note.replace('快速驶入后趋于停靠', 'Drove in quickly and parked')
    note = note.replace('行人在', 'Pedestrian at ')
    note = note.replace('在人行道', 'at sidewalk ')
    note = note.replace('在十字路口', 'at intersection ')
    note = note.replace('人行道', 'sidewalk ')
    note = note.replace('十字路口', 'intersection ')
    note = note.replace('行人', 'Pedestrian ')
    
    note = note.replace('sidewalk', 'sidewalk ')
    note = note.replace('intersection', 'intersection ')
    note = note.replace('转向并进入', 'Turned and entered ')
    note = note.replace('倒车并进入', 'Reversed and entered ')
    note = note.replace('缓慢驶出并进入', 'Drove out slowly and entered ')
    note = note.replace('加速驶离并进入', 'Sped away and entered ')
    note = note.replace('快速驶入并进入', 'Drove in quickly and entered ')
    
    note = note.replace('徘徊', ' wandered')
    note = note.replace('搬运物品', ' carried items')
    note = note.replace('使用手机', ' used mobile phone')
    note = note.replace('快步走过', ' walked quickly')
    note = note.replace('短暂停留', ' stayed briefly')
    note = note.replace('奔跑', ' ran')
    note = note.replace('交流', ' communicated')
    note = note.replace('推车', ' pushed a cart')
    
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

    for k, v in zone_map.items():
        note = note.replace(k, f" {v.lower()} ")

    note = note.replace('  ', ' ')
    return note.strip().capitalize()

with open('agent/mock_data/data/video_events_mock_en.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for video in data:
    for event in video.get('events', []):
        if event.get('object_type') == 'car' and 'parking lot' in event.get('scene_zone_en', '').lower():
            event['object_color_en'] = 'White'
            if 'event_summary_en' in event:
                event['event_summary_en'] = event['event_summary_en'].replace('silver', 'white').replace('red', 'white').replace('green', 'white').replace('black', 'white').replace('yellow', 'white').replace('brown', 'white').replace('orange', 'white')

with open('agent/mock_data/data/video_events_mock_en.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

for video in data:
    for event in video.get('events', []):
        if 'object_color_cn' in event:
            event['object_color_en'] = color_map.get(event['object_color_cn'], "Unknown")
            del event['object_color_cn']
            
        if 'scene_zone_cn' in event:
            event['scene_zone_en'] = zone_map.get(event['scene_zone_cn'], "Unknown Area")
            del event['scene_zone_cn']
            
        if 'appearance_notes_cn' in event:
            event['appearance_notes_en'] = translate_note(event['appearance_notes_cn'])
            del event['appearance_notes_cn']
            
        if 'event_text_cn' in event:
            obj_type = event.get('object_type', 'unknown')
            color = event.get('object_color_en', 'Unknown')
            zone = event.get('scene_zone_en', 'Unknown Area')
            notes = event.get('appearance_notes_en', '')
            event['event_summary_en'] = f"A {color.lower()} {obj_type.lower()} was at {zone.lower()}. Action: {notes.lower()}"
            del event['event_text_cn']

with open('agent/mock_data/data/video_events_mock_en.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully translated mock data and saved to video_events_mock_en.json")
