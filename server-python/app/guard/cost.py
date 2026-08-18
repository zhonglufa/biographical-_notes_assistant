"""guard/cost.py — LLM 成本护栏（护栏 2 核心 · 迁移自 scaffold llm_match.CostGuard + cost_policy.BudgetPolicy）

迁移原则（结构规范 §四：迁移而非重写）：保留 scaffold 的「日硬上限 + 失败熔断 + 冷却半开」
语义，仅去掉对 demo 模块 llm_match.MatchService 的耦合，改为可被 LLMClient 直接使用的纯逻辑。

⚠️ DEMO 默认日硬上限 ¥500（50000 分）；**真实金额由部署方/用户按预算配置**
   （循环不代设真实金额、不花钱、不订阅）。本模块只把护栏 2 组装成可注入 LLMClient 的统一策略。
"""
from __future__ import annotations

import time
from typing import Callable, Optional

# DEMO 默认日硬上限（¥500/天 = 50000 分）。生产值由部署方/用户配置。
DEFAULT_DAILY_CAP_CENTS = 50_000
DEFAULT_PER_CALL_CENTS = 10
DEFAULT_BREAKER_THRESHOLD = 5
DEFAULT_COOLDOWN_S = 60


class CostGuardOpen(Exception):
    """成本护栏触发标记（保留 scaffold 语义）；LLMClient 内部捕获并降级，不向外抛。"""


class CostGuard:
    """LLM 成本护栏：日硬上限 + 失败熔断（护栏 2 可度量落地）。

    触顶或连续失败达阈值即「开闸（OPEN）」，拒绝后续调用，防止成本失控 / 故障放大；
    冷却窗口结束后进入「半开」，允许一次探测恢复（charge 成功则闭合）。
    """

    def __init__(self, daily_cap_cents: int = DEFAULT_DAILY_CAP_CENTS, *,
                 failure_threshold: int = DEFAULT_BREAKER_THRESHOLD,
                 cooldown_s: int = DEFAULT_COOLDOWN_S,
                 now: Optional[Callable[[], float]] = None) -> None:
        self.daily_cap_cents = daily_cap_cents
        self.failure_threshold = failure_threshold
        self.cooldown_s = cooldown_s
        self._spent = 0
        self._failures = 0
        self._opened_at: Optional[float] = None
        self._now = now or time.time

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if (self._now() - self._opened_at) >= self.cooldown_s:
            return False  # 冷却结束 → 半开：允许一次探测（charge 成功则闭合）
        return True

    def charge(self, cents: int) -> bool:
        """预扣成本；超日硬上限或熔断开启则拒绝（返回 False，并触发开闸）。"""
        if self.is_open:
            return False
        if self._spent + max(0, cents) > self.daily_cap_cents:
            self._open()
            return False
        self._spent += max(0, cents)
        return True

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._open()

    def record_success(self) -> None:
        self._failures = 0

    def _open(self) -> None:
        self._opened_at = self._now()

    def reset(self) -> None:
        self._spent = 0
        self._failures = 0
        self._opened_at = None

    def remaining_cents(self) -> int:
        return max(0, self.daily_cap_cents - self._spent)


class BudgetPolicy:
    """护栏 2 装配入口：预算 + 熔断参数打包，含摘要（对齐 scaffold BudgetPolicy）。"""

    def __init__(self, *, daily_cap_cents: int = DEFAULT_DAILY_CAP_CENTS,
                 per_call_cents: int = DEFAULT_PER_CALL_CENTS,
                 breaker_threshold: int = DEFAULT_BREAKER_THRESHOLD,
                 cooldown_s: int = DEFAULT_COOLDOWN_S, now=None) -> None:
        self.daily_cap_cents = daily_cap_cents
        self.per_call_cents = per_call_cents
        self.breaker_threshold = breaker_threshold
        self.cooldown_s = cooldown_s
        # 持有单一 live guard，as_dict 反映实时剩余/熔断状态（与 scaffold 语义一致）
        self.guard = CostGuard(daily_cap_cents, failure_threshold=breaker_threshold,
                               cooldown_s=cooldown_s, now=now)

    def remaining_cents(self) -> int:
        return self.guard.remaining_cents()

    def is_open(self) -> bool:
        return self.guard.is_open

    def as_dict(self) -> dict:
        """策略摘要（供监控 / 运维面板展示）。"""
        return {
            "daily_cap_cents": self.daily_cap_cents,
            "per_call_cents": self.per_call_cents,
            "breaker_threshold": self.breaker_threshold,
            "cooldown_s": self.cooldown_s,
            "remaining_cents": self.remaining_cents(),
            "circuit_open": self.is_open(),
        }
