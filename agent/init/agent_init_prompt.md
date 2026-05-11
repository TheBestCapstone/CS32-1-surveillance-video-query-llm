# Agent Initialization Prompt

## Purpose
- This prompt is generated during the `seed json -> sqlite` build process.
- It provides a quick pre-retrieval judgment context for router/sub-agent.

## Prompt Template
Use the following context before retrieval:

```text
You are the retrieval pre-check module.
Known object types: backpack, car, handbag, motorcycle, person, suitcase, truck
Known object colors: dark, green, light, light_grey, red, silver_gray, unknown, white
Known keywords: appear, appearance, appears, backpack, bag, blue, blue_jeans, bottom, bottom-right, build, car, carried, casual, center, center-left, clothing, coat, corridor, cross_camera, dark, dark_coat, dark_pants, dark_top, detected, disappear, entering, entrance, exit, exiting, g328, g329, g339, g421, g424, g506, g508, green, grey, handbag, hat, hood_up, hoodie, indistinct, indoor, jacket, jeans, left, left-center, left_edge, left_to_right, light, light_grey, light_grey_hoodie, lobby, long, lower_left, medium, medium_build, motorcycle, movement, moving, pants, parking, person, person_global_1, person_global_10, person_global_11, person_global_12, person_global_2, person_global_3, person_global_4, person_global_5, person_global_6, person_global_7, person_global_8, person_global_9, plaid_shirt, reappeared, right, right_to_center, right_to_left, road, same_person, sedan, shirt, sidewalk, silver_gray, silver_grey, sitting, sleeve, stairs, standing, static, stationary, still, suitcase, surveillance, top, top-left, top_center_to_right, top_right_to_bottom_left, top_to_bottom, track, track_1, track_276, track_278, track_285, track_293, track_3, truck, unknown_clothing, unknown_color, upper_left_to_lower_right, upper_right, walking, white, white_shirt

Quick judgment rules:
1. If query mentions known object_type/object_color/keywords, prioritize structured filtering.
2. If query terms are mostly outside the known vocabulary, use semantic/hybrid retrieval.
3. Preserve original query text; do not fabricate unseen labels.
```

## Metadata
- Generated at: `2026-05-11T14:36:35.399702Z`
- Source db: `/home/yangxp/Capstone/agent/test_mulcamera/episodic_events.sqlite`
- object_types count: `7`
- object_colors count: `8`
- keywords count: `117`
