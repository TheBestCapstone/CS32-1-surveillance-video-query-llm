"""run_all_tests.py — 一键运行全部多摄像头测试。

用法:
    cd agent/test/多摄像头测试
    conda run -n capstone python run_all_tests.py

输出目录: output/
"""

from __future__ import annotations

import importlib
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "lib"))

from utils import OUTPUT_DIR, setup_env

TEST_MODULES = [
    "test_01_classification",
    "test_02_fusion",
    "test_03_ge_branch",
    "test_04_e2e",
    "test_05_performance",
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    setup_env()

    started = datetime.now()
    print(f"{'='*60}")
    print(f"  多摄像头管道全量测试")
    print(f"  开始时间: {started.isoformat()}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}")
    print()

    for i, mod_name in enumerate(TEST_MODULES, 1):
        print(f"[{i}/{len(TEST_MODULES)}] 运行 {mod_name}...")
        try:
            mod = importlib.import_module(mod_name)
            mod.main()
        except Exception as exc:
            print(f"  ❌ {mod_name} 失败: {exc}")
            import traceback
            traceback.print_exc()
        print()

    elapsed = (datetime.now() - started).total_seconds()
    print(f"{'='*60}")
    print(f"  全量测试完成，总耗时 {elapsed:.1f}s")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  文件列表:")
    for f in sorted(OUTPUT_DIR.glob("*")):
        size = f.stat().st_size
        print(f"    {f.name} ({size:,} bytes)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
