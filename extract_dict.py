import json

with open('agent/mock_data/data/video_events_mock.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

colors = set()
zones = set()
notes = set()

for video in data:
    for event in video.get('events', []):
        colors.add(event.get('object_color_cn', ''))
        zones.add(event.get('scene_zone_cn', ''))
        notes.add(event.get('appearance_notes_cn', ''))

print("Colors:", colors)
print("Zones:", zones)
print("Notes:", notes)
