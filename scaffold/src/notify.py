"""notify.py — 通知服务（B2-4）

订阅 domain-events，把关键业务事件转成站内信（A22 notifications-list 条目形状）。
- NotificationSink(Protocol)：推送目标；默认 InMemoryNotificationSink（演示）。
- NotificationService：在 EventBus 上订阅 apply/payment/daily/member 事件，
  构建合规通知并推送。

⚠️ 安全边界：不触真实 PII / 推送通道（真实推送经 A23 WS，由前端/网关持有凭据）；
此处只生成站内信记录，遵循「半自动 + 用户可观测」的产品定位。
"""
from __future__ import annotations

import time
from typing import Protocol, runtime_checkable


@runtime_checkable
class NotificationSink(Protocol):
    """通知推送目标端口；生产注入真实推送（站内信表 / 邮件 / WS 网关注入凭据）。"""

    def push(self, notification: dict) -> None:
        ...


class InMemoryNotificationSink:
    """内存通知汇（演示 + 单测）。"""

    def __init__(self) -> None:
        self.items: list[dict] = []

    def push(self, n: dict) -> None:
        self.items.append(n)

    def unread(self) -> int:
        return sum(1 for n in self.items if not n["read"])


def _now_ms() -> int:
    return int(time.time() * 1000)


class NotificationService:
    """事件驱动的通知服务：订阅领域事件 -> 生成合规站内信。"""

    def __init__(self, sink: NotificationSink, bus) -> None:
        self.sink = sink
        self.bus = bus
        self._seq = 0
        bus.subscribe("apply.status.changed", self._on_apply)
        bus.subscribe("payment.status.changed", self._on_payment)
        bus.subscribe("daily.report.generated", self._on_daily)
        bus.subscribe("member.plan.changed", self._on_member)

    def _push(self, level: str, title: str, body: str, *, channel=None) -> None:
        self._seq += 1
        self.sink.push({
            "id": f"NTF-{_now_ms()}-{self._seq}",
            "level": level,
            "title": title,
            "body": body,
            "read": False,
            "createdAt": _now_ms(),
            "channel": channel,
        })

    def _on_apply(self, p: dict) -> None:
        to = p.get("toState")
        job = p.get("jobId", "")
        if to == "submitted":
            self._push("L1", "投递已提交", f"岗位 {job} 已提交至 {p.get('platformId')}")
        elif to == "failed":
            self._push("L2", "投递失败", f"岗位 {job} 投递失败，请检查")
        elif to == "pending_retry":
            self._push("L2", "投递待重试", f"岗位 {job} 需重试")

    def _on_payment(self, p: dict) -> None:
        to = p.get("toState")
        if to == "paid":
            self._push("L1", "支付成功", f"订单 {p.get('orderNo')} 已支付 {p.get('amount')} 分")
        elif to == "refunded":
            self._push("L2", "已退款", f"订单 {p.get('orderNo')} 已退款")

    def _on_daily(self, p: dict) -> None:
        self._push("L1", "每日日报", p.get("summary") or f"今日投递 {p.get('appliedTotal', 0)} 份")

    def _on_member(self, p: dict) -> None:
        self._push("L1", "会员变更", f"会员套餐变更为 {p.get('plan')}（{p.get('changeType')}）")
