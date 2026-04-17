import json
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Video Events Mock Server")

# Path to bundled mock JSON (same directory as this server)
MOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "video_events_mock.json")

@app.get("/api/v1/video/events")
def get_video_events(video_id: str = None):
    try:
        with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            if isinstance(data, list):
                if video_id:
                    for item in data:
                        if item.get("video_id") == video_id:
                            return item
                    return {"video_id": video_id, "events": []}
                else:
                    return data[0] if data else {}

            else:
                if video_id and data.get("video_id") != video_id:
                    return {"video_id": video_id, "events": []}
                return data
                
    except Exception as e:
        return {"error": f"Failed to load mock data: {str(e)}"}

if __name__ == "__main__":
    print("Starting Mock Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
