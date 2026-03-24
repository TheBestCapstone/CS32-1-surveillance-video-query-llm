import urllib.request
import urllib.parse
import json

def test_mock_server():
    base_url = "http://127.0.0.1:8000/api/v1/video/events"
    
    print(f"正在请求 Mock 服务器 (不带参数): {base_url}")
    print("-" * 50)
    
    try:
        req = urllib.request.Request(base_url)
        with urllib.request.urlopen(req) as response:
            result = response.read()
            data = json.loads(result.decode('utf-8'))
            
            print("✅ 请求成功！")
            print(f"📌 默认返回的视频 ID: {data.get('video_id')}")
            print(f"📊 获取到事件数量: {len(data.get('events', []))} 个\n")
                
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        print("请确保你已经在一个终端中运行了 mock_server.py\n")

def test_with_query_param(video_id):
    url = f"http://127.0.0.1:8000/api/v1/video/events?video_id={urllib.parse.quote(video_id)}"
    
    print(f"正在测试带参数的请求: {url}")
    print("-" * 50)
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            result = response.read()
            data = json.loads(result.decode('utf-8'))
            print(f"✅ 请求成功！视频 ID: {data.get('video_id')}")
            events = data.get('events', [])
            print(f"📊 获取到事件数量: {len(events)} 个")
            if events:
                print(f"🔍 示例事件(第一条): {events[0].get('event_text_cn', 'N/A')}\n")
            else:
                print("⚠️ 该视频没有事件数据。\n")
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}\n")

if __name__ == "__main__":
    # 测试默认请求
    test_mock_server()
    
    # 测试原始提供的 video_id
    test_with_query_param("VIRAT_S_000200_00_000100_000171.mp4")
    
    # 测试新生成的随机 video_id
    test_with_query_param("VIRAT_S_050203_09_001000_001100.mp4")
    
    # 测试一个不存在的 video_id
    test_with_query_param("NOT_EXIST_VIDEO.mp4")
