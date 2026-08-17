"""domain_events.py — 领域事件构造器（contract-first）

所有构造器返回严格通过 design/contracts/domain-events.event.schema.json 的 dict。
供 server_app / notify / llm_match 等模块复用，确保「发事件前先合规」。

事件类型（对齐 HLD §4.6 事件信封 + LLD 各模块）：
  apply.status.changed / strategy.updated / payment.status.changed /
  daily.report.generated / member.plan.changed
"""
from __future__ import annotations

import time

_APPLY_STATES = {"created", "submitted", "pending_retry", "succeeded", "failed"}
_PLATFORMS = {"boss", "liepin", "zhaopin", "51job", "lagou"}
_PLANS = {"free", "pro", "premium", "admin"}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _envelope(event_type: str, payload: dict, *, trace_id: str | None = None,
              producer: str = "server") -> dict:
    return {
        "eventType": event_type,
        "traceId": trace_id or f"trace-{_now_ms()}",
        "ts": _now_ms(),
        "producer": producer,
        "payload": payload,
    }


def apply_status_changed(task_id, user_id, platform_id, job_id, from_state, to_state,
                         reason=None, *, trace_id=None) -> dict:
    assert from_state in _APPLY_STATES, f"非法 fromState: {from_state}"
    assert to_state in _APPLY_STATES, f"非法 toState: {to_state}"
    assert platform_id in _PLATFORMS, f"非法 platformId: {platform_id}"
    return _envelope(
        "apply.status.changed",
        {"taskId": task_id, "userId": user_id, "platformId": platform_id,
         "jobId": job_id, "fromState": from_state, "toState": to_state, "reason": reason},
        trace_id=trace_id, producer="server",
    )


def strategy_updated(user_id, strategy_id, version, changed_fields, effective_at,
                     *, trace_id=None) -> dict:
    return _envelope(
        "strategy.updated",
        {"userId": user_id, "strategyId": strategy_id, "version": version,
         "changedFields": changed_fields, "effectiveAt": effective_at},
        trace_id=trace_id, producer="server",
    )


def payment_status_changed(order_no, user_id, trade_no, from_state, to_state, amount,
                           currency="CNY", *, trace_id=None) -> dict:
    assert from_state in {"created", "paid", "refunded", "renewing", "grace"}
    assert to_state in {"paid", "refunded", "renewing", "grace"}
    return _envelope(
        "payment.status.changed",
        {"orderNo": order_no, "userId": user_id, "tradeNo": trade_no,
         "fromState": from_state, "toState": to_state, "amount": amount, "currency": currency},
        trace_id=trace_id, producer="java-pay",
    )


def daily_report_generated(user_id, date, summary, applied_total, success, failed,
                           *, trace_id=None) -> dict:
    return _envelope(
        "daily.report.generated",
        {"userId": user_id, "date": date, "summary": summary,
         "appliedTotal": applied_total, "success": success, "failed": failed},
        trace_id=trace_id, producer="daily-report",
    )


def member_plan_changed(user_id, order_no, plan, effective_at, change_type,
                        *, trace_id=None) -> dict:
    assert plan in _PLANS, f"非法 plan: {plan}"
    return _envelope(
        "member.plan.changed",
        {"userId": user_id, "orderNo": order_no, "plan": plan,
         "effectiveAt": effective_at, "changeType": change_type},
        trace_id=trace_id, producer="member",
    )
