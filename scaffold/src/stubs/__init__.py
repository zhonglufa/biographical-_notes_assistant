"""
stubs/__init__.py — A 层接口桩自动发现与注册

机制：扫描本包内所有 *.py（除 __init__/_TEMPLATE/core），import 各模块的
ENDPOINTS 列表，汇总进全局 API_STUB。

因此「新增一个模块 = 新建一个 stubs/<module>.py，无需改任何共享文件」，
天然支持并行子代理各写各的模块、零冲突。

落地索引见 design/contracts/implementation-index.md
"""
import importlib
import os
import sys

# 让 contract_runtime 可 import（与 core.py 同目录处理）
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_SRC_DIR))

from .core import ApiStub, Endpoint, validate_payload  # 暴露给各模块复用

API_STUB = ApiStub()

# 自动发现模块文件（排除基础设施文件）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXCLUDED = {"__init__.py", "_TEMPLATE.py", "core.py"}
_MODULE_FILES = sorted(
    f for f in os.listdir(_THIS_DIR)
    if f.endswith(".py") and f not in _EXCLUDED
)

for _f in _MODULE_FILES:
    _mod_name = os.path.splitext(_f)[0]
    _mod = importlib.import_module("." + _mod_name, __package__)
    for _ep in getattr(_mod, "ENDPOINTS", []):
        API_STUB.register(_ep)

__all__ = ["API_STUB", "Endpoint", "ApiStub", "validate_payload"]
