"""
event_bus.py — 领域事件总线（内存版 stub，contract-first · B3 增强）

演示「发布事件前必须先过契约校验」。生产环境替换为 RabbitMQ（HLD §4.6），
但「校验逻辑」完全一致 —— 这就是 contract-first 的意义：换传输不改规则。

事件必须匹配 design/contracts/domain-events.event.schema.json
（投递状态流转 / 策略变更 / 支付状态 / 日报生成 / 会员权益）。

B3 增强点（2026-08-17）：
  - 增加 at-least-once 语义支撑：publish() 落审计日志，replay() 可重投（幂等消费由订阅者保证）；
  - 增加 subscribe_all() 与 reset()（测试基座复用）。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contract_runtime import validate_payload

EVENT_SCHEMA = "domain-events.event.schema.json"


class EventBus:
    """极简内存事件总线：发布前校验，订阅者按 eventType 分发。"""

    def __init__(self):
        self._subscribers = {}   # eventType -> [handler, ...]
        self._log = []            # 已发布且通过校验的事件（审计溯源 + at-least-once 重投源）

    def subscribe(self, event_type: str, handler):
        self._subscribers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler):
        """订阅全部事件类型（测试/审计场景）。"""
        self._subscribers.setdefault("*", []).append(handler)

    def publish(self, event: dict) -> tuple:
        """发布一个事件。返回 (是否发布成功, 信息)。

        步骤：
          1) 用 domain-events schema 校验整包（envelope + oneOf 定型 payload）
          2) 校验失败 -> fail-closed，绝不发布（防脏数据入 MQ）
          3) 校验通过 -> 记录审计 + 通知订阅者
        """
        ok, err = validate_payload(EVENT_SCHEMA, event)
        if not ok:
            return False, f"事件未通过契约校验，拒绝发布: {err}"
        self._log.append(event)
        et = event["eventType"]
        delivered = 0
        for h in self._subscribers.get(et, []):
            h(event["payload"])
            delivered += 1
        for h in self._subscribers.get("*", []):
            h(event)
            delivered += 1
        return True, f"已发布 {et}（投递 {delivered} 个订阅者）"

    def replay(self) -> int:
        """at-least-once 语义支撑：把所有已审计事件重新投递给当前订阅者。

        生产环境由 MQ 的「未确认重投」保证；此处用显式 replay 演示同一能力。
        幂等由订阅者依据事件内的幂等键（如 orderNo/idempotencyKey）去重。
        """
        count = 0
        for ev in self._log:
            et = ev["eventType"]
            for h in self._subscribers.get(et, []):
                h(ev["payload"])
                count += 1
            for h in self._subscribers.get("*", []):
                h(ev)
                count += 1
        return count

    def log_size(self) -> int:
        return len(self._log)

    def reset(self):
        """清空订阅者与审计日志（测试隔离）。"""
        self._subscribers.clear()
        self._log.clear()


# ---- 一个具体事件的构造示例（支付状态变更，驱动会员权益 C5）----
def build_payment_status_event(order_no: str, user_id: str, to_state: str, amount: int):
    return {
        "eventType": "payment.status.changed",
        "traceId": "trace-demo-001",
        "ts": 1700000000000,
        "producer": "java-pay",
        "payload": {
            "orderNo": order_no,
            "userId": user_id,
            "fromState": "created",
            "toState": to_state,
            "amount": amount,
            "currency": "CNY",
        },
    }


if __name__ == "__main__":
    bus = EventBus()
    captured = []
    bus.subscribe("payment.status.changed", lambda p: captured.append(p))

    ev = build_payment_status_event("O1", "U1", "paid", 29900)
    ok, msg = bus.publish(ev)
    print("发布合法支付事件 ->", msg, "| 订阅者收到:", len(captured))

    # 故意构造一个非法事件（amount 为负，违反 minimum）
    bad = build_payment_status_event("O2", "U1", "paid", -1)
    ok2, msg2 = bus.publish(bad)
    print("发布非法支付事件 ->", msg2)

    # at-least-once 重投演示
    n = bus.replay()
    print("replay 重投次数 ->", n, "| 订阅者累计收到:", len(captured))
