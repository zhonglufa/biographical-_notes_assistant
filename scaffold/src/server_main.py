"""server_main.py — 零依赖 HTTP 入口（O 阶段 · 上线就绪）

把「契约优先」的 ServerApp 暴露为 HTTP 服务。设计原则：
- 仅用 Python 标准库（http.server），零第三方依赖，CI/容器直接跑；
- 所有请求/响应经契约校验（fail-closed），永不偏离 design/contracts 真相源；
- 接线护栏3：ServerApp(bus=...) 自动创建并挂接 LightweightMonitor——
  错误率来自共享 InMemoryMetrics，投递成功率来自 apply.status.changed 事件流，
  封号率来自适配器验证码挑战 record_ban，LLM 成本来自 MatchService 回写；四项指标
  真实流动（此前 monitor 是孤儿代码，本次已修复，见 commit 743b660）。

路由约定（无需手填路由表，A 编号为契约端点的规范 id）：
- POST /api/<Axx>      -> 按 A 编号唯一匹配端点（如 /api/A01 -> "A01 auth-login"）
- GET  /healthz        -> 存活探针
- GET  /metrics        -> Prometheus 文本（护栏3 四指标 + 告警）

⚠️ 部署上线、提供真实凭据、点击上线开关属用户独有动作，本文件不伪造部署完成。
"""
from __future__ import annotations

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

# 让同目录模块可 import（server_app / stubs / monitor / event_bus ...）
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from server_app import ServerApp
from event_bus import EventBus
from metrics import InMemoryMetrics
from delivery_state_machine import DeliveryStateMachine


# /api/A01 或 /api/A01/ 均能匹配；A 编号为契约端点规范 id
_A_RE = re.compile(r"^/api/([Aa]\d{2})(?:/.*)?$")

# Prometheus exposition 文本格式版本标识
_PROM_CT = "text/plain; version=0.0.4; charset=utf-8"


def _to_prometheus(snap: dict) -> str:
    """把 LightweightMonitor.snapshot() 渲染为 Prometheus 文本（与 export_metrics 同口径）。"""
    lines = [
        "# HELP rat_apply_success_rate 投递成功率(0~1)",
        "# TYPE rat_apply_success_rate gauge",
        f"rat_apply_success_rate {snap['apply_success_rate']}",
        "# HELP rat_ban_rate 账号封号率(0~1)",
        "# TYPE rat_ban_rate gauge",
        f"rat_ban_rate {snap['ban_rate']}",
        "# HELP rat_error_rate 接口错误率(0~1)",
        "# TYPE rat_error_rate gauge",
        f"rat_error_rate {snap['error_rate']}",
        "# HELP rat_llm_cost_cents LLM 当日累计成本(分)",
        "# TYPE rat_llm_cost_cents counter",
        f"rat_llm_cost_cents {snap['llm_cost_cents']}",
        "# HELP rat_alert 护栏告警(1=有告警)",
        "# TYPE rat_alert gauge",
        f"rat_alert{{count=\"{len(snap['alerts'])}\"}} {1 if snap['alerts'] else 0}",
    ]
    return "\n".join(lines) + "\n"


class HttpApp:
    """无 socket 的 HTTP 应用核心，便于单测；BaseHTTPRequestHandler 仅做 I/O 适配。

    构造时即完成护栏3 接线：EventBus + InMemoryMetrics + DeliveryStateMachine 注入
    ServerApp，ServerApp 在 bus 存在时自动创建并挂接 LightweightMonitor。
    """

    def __init__(self) -> None:
        bus = EventBus()
        metrics = InMemoryMetrics()
        sm = DeliveryStateMachine()
        # bus 非空 -> ServerApp 内部自动 LightweightMonitor(metrics) + attach_monitor(bus, monitor)
        self.app = ServerApp(bus=bus, metrics=metrics, state_machine=sm)
        # 预建 A 编号 -> 端点 id 的查找表（大小写不敏感）
        self._by_a = {e.split(" ", 1)[0].lower(): e for e in self.app.rt.list_endpoints()}

    # 返回 (status:int, payload:dict|str, content_type:str)
    def route(self, method: str, path: str, body: Optional[dict],
              headers: Optional[dict] = None) -> tuple:
        method = (method or "GET").upper()
        path = (path or "/").split("?")[0]

        if method == "GET" and path == "/healthz":
            return 200, {"status": "ok", "endpoints": len(self._by_a)}, "application/json"

        if method == "GET" and path == "/metrics":
            snap = self.app.monitor.snapshot()
            return 200, _to_prometheus(snap), _PROM_CT

        if method == "POST" and (m := _A_RE.match(path)):
            endpoint_id = self._by_a.get(m.group(1).lower())
            if endpoint_id is None:
                return 404, {"error": "unknown_endpoint", "endpoint": m.group(1)}, "application/json"
            user_id = (headers or {}).get("X-User-Id", "anonymous")
            result = self.app.handle(endpoint_id, body, user_id=user_id)
            return result.status, result.body, "application/json"

        return 404, {"error": "not_found", "path": path, "method": method}, "application/json"


class _Handler(BaseHTTPRequestHandler):
    """线程化 HTTP 处理器：解析请求 -> HttpApp.route -> 写回 JSON/文本。"""

    # 由 main() 注入的单例 HttpApp
    app: "HttpApp" = None  # type: ignore[assignment]

    def _send(self, status: int, payload, ctype: str) -> None:
        if isinstance(payload, (dict, list)):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        elif isinstance(payload, str):
            data = payload.encode("utf-8")
        else:
            data = payload
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> Optional[dict]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return None
        raw = self.rfile.read(length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None  # 交由 route 处理（契约校验会拒绝）

    def do_GET(self):
        status, payload, ctype = self.server.app.route("GET", self.path, None)  # type: ignore[attr-defined]
        self._send(status, payload, ctype)

    def do_POST(self):
        body = self._read_body()
        hdrs = {k: v for k, v in self.headers.items()}
        status, payload, ctype = self.server.app.route("POST", self.path, body, hdrs)  # type: ignore[attr-defined]
        self._send(status, payload, ctype)

    def log_message(self, *args):  # 静默默认访问日志（生产由 /metrics 观测）
        pass


def build_app() -> HttpApp:
    """工厂：供测试注入，亦供 main() 使用。"""
    return HttpApp()


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    app = build_app()
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.app = app  # type: ignore[attr-defined]
    print(f"▶ resume-ai-prod 服务端已启动：http://{host}:{port}  "
          f"（{len(app._by_a)} 个契约端点 + /healthz + /metrics）")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        print("\n⏹ 服务端已停止")


if __name__ == "__main__":
    main()
