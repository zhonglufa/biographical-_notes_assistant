"""test_domain_events.py — 领域事件构造器合规单测（B2-1）"""
from base import check
from contract_runtime import validate_payload
from domain_events import (apply_status_changed, strategy_updated, payment_status_changed,
                           daily_report_generated, member_plan_changed)

SCHEMA = "domain-events.event.schema.json"


def _ok(ev):
    return validate_payload(SCHEMA, ev)


def main():
    ev1 = apply_status_changed("t1", "u1", "boss", "j1", "created", "submitted", "ok")
    ok, err = _ok(ev1)
    check("apply 事件合规", ok), (err and print("  ", err))

    ev2 = payment_status_changed("O1", "u1", None, "created", "paid", 29900)
    ok, err = _ok(ev2)
    check("payment 事件合规", ok), (err and print("  ", err))

    ev3 = strategy_updated("u1", "s1", 1, ["dailyQuota"], 1760000000000)
    ok, err = _ok(ev3)
    check("strategy 事件合规", ok), (err and print("  ", err))

    ev4 = daily_report_generated("u1", "2026-08-17", "今日投递5", 5, 4, 1)
    ok, err = _ok(ev4)
    check("daily 事件合规", ok), (err and print("  ", err))

    ev5 = member_plan_changed("u1", "O1", "pro", 1760000000000, "activated")
    ok, err = _ok(ev5)
    check("member 事件合规", ok), (err and print("  ", err))

    # 非法平台应断言失败（构造器内置 assert）
    raised = False
    try:
        apply_status_changed("t", "u", "unknown_platform", "j", "created", "submitted")
    except AssertionError:
        raised = True
    check("非法 platformId 被构造器拒绝", raised)

    print("test_domain_events OK")


if __name__ == "__main__":
    main()
