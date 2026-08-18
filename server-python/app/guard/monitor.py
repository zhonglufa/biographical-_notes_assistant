"""guard/monitor.py — 轻量监控（护栏 3 · 迁移自 scaffold metrics.InMemoryMetrics + monitor.LightweightMonitor）

聚合 4 项可度量指标（对齐运维采纳结论「监控必要且比 K8s 更该先有」）：
  - 错误率 error_rate：来自逐端点请求计数（InMemoryMetrics，由中间件/路由层 record_request 填充）
  - 封号率 ban_rate：平台账号封禁数 / 活跃账号数
  - 投递成功率 apply_success_rate：投递成功 / 总投递
  - LLM 成本（分）：来自成本护栏累计（LLMClient 成功调用后 record_llm_cost）

暴露 snapshot()（指标 + 阈值告警）；生产替换为 Prometheus/OTel（HLD §4.7），
本模块定义统一接缝与阈值语义。迁移时仅去掉对 demo 模块 metrics 的外部 import，逻辑一致。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class MonitorThresholds:
    """护栏 3 告警阈值（均为 DEMO 默认；生产值由运维配置）。"""
    error_rate_max: float = 0.05        # 错误率 > 5% 告警
    ban_rate_max: float = 0.02          # 封号率 > 2% 告警
    apply_success_min: float = 0.80     # 投递成功率 < 80% 告警
    llm_daily_cap_cents: int = 50_000   # LLM 日成本超 ¥500 告警


class InMemoryMetrics:
    """内存指标实现（演示 + 单测用）。生产环境替换为外部时序库（HLD §4.7）。"""

    def __init__(self) -> None:
        self._per_endpoint: dict[str, int] = {}
        self.total_cost_cents: int = 0
        self.error_count: int = 0
        self.ok_count: int = 0
        self._lock = threading.Lock()

    def record(self, endpoint_id: str, status: int, cost_cents: int) -> None:
        with self._lock:
            self._per_endpoint[endpoint_id] = self._per_endpoint.get(endpoint_id, 0) + 1
            self.total_cost_cents += max(0, cost_cents)
            if status >= 400:
                self.error_count += 1
            else:
                self.ok_count += 1

    def snapshot(self) -> dict:
        with self._lock:
            total = self.ok_count + self.error_count
            return {
                "per_endpoint": dict(self._per_endpoint),
                "total_requests": total,
                "ok": self.ok_count,
                "errors": self.error_count,
                "error_rate": (self.error_count / total) if total else 0.0,
                "total_cost_cents": self.total_cost_cents,
            }


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
        self.metrics = metrics or InMemoryMetrics()
        self.bans = BanTracker()
        self.applies = ApplyLedger()
        self.llm_cost_cents: int = 0

    # ---- 数据接入 ----
    def record_request(self, endpoint_id: str, status: int, cost_cents: int = 0) -> None:
        """路由/中间件层逐请求调用，填充错误率与逐端点计数。"""
        self.metrics.record(endpoint_id, status, cost_cents)

    def record_llm_cost(self, cents: int) -> None:
        self.llm_cost_cents += max(0, cents)

    def record_apply(self, success: bool) -> None:
        self.applies.record(success)

    def record_ban(self, n: int = 1) -> None:
        self.bans.record_ban(n)

    # ---- 指标读取 ----
    def error_rate(self) -> float:
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
