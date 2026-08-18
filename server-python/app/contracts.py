"""contracts.py — 复用设计层零依赖契约校验器（fail-closed 真相源）

server-python 不重新造校验轮子：直接 import design/contracts/validate_contracts.py
的纯标准库 validate()，对任意「响应 payload」做机器可读 schema 校验。
所有 B 层成功响应在返回前必过 validate_payload()；失败即视为实现偏离契约 → 500 暴露。
"""
from __future__ import annotations

import os
import sys

# 上溯到仓库根，把 design/contracts 加入搜索路径，复用既有校验器（零外部依赖）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONTRACTS_DIR = os.path.join(_REPO_ROOT, "design", "contracts")
if _CONTRACTS_DIR not in sys.path:
    sys.path.insert(0, _CONTRACTS_DIR)

import validate_contracts  # noqa: E402  (standalone module，无第三方依赖)


def load_schema(schema_name: str) -> dict:
    """按文件名加载一个 JSON Schema（如 "b01-match.response.schema.json"）。"""
    path = os.path.join(_CONTRACTS_DIR, schema_name)
    with open(path, "r", encoding="utf-8") as f:
        return __import__("json").load(f)


def validate_payload(schema_name: str, payload) -> tuple[bool, str]:
    """对 payload 用指定 schema 做校验，返回 (是否通过, 错误信息)。

    复用 validate_contracts.validate —— 失败时抛 SchemaError，这里包成布尔便于分支。
    """
    schema = load_schema(schema_name)
    try:
        validate_contracts.validate(payload, schema)
        return True, ""
    except validate_contracts.SchemaError as e:
        return False, str(e)


def validate_event(schema_name: str, payload) -> tuple[bool, str]:
    """事件 payload 校验（如 ai-result.event.schema.json），与响应同口径。"""
    return validate_payload(schema_name, payload)
