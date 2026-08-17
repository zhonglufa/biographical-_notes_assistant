"""test_server_app.py — 服务端 API 框架单测（B2-1）"""
from base import check
from event_bus import EventBus
from metrics import InMemoryMetrics
from server_app import ServerApp
from delivery_state_machine import DeliveryStateMachine


def main():
    bus = EventBus()
    metrics = InMemoryMetrics()
    sm = DeliveryStateMachine()
    app = ServerApp(bus=bus, metrics=metrics, state_machine=sm)

    # 路由：合法端点 200
    r = app.handle("A01 auth-login",
                   {"channel": "email", "deviceId": "d", "email": "a@b.com", "password": "secret123"})
    check("A01 路由 200", r.status == 200 and r.ok)
    # 未知端点 404 + 错误码映射
    r2 = app.handle("ZZZ", {})
    check("未知端点 404+RESOURCE_NOT_FOUND", r2.status == 404 and r2.error_code == "RESOURCE_NOT_FOUND")
    # 指标记录
    check("指标已记录 A01", metrics.snapshot()["per_endpoint"].get("A01 auth-login") == 1)

    # 投递应用：推进状态机
    tid = app.create_application("u1", "j1", "boss")
    check("create→autofilling", sm.state(tid) == "autofilling")

    captured = []
    bus.subscribe("apply.status.changed", lambda p: captured.append(p))
    app.record_submission(tid)
    check("提交→submitted", sm.state(tid) == "submitted")
    check("发出 apply 事件", len(captured) == 1)
    check("事件 toState=submitted", captured[0]["toState"] == "submitted")

    # 失败路径：autofilling 态直接 closed
    tid2 = app.create_application("u1", "j2", "boss")
    app.record_failure(tid2)
    check("失败→closed", sm.state(tid2) == "closed")

    print("test_server_app OK")


if __name__ == "__main__":
    main()
