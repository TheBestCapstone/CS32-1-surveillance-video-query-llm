from pathlib import Path

from result_test_runner import run_result_tests


def run() -> Path:
    out = run_result_tests()
    return Path(out["result_md"])


if __name__ == "__main__":
    path = run()
    print(path)
