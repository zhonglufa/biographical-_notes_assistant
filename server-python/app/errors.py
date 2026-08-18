"""errors.py — 统一错误信封（HLD §4.7 / error-envelope.schema.json）

所有非 2xx 响应一律走 error-envelope：{code, message, traceId, retryable[, user_action]}。
code 必须在 design/contracts/error-codes.json 注册表唯一（已新增 INTERNAL_ERROR / CONTRACT_BREACH）。
fail-closed：请求/响应契约违规都返回规范错误信封，绝不悄悄放行或吞掉实现偏离。
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONTRACTS_DIR = os.path.join(_REPO_ROOT, "design", "contracts")
if _CONTRACTS_DIR not in sys.path:
    sys.path.insert(0, _CONTRACTS_DIR)

# 加载错误码注册表，用于 code -> (http, retryable) 一致映射
def _load_error_registry() -> dict:
    with open(os.path.join(_CONTRACTS_DIR, "error-codes.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["code"]: e for e in data["registry"]}


_ERROR_REGISTRY = _load_error_registry()


class AppError(Exception):
    """业务错误：携带规范错误码，自动映射 http / retryable（来自注册表）。"""

    def __init__(self, code: str, message: str, *, trace_id: str = "", user_action: str | None = None,
                 http: int | None = None, retryable: bool | None = None):
        meta = _ERROR_REGISTRY.get(code, {})
        self.code = code
        self.message = message
        self.trace_id = trace_id
        self.user_action = user_action
        self.http = http if http is not None else meta.get("http", 500)
        self.retryable = retryable if retryable is not None else meta.get("retryable", True)
        super().__init__(message)


def error_envelope(code: str, message: str, trace_id: str, retryable: bool,
                   user_action: str | None = None) -> dict:
    """构造符合 error-envelope.schema.json 的错误信封（additionalProperties:false）。"""
    env: dict = {
        "code": code,
        "message": message,
        "traceId": trace_id,
        "retryable": bool(retryable),
    }
    if user_action is not None:
        env["user_action"] = user_action
    return env


def envelope_from_error(err: AppError) -> dict:
    return error_envelope(err.code, err.message, err.trace_id, err.retryable, err.user_action)
