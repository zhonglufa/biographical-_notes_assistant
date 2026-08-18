"""cost_policy.py — LLM 预算策略（护栏 2 装配 · C1）

把 B2-3 的 CostGuard 装配成产品级「LLM 预算策略」：
  - 日硬上限 daily_cap_cents（护栏 2 核心，超帽即熔断）
  - 单 call 成本 per_call_cents（按模型定价配置）
  - 失败熔断阈值 breaker_threshold + 冷却 cooldown_s

⚠️ 生产硬上限金额 DEMO 默认（¥500/天）；**真实值由部署方/用户按预算配置**
   （循环不代设真实金额、不花钱、不订阅）。本模块只把护栏 2 组装成可注入
   MatchService 的统一策略，确保成本护栏「落地」而非孤立类。
"""
from __future__ import annotations

from llm_match import CostGuard, MatchService, LLMGateway


# DEMO 默认日硬上限（¥500/天 = 50000 分）；生产值由部署方/用户配置。
DEMO_DAILY_CAP_CENTS = 50_000
DEFAULT_PER_CALL_CENTS = 10
DEFAULT_BREAKER_THRESHOLD = 5
DEFAULT_COOLDOWN_S = 60


class BudgetPolicy:
    """LLM 预算策略：护栏 2 的唯一装配入口。"""

    def __init__(self, *, daily_cap_cents: int = DEMO_DAILY_CAP_CENTS,
                 per_call_cents: int = DEFAULT_PER_CALL_CENTS,
                 breaker_threshold: int = DEFAULT_BREAKER_THRESHOLD,
                 cooldown_s: int = DEFAULT_COOLDOWN_S, now=None) -> None:
        self.daily_cap_cents = daily_cap_cents
        self.per_call_cents = per_call_cents
        self.breaker_threshold = breaker_threshold
        self.cooldown_s = cooldown_s
        self._guard = CostGuard(daily_cap_cents, failure_threshold=breaker_threshold,
                                cooldown_s=cooldown_s, now=now)

    def guard(self) -> CostGuard:
        return self._guard

    def build_match_service(self, gateway: LLMGateway) -> MatchService:
        """用本策略的护栏 + 单 call 成本装配 MatchService。"""
        return MatchService(gateway, self._guard, cost_per_call_cents=self.per_call_cents)

    def remaining_cents(self) -> int:
        return self._guard.remaining_cents()

    def is_open(self) -> bool:
        return self._guard.is_open

    def as_dict(self) -> dict:
        """策略摘要（供监控 C2 / 运维面板展示）。"""
        return {
            "daily_cap_cents": self.daily_cap_cents,
            "per_call_cents": self.per_call_cents,
            "breaker_threshold": self.breaker_threshold,
            "cooldown_s": self.cooldown_s,
            "remaining_cents": self.remaining_cents(),
            "circuit_open": self.is_open(),
        }
