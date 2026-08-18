"""ai/llm_client.py — LLM 网关客户端（主 DeepSeek + 备用，ADR-009）

关键安全/可用性约束（防生产事故）：
- 仅当配置 LLM_API_KEY 才「可用」；否则 available()=False，编排层直接走降级链；
- 任何网络/解析异常都返回 None（绝不抛给调用方），由编排层 fail-closed 降级；
- 真实 HTTP 调用用 httpx（FastAPI 依赖自带），仅在生产配置 key 后触发；
  本开发与测试环境无 key → 不触网、不消耗额度。
"""
from __future__ import annotations

import httpx


class LLMClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.deepseek.com/v1",
                 primary_model: str = "deepseek-chat", backup_model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.backup_model = backup_model

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None = None) -> str | None:
        """返回模型文本；不可用或任何失败返回 None（调用方据此降级）。"""
        if not self.available():
            return None
        model = model or self.primary_model
        try:
            with httpx.Client(timeout=max(0.5, timeout_ms / 1000.0)) as client:
                resp = client.post(
                    self.base_url + "/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            # fail-closed：任何失败（超时/5xx/解析）→ 返回 None 触发降级
            return None
