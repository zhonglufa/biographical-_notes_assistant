"""test_notify.py — 通知服务单测（B2-4）"""
from base import check
from event_bus import EventBus
from notify import InMemoryNotificationSink, NotificationService
from domain_events import (apply_status_changed, payment_status_changed,
                           daily_report_generated, member_plan_changed)


def main():
    bus = EventBus()
    sink = InMemoryNotificationSink()
    svc = NotificationService(sink, bus)

    bus.publish(apply_status_changed("t1", "u1", "boss", "j1", "created", "submitted", "ok"))
    check("投递提交→1条通知", len(sink.items) == 1)
    check("提交通知 level=L1", sink.items[0]["level"] == "L1")

    bus.publish(apply_status_changed("t2", "u1", "boss", "j2", "created", "failed", "boom"))
    check("投递失败→第2条", len(sink.items) == 2)
    check("失败通知 level=L2", sink.items[1]["level"] == "L2")

    bus.publish(payment_status_changed("O1", "u1", None, "created", "paid", 29900))
    check("支付→第3条", len(sink.items) == 3)

    bus.publish(daily_report_generated("u1", "2026-08-17", "今日5份", 5, 4, 1))
    check("日报→第4条", len(sink.items) == 4)

    bus.publish(member_plan_changed("u1", "O1", "pro", 1760000000000, "activated"))
    check("会员→第5条", len(sink.items) == 5)

    check("字段合规 createdAt=int", isinstance(sink.items[0]["createdAt"], int))
    check("字段合规含 body", "body" in sink.items[0])
    check("unread 计数=5", sink.unread() == 5)

    print("test_notify OK")


if __name__ == "__main__":
    main()
