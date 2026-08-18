"""
monitor_hooks.py — 监控生产接入点（O3 · 护栏 3 落地衔接）

把 LightweightMonitor 接入运行期事件流，使护栏 3 的 4 指标
（LLM 成本 / 封号率 / 投递成功率 / 错误率）在真实运行时被持续填充，而非仅 demo 计数。

接入点（零外部依赖，纯标准库）：
  - attach_monitor(bus, monitor)：订阅 domain-events（apply.status.changed），
    自动累计「投递成功率」（toState=submitted 记成功 / closed|failed 记失败）。
  - record_llm_cost(monitor, cents)：LLM 匹配调用后调用，累计 LLM 日成本
    （护栏 2 成本护栏与 护栏 3 监控共享同一计数）。
  - record_ban(monitor, n)：平台适配器检测到账号封禁时调用，累计封号率。
  - 错误率：由 ServerApp 的 MetricsSink 透传进 monitor.metrics（构造时传入即可）。

真实部署时由运维把 monitor.snapshot() 接 Prometheus / OTel
（见 scripts/export_metrics.py 的 Prometheus 文本导出范式）。

⚠️ 本文件为「生产就绪脚本」，不真部署；部署上线属用户独有动作。
"""
from __future__ import annotations

from event_bus import EventBus
from monitor import LightweightMonitor


def attach_monitor(bus: EventBus, monitor: LightweightMonitor) -> None:
    """订阅 apply.status.changed，自动累计投递成功率。

    事件 payload 形态（对齐 local_agent._emit / server_app）：
      {"eventType": "apply.status.changed", "payload": {"toState": "submitted" | "closed" | "failed", ...}}
    """
    # 幂等：同一 monitor 实例可能被 server_app 与 local_agent 多处注入同一总线，
    # 重复订阅会导致成功率重复计数；用实例标记避免。
    if getattr(monitor, "_monitor_attached", False):
        return
    monitor._monitor_attached = True

    def _on_apply(payload: dict):
        # EventBus.publish 向订阅者投递的是 event["payload"]（见 event_bus.py）
        to_state = payload.get("toState") if isinstance(payload, dict) else None
        if to_state == "submitted":
            monitor.record_apply(True)        # 投递成功
        elif to_state in ("closed", "failed"):
            monitor.record_apply(False)       # 投递失败

    bus.subscribe("apply.status.changed", _on_apply)


def record_llm_cost(monitor: LightweightMonitor, cents: int) -> None:
    """LLM 匹配调用后累计成本（护栏 2 与 3 共享计数，单位：分）。"""
    monitor.record_llm_cost(cents)


def record_ban(monitor: LightweightMonitor, n: int = 1) -> None:
    """平台适配器检测到封禁时累计（封号率 = bans / 活跃账号数）。"""
    monitor.record_ban(n)


if __name__ == "__main__":
    # 自测：attach_monitor 能把事件流正确累计进 monitor。
    from event_bus import EventBus as _Bus
    from monitor import LightweightMonitor as _Mon

    bus = _Bus()
    mon = _Mon()
    attach_monitor(bus, mon)

    def _ev(to_state, i):
        # 完整 envelope + payload（对齐 local_agent._emit 与 domain-events 契约）
        return {"eventType": "apply.status.changed", "traceId": f"tr{i}",
                "ts": 1700000000000, "producer": "test",
                "payload": {"taskId": f"t{i}", "userId": "u", "platformId": "boss",
                            "jobId": f"j{i}", "fromState": "created",
                            "toState": to_state, "reason": "demo"}}

    # 模拟 3 次成功 + 1 次失败
    for i in range(3):
        bus.publish(_ev("submitted", i))
    bus.publish(_ev("failed", 9))
    snap = mon.snapshot()
    assert abs(snap["apply_success_rate"] - 0.75) < 1e-9, snap
    # 成功率 75% < 80% 阈值 -> apply_success_low 告警应触发（验证阈值逻辑生效）
    assert "apply_success_low" in snap["alerts"], snap
    print("monitor_hooks 自测通过 ✅  apply_success_rate =", snap["apply_success_rate"], "alerts =", snap["alerts"])
