import json

test_cases = [
    {"case_id": "TC01", "description": "Basic SQL search with specific object", "query": "Did you see any car in the database?", "expected_mode": "pure_sql", "min_results": 1, "max_results": 500},
    {"case_id": "TC02", "description": "SQL search with object and color", "query": "Are there any red cars?", "expected_mode": "pure_sql", "min_results": 1, "max_results": 200},
    {"case_id": "TC03", "description": "SQL search for non-existent color", "query": "Show me pink cars.", "expected_mode": "pure_sql", "min_results": 0, "max_results": 0},
    {"case_id": "TC04", "description": "Hybrid search with specific location", "query": "Is there a white car at the parking lot edge?", "expected_mode": "hybrid_search", "min_results": 0, "max_results": 50},
    {"case_id": "TC05", "description": "Hybrid search with specific location and action", "query": "Look for a person running on the sidewalk.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 100},
    {"case_id": "TC06", "description": "Hybrid search for specific intersection events", "query": "Any truck entering the intersection?", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 100},
    {"case_id": "TC07", "description": "SQL search with multiple colors", "query": "Show me red or blue cars.", "expected_mode": "pure_sql", "min_results": 1, "max_results": 500},
    {"case_id": "TC08", "description": "Hybrid search focusing on an action", "query": "Someone wandering near the greenbelt.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 100},
    {"case_id": "TC09", "description": "SQL search with specific object type", "query": "I need to find all the motorcycles.", "expected_mode": "pure_sql", "min_results": 1, "max_results": 200},
    {"case_id": "TC10", "description": "Hybrid search with complex action and color", "query": "A silver car reversing and entering the parking space area.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 50},
    {"case_id": "TC11", "description": "SQL search counting objects", "query": "How many bicycles are there?", "expected_mode": "pure_sql", "min_results": 1, "max_results": 200},
    {"case_id": "TC12", "description": "Hybrid search with obscure location", "query": "Did anyone walk through the back alley?", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 50},
    {"case_id": "TC13", "description": "SQL search for an obscure color", "query": "Are there any brown trucks?", "expected_mode": "pure_sql", "min_results": 0, "max_results": 50},
    {"case_id": "TC14", "description": "Hybrid search with missing object type", "query": "Something was parked steadily at the building entrance.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 100},
    {"case_id": "TC15", "description": "SQL search with general term", "query": "Show me all people in the database.", "expected_mode": "pure_sql", "min_results": 1, "max_results": 500},
    {"case_id": "TC16", "description": "Hybrid search for an interaction", "query": "Two people communicated near the parking lot entrance.", "expected_mode": "hybrid_search", "min_results": 0, "max_results": 50},
    {"case_id": "TC17", "description": "SQL search with boundary conditions", "query": "Find unknown color objects.", "expected_mode": "pure_sql", "min_results": 1, "max_results": 200},
    {"case_id": "TC18", "description": "Hybrid search for distant object", "query": "Distant pedestrian with unclear color details on the lawn.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 50},
    {"case_id": "TC19", "description": "SQL search for non-existent object type", "query": "Are there any airplanes?", "expected_mode": "pure_sql", "min_results": 0, "max_results": 0},
    {"case_id": "TC20", "description": "Hybrid search for sudden action", "query": "A motorcycle turned suddenly in the middle of the road.", "expected_mode": "hybrid_search", "min_results": 1, "max_results": 50}
]

with open("agent/test/result_cases.json", "w", encoding="utf-8") as f:
    json.dump(test_cases, f, ensure_ascii=False, indent=2)

print("Created 20 English test cases.")
