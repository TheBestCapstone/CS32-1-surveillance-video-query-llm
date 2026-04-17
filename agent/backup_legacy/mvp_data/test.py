import urllib.request
import urllib.parse
import json


def test_mock_server():
    base_url = "http://127.0.0.1:8000/api/v1/video/events"

    print(f"GET mock server (no query): {base_url}")
    print("-" * 50)

    try:
        req = urllib.request.Request(base_url)
        with urllib.request.urlopen(req) as response:
            result = response.read()
            data = json.loads(result.decode("utf-8"))

            print("OK")
            print(f"video_id: {data.get('video_id')}")
            print(f"event count: {len(data.get('events', []))}\n")

    except Exception as e:
        print(f"Request failed: {e}")
        print("Start mock_server.py in another terminal if needed.\n")


def test_with_query_param(video_id):
    url = f"http://127.0.0.1:8000/api/v1/video/events?video_id={urllib.parse.quote(video_id)}"

    print(f"GET with video_id: {url}")
    print("-" * 50)

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            result = response.read()
            data = json.loads(result.decode("utf-8"))
            print(f"OK video_id={data.get('video_id')}")
            events = data.get("events", [])
            print(f"event count: {len(events)}")
            if events:
                et = events[0].get("event_text") or events[0].get("event_text_cn", "N/A")
                print(f"first event_text: {et}\n")
            else:
                print("No events for this video.\n")
    except Exception as e:
        print(f"Request failed: {e}\n")


if __name__ == "__main__":
    test_mock_server()
    test_with_query_param("VIRAT_S_000200_00_000100_000171.mp4")
    test_with_query_param("VIRAT_S_050203_09_001000_001100.mp4")
    test_with_query_param("NOT_EXIST_VIDEO.mp4")
