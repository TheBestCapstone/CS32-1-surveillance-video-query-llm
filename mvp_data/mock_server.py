import json
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Video Events Mock Server")

# 获取当前目录下 json 文件的路径
MOCK_FILE_PATH = os.path.join(os.path.dirname(__file__), "video_events_mock.json")

@app.get("/api/v1/video/events")
def get_video_events(video_id: str = None):
    try:
        with open(MOCK_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # 如果数据是一个列表（包含多个视频的数据）
            if isinstance(data, list):
                if video_id:
                    # 查找请求中对应的 video_id
                    for item in data:
                        if item.get("video_id") == video_id:
                            return item
                    # 如果找不到对应的 video_id，返回空事件列表
                    return {"video_id": video_id, "events": []}
                else:
                    # 如果没有传 video_id，默认返回列表中的第一个视频数据
                    return data[0] if data else {}
            
            # 兼容旧版本：如果数据仍然是单个字典
            else:
                if video_id and data.get("video_id") != video_id:
                    return {"video_id": video_id, "events": []}
                return data
                
    except Exception as e:
        return {"error": f"Failed to load mock data: {str(e)}"}

if __name__ == "__main__":
    print("Starting Mock Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
