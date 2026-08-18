"""ai/llm_client.py — LLM 网关客户端（主 DeepSeek + 备用，ADR-009）

关键安全/可用性约束（防生产事故）：
- 仅当配置 LLM_API_KEY 或注入了 gateway 才「可用」；否则 available()=False，编排层直接走降级链；
- 任何网络/解析异常都返回 None（绝不抛给调用方），由编排层 fail-closed 降级；
- 真实 HTTP 调用用 httpx（FastAPI 依赖自带），仅在生产配置 key 后触发；
  本开发与测试环境无 key → 不触网、不消耗额度。

护栏接入（本次迁移落地）：
- 护栏 2（成本熔断）：每次调用前经 CostGuard.charge() 预扣；超日硬上限或熔断开启 → 拒绝本次
  调用（返回 None → 编排层走规则兜底），并写审计；成功后记账 + 累计 LLM 成本到监控。
- 护栏 4（特性开关）：llm_cost_guard 关闭时跳过成本门禁（紧急止血用）。
- 全部行为 fail-closed：成本护栏异常不阻断业务，仅降级。
"""
from __future__ import annotations

from typing import Optional, Protocol

import httpx


class LLMGateway(Protocol):
    """LLM 调用网关端口（对齐 scaffold LLMGateway）。生产注入真实适配；测试/默认注入 FakeGateway。"""

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None) -> str | None:
        """返回模型原始文本（期望 JSON）；失败返回 None。"""
        ...


class LLMClient:
    def __init__(self, *, api_key: str | None = None,
                 base_url: str = "https://api.deepseek.com/v1",
                 primary_model: str = "deepseek-chat", backup_model: str = "deepseek-chat",
                 gateway: LLMGateway | None = None,
                 cost_guard=None, monitor=None, audit=None, feature_flags=None,
                 per_call_cents: int = 10) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.backup_model = backup_model
        self.gateway = gateway
        self.cost_guard = cost_guard
        self.monitor = monitor
        self.audit = audit
        self.feature_flags = feature_flags
        self.per_call_cents = per_call_cents

    def available(self) -> bool:
        # 配置了真实 key 或注入了 gateway（含测试 FakeGateway）→ 视为可用
        return bool(self.api_key) or (self.gateway is not None)

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None = None) -> str | None:
        """返回模型文本；不可用/成本护栏拦截/任何失败返回 None（调用方据此降级）。"""
        if not self.available():
            return None

        # —— 护栏 4：特性开关（llm_cost_guard 关闭 → 跳过成本门禁）——
        guard_enabled = True
        if self.feature_flags is not None:
            guard_enabled = self.feature_flags.is_enabled("llm_cost_guard")
        # —— 护栏 2：成本门禁（预扣；超预算/熔断 → 拦截并降级）——
        if guard_enabled and self.cost_guard is not None:
            if not self.cost_guard.charge(self.per_call_cents):
                if self.audit is not None:
                    self.audit.append(actor="llm-client", action="cost_guard.block",
                                      target="llm-cost", decision="degrade",
                                      meta={"remaining_cents": self.cost_guard.remaining_cents()})
                return None

        try:
            raw = self._call_gateway(system=system, user=user, timeout_ms=timeout_ms, model=model)
            # 成功记账：闭合熔断 + 累计 LLM 成本到监控（护栏 2/3 共享计数）
            if self.cost_guard is not None:
                self.cost_guard.record_success()
            if self.monitor is not None:
                self.monitor.record_llm_cost(self.per_call_cents)
            return raw
        except Exception:
            # fail-closed：任何失败（超时/5xx/解析）→ 记录失败（可能触发熔断）→ 返回 None 触发降级
            if self.cost_guard is not None:
                self.cost_guard.record_failure()
            return None

    def _call_gateway(self, *, system: str, user: str, timeout_ms: int, model: str | None) -> str | None:
        if self.gateway is not None:
            return self.gateway.complete(system=system, user=user, timeout_ms=timeout_ms, model=model)
        model = model or self.primary_model
        try:
            with httpx.Client(timeout=max(0.5, timeout_ms / 1000.0)) as client:
                resp = client.post(
                    self.base_url + "/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}",
                             "Content-Type": "application/json"},
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
            # 主模型失败 → 试探备份模型一次（仅 httpx 路径有意义）
            if model != self.backup_model:
                try:
                    with httpx.Client(timeout=max(0.5, timeout_ms / 1000.0)) as client:
                        resp = client.post(
                            self.base_url + "/chat/completions",
                            headers={"Authorization": f"Bearer {self.api_key}",
                                     "Content-Type": "application/json"},
                            json={
                                "model": self.backup_model,
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
                    return None
            return None
