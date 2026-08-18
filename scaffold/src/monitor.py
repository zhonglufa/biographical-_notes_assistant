"""monitor.py — 轻量监控（护栏 3 · C2）

聚合 4 项可度量指标（对齐运维采纳结论「监控必要且比 K8s 更该先有」）：
  - LLM 成本（分）：来自成本护栏 / 预算策略累计
  - 封号率 ban_rate：平台账号封禁数 / 活跃账号数
  - 投递成功率 apply_success_rate：投递成功 / 总投递
  - 错误率 error_rate：来自 B2-1 MetricsSink

暴露 snapshot()（指标 + 阈值告警）；生产替换为 Prometheus/OTel（HLD §4.7），
本模块定义统一接缝与阈值语义。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from metrics import InMemoryMetrics


@dataclass
class MonitorThresholds:
    """护栏 3 告警阈值（均为 DEMO 默认；生产值由运维配置）。"""
    error_rate_max: float = 0.05        # 错误率 > 5% 告警
    ban_rate_max: float = 0.02          # 封号率 > 2% 告警
    apply_success_min: float = 0.80     # 投递成功率 < 80% 告警
    llm_daily_cap_cents: int = 50_000   # LLM 日成本超 ¥500 告警


class BanTracker:
    """平台封号追踪：记录封禁数 + 活跃账号基数。"""

    def __init__(self) -> None:
        self._bans = 0
        self._active_accounts = 0

    def set_active_accounts(self, n: int) -> None:
        self._active_accounts = n

    def record_ban(self, n: int = 1) -> None:
        self._bans += n

    def ban_rate(self) -> float:
        if self._active_accounts == 0:
            return 0.0
        return self._bans / self._active_accounts


class ApplyLedger:
    """投递成功/失败计数。"""

    def __init__(self) -> None:
        self._success = 0
        self._total = 0

    def record(self, success: bool) -> None:
        self._total += 1
        if success:
            self._success += 1

    def success_rate(self) -> float:
        return self._success / self._total if self._total else 0.0


class LightweightMonitor:
    """轻量监控中枢：聚合 4 指标 + 阈值告警。"""

    def __init__(self, *, thresholds: Optional[MonitorThresholds] = None,
                 metrics: Optional[InMemoryMetrics] = None) -> None:
        self.thresholds = thresholds or MonitorThresholds()
        self.metrics = metrics
        self.bans = BanTracker()
        self.applies = ApplyLedger()
        self.llm_cost_cents: int = 0

    # ---- 数据接入 ----
    def record_llm_cost(self, cents: int) -> None:
        self.llm_cost_cents += max(0, cents)

    def record_apply(self, success: bool) -> None:
        self.applies.record(success)

    def record_ban(self, n: int = 1) -> None:
        self.bans.record_ban(n)

    # ---- 指标读取 ----
    def error_rate(self) -> float:
        if self.metrics is None:
            return 0.0
        return self.metrics.snapshot()["error_rate"]

    def snapshot(self) -> dict:
        er = self.error_rate()
        br = self.bans.ban_rate()
        sr = self.applies.success_rate()
        t = self.thresholds
        alerts = []
        if er > t.error_rate_max:
            alerts.append("error_rate_high")
        if br > t.ban_rate_max:
            alerts.append("ban_rate_high")
        if sr < t.apply_success_min:
            alerts.append("apply_success_low")
        if self.llm_cost_cents > t.llm_daily_cap_cents:
            alerts.append("llm_cost_over_cap")
        return {
            "error_rate": er,
            "ban_rate": br,
            "apply_success_rate": sr,
            "llm_cost_cents": self.llm_cost_cents,
            "alerts": alerts,
        }
