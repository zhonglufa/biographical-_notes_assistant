"""server_app.py — 服务端 API 应用框架（B2-1）

- 包裹 ContractRuntime：所有请求先过契约（fail-closed），再分发到对应 A 层桩。
- 集成 MetricsSink（guardrail 3 接缝）：每次 handle 记一条指标。
- 集成 DeliveryStateMachine：create_application 推进 10 态机；
  record_submission / record_failure 发合规 apply.status.changed 事件（经 EventBus，fail-closed）。
- 不实现真实 DB / HTTP 层（生产挂 Spring Boot + 本 Runtime；此处契约优先演示）。

防生产事故：所有出参经契约校验；事件发布失败绝不吞掉（EventBus 内部 fail-closed）；
不触真实凭据 / 部署 / 真实 LLM（LLM 经 llm_match 网关注入）。
"""
from __future__ import annotations

import time
from typing import Optional

from contract_runtime import ContractRuntime
from delivery_state_machine import DeliveryStateMachine
from domain_events import apply_status_changed
from monitor import LightweightMonitor
from monitor_hooks import attach_monitor


class ServerApp:
    """契约优先服务端应用：分发 + 指标 + 投递状态机 + 事件。"""

    def __init__(self, *, bus=None, metrics=None, state_machine=None, monitor=None) -> None:
        self.rt = ContractRuntime()
        self.bus = bus
        self.metrics = metrics
        self.sm = state_machine or DeliveryStateMachine()
        self._meta: dict[str, dict] = {}
        # 护栏3接线：有事件总线且未显式传入 monitor 时，自动创建并挂接 LightweightMonitor；
        # 复用同一 metrics 实例使「错误率」自动流入，attach_monitor 订阅 apply.status.changed
        # 使「投递成功率」事件真正进入监控（此前 monitor 为孤儿代码，生产环境收不到事件）。
        if bus is not None and monitor is None:
            monitor = LightweightMonitor(metrics=self.metrics)
            attach_monitor(bus, monitor)
        self.monitor = monitor

    # ---- 通用请求分发 ----
    def handle(self, endpoint_id: str, request: Optional[dict], *, user_id: str = "anonymous"):
        result = self.rt.call(endpoint_id, request or {})
        if self.metrics is not None:
            self.metrics.record(endpoint_id, result.status, 0)
        return result

    # ---- 投递应用：推进 10 态机 + 发事件 ----
    def create_application(self, user_id: str, job_id: str, platform_id: str,
                           *, trace_id: Optional[str] = None) -> str:
        task_id = f"task-{job_id}-{int(time.time() * 1000)}"
        self.sm.create(task_id)
        self.sm.transition(task_id, "autofilling")
        self._meta[task_id] = {"user_id": user_id, "job_id": job_id, "platform_id": platform_id}
        return task_id

    def record_submission(self, task_id: str, *, trace_id: Optional[str] = None) -> None:
        meta = self._meta.get(task_id, {})
        self.sm.transition(task_id, "submitted")
        if self.bus is not None:
            self.bus.publish(apply_status_changed(
                task_id, meta.get("user_id", "anon"), meta.get("platform_id", "boss"),
                meta.get("job_id", ""), "created", "submitted", "local-agent submitted",
                trace_id=trace_id or f"trace-{task_id}"))

    def record_failure(self, task_id: str, *, trace_id: Optional[str] = None) -> None:
        meta = self._meta.get(task_id, {})
        self.sm.transition(task_id, "closed")
        if self.bus is not None:
            self.bus.publish(apply_status_changed(
                task_id, meta.get("user_id", "anon"), meta.get("platform_id", "boss"),
                meta.get("job_id", ""), "created", "failed", "submission failed",
                trace_id=trace_id or f"trace-{task_id}"))
