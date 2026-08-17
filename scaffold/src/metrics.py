"""metrics.py — 指标汇接层（guardrail 3 接缝 · B2-1 建立，C2 监控消费）

ServerApp 每次 handle 都会 record 一条 (endpoint_id, status, cost_cents)。
本模块定义 MetricsSink 协议 + 内存实现；C2 轻量监控将在本接缝之上叠加
LLM 成本 / 封号率 / 投递成功率 / 错误率的聚合与暴露（护栏 3 落地）。

设计原则：契约优先、零外部依赖；生产替换为 Prometheus/OTel（HLD §4.7）。
"""
from __future__ import annotations

import threading
from typing import Protocol


class MetricsSink(Protocol):
    """指标汇接协议。任何实现只要提供 record() 即可接入 ServerApp。"""

    def record(self, endpoint_id: str, status: int, cost_cents: int) -> None:
        """记录一次请求：端点 id、HTTP 状态码、本次 LLM 成本（分）。"""
        ...


class InMemoryMetrics:
    """内存指标实现（演示 + 单测用）。生产环境替换为外部时序库。"""

    def __init__(self) -> None:
        self._per_endpoint: dict[str, int] = {}
        self.total_cost_cents: int = 0
        self.error_count: int = 0
        self.ok_count: int = 0
        # 轻量容器多线程场景（ThreadingHTTPServer）下保护计数，避免竞争丢计数
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
        """聚合快照：供 C2 监控读取（错误率 / 总成本 / 逐端点计数）。"""
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
