"""base.py — 测试基座共享工具（B3 · 零外部依赖）

提供统一的 PASS/FAIL 断言；新测试文件只需 `from base import check` 即可
复用，无需 pytest。运行方式与 test_smoke.py 一致：直接 `python xxx.py`。
"""
import os
import sys

# 让 import 能找到 src 下的模块
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "src"))


def check(name: str, cond: bool):
    """断言 cond 为真；失败抛 AssertionError 并中断当前 main()。"""
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}")
    if not cond:
        raise AssertionError(name)
