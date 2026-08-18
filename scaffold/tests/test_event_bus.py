"""test_event_bus.py — 领域事件总线测试（B3）

验证：发布前契约校验 fail-closed / 合法发布 / at-least-once replay / subscribe_all。
零外部依赖，直接 `python scaffold/tests/test_event_bus.py` 运行。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from base import check
from event_bus import EventBus, build_payment_status_event


def test_publish_ok():
    print("· 合法事件发布")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))
    ok, msg = bus.publish(build_payment_status_event("O1", "U1", "paid", 29900))
    check("合法支付事件发布成功", ok is True and len(got) == 1)
    check("审计日志 +1", bus.log_size() == 1)


def test_publish_fail_closed():
    print("· 非法事件 fail-closed")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))
    ok, msg = bus.publish(build_payment_status_event("O2", "U1", "paid", -1))
    check("非法支付事件被拒(fail-closed)", ok is False and len(got) == 0)
    check("非法事件不入审计日志", bus.log_size() == 0)


def test_replay_at_least_once():
    print("· at-least-once replay")
    bus = EventBus()
    got = []
    bus.subscribe("payment.status.changed", lambda p: got.append(p))
    bus.publish(build_payment_status_event("O1", "U1", "paid", 29900))
    before = len(got)
    n = bus.replay()
    check("replay 至少重投 1 次", n >= 1)
    check("订阅者累计收到 >= 原1 + 重投1", len(got) >= before + 1)


def test_subscribe_all():
    print("· subscribe_all 通配订阅")
    bus = EventBus()
    allc = []
    bus.subscribe_all(lambda e: allc.append(e))
    bus.publish(build_payment_status_event("O1", "U1", "paid", 29900))
    check("subscribe_all 收到事件", len(allc) == 1)


def main():
    print("=== test_event_bus ===")
    test_publish_ok()
    test_publish_fail_closed()
    test_replay_at_least_once()
    test_subscribe_all()
    print("事件总线测试通过 ✅")


if __name__ == "__main__":
    main()
