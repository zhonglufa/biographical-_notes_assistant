"""security.py — 内部调用鉴权（HLD §4.5 / §939：X-Internal-Token）

B01–B05 仅 Java→Python 服务间内网调用，Nginx 不暴露；鉴权用 X-Internal-Token。
fail-closed：生产环境 INTERNAL_TOKEN 未注入 → 拒绝全部内部调用（不开后门）。
"""
from __future__ import annotations

from fastapi import Header

from app.config import settings
from app.errors import AppError


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> str:
    """FastAPI 依赖：校验 X-Internal-Token，通过则返回令牌，否则抛 UNAUTHORIZED。

    注：本依赖返回令牌字符串，仅作为「已鉴权」凭证；各端点可直接当作已认证上下文。
    """
    expected = settings.internal_token
    # 生产未配置令牌 → 一律拒绝（防误配置导致内网接口裸奔）
    if not expected:
        raise AppError("UNAUTHORIZED", "Internal token not configured on server", http=401, retryable=False)
    if not x_internal_token or x_internal_token != expected:
        raise AppError("UNAUTHORIZED", "Missing or invalid X-Internal-Token", http=401, retryable=False)
    return x_internal_token
