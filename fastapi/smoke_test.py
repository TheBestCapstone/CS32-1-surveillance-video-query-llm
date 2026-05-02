from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen


def _post_json(url: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _select_database(base_url: str, database_id: str, timeout: int) -> dict:
    return _post_json(
        f"{base_url}/api/v1/databases/select",
        {"database_id": database_id},
        timeout,
    )


def _stream_sse(url: str, payload: dict, timeout: int) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8").rstrip()
            if line:
                print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight smoke test for the FastAPI wrapper.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="FastAPI base URL.")
    parser.add_argument(
        "--query",
        default="two white police cars flashing roof lights",
        help="Query text sent to the API.",
    )
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout in seconds.")
    parser.add_argument("--stream", action="store_true", help="Use the SSE stream endpoint.")
    parser.add_argument(
        "--database-id",
        default="configured-default",
        help="Database id selected before querying.",
    )
    args = parser.parse_args()

    selection = _select_database(args.base_url, args.database_id, args.timeout)
    print(json.dumps(selection, ensure_ascii=False, indent=2))

    payload = {
        "query": args.query,
        "include_rows": False,
        "top_k_rows": 3,
    }
    if args.stream:
        _stream_sse(f"{args.base_url}/api/v1/query/stream", payload, args.timeout)
        return

    result = _post_json(f"{args.base_url}/api/v1/query", payload, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
