"""test_server_main.py — HTTP 入口路由 + 契约 fail-closed + 护栏3 /metrics 接线

不启真实 socket：直接驱动 HttpApp.route()，覆盖 25 端点路由、请求校验、
存活探针、Prometheus 指标导出。护栏3 四项指标经 ServerApp(bus=) 自动挂接后
须真实可导出（URL /metrics 返回 rat_* 系列）。
"""
from base import check
from server_main import build_app
from stubs import API_STUB


def test_http_routing():
    app = build_app()

    # 1) 存活探针
    st, body, ct = app.route("GET", "/healthz", None)
    check("healthz = 200", st == 200)
    check("healthz 暴露 25 个契约端点", body.get("endpoints") == 25)

    # 2) Prometheus 指标（护栏3 接线后必须可导出）
    st, body, ct = app.route("GET", "/metrics", None)
    check("metrics = 200", st == 200)
    check("metrics 是 Prometheus 文本", "rat_error_rate" in body and "rat_apply_success_rate" in body)
    check("metrics 含封号率/LLM成本", "rat_ban_rate" in body and "rat_llm_cost_cents" in body)

    # 3) 有效请求：A01 用其 example_request，须过契约 -> 200
    ep_a01 = next(e for e in API_STUB.endpoints() if e.name.startswith("A01"))
    st, body, ct = app.route("POST", "/api/A01", dict(ep_a01.example_request))
    check("A01 有效请求 = 200", st == 200)

    # 4) 无效请求：缺必填字段 + additionalProperties:false -> 422 fail-closed
    st, body, ct = app.route("POST", "/api/A01", {"channel": "email"})
    check("A01 无效请求 = 422(fail-closed)", st == 422)
    check("422 返回契约违规错误", isinstance(body, dict) and body.get("error") == "request_schema_violation")

    # 5) 未知端点编号 -> 404
    st, body, ct = app.route("POST", "/api/A99", {})
    check("未知 A 编号 = 404", st == 404)

    # 6) 未知路径 -> 404
    st, body, ct = app.route("GET", "/nope", None)
    check("未知路径 = 404", st == 404)

    # 7) 大小写不敏感路由：/api/a01 == /api/A01
    st, body, ct = app.route("POST", "/api/a01", dict(ep_a01.example_request))
    check("小写 /api/a01 仍路由到 A01 = 200", st == 200)


def main():
    test_http_routing()
    print("test_server_main OK")


if __name__ == "__main__":
    main()
