#!/usr/bin/env python3
"""
export_metrics.py — 把 LightweightMonitor.snapshot() 导出为 Prometheus 文本格式（O3）

用法（演示 / 运维接入）：
  python scripts/export_metrics.py            # 用内置演示 monitor 打印指标
  python scripts/export_metrics.py --json     # 同时打印 JSON（便于其它采集器）

真实部署时，运维应把本输出挂到 /metrics 端点（可用 prometheus-client 或本文件的
纯文本生成器），由 Prometheus 周期抓取；本脚本零外部依赖，不引入新包。

⚠️ 本文件为「生产就绪脚本」，不真部署；部署上线属用户独有动作。
"""
from __future__ import annotations

import argparse
import json
import sys

# 让 import 找到 scaffold/src 下的模块
_HERE = sys.path[0]
sys.path.insert(0, "scaffold/src")

from monitor import LightweightMonitor, MonitorThresholds
from monitor_hooks import attach_monitor, record_llm_cost, record_ban
from event_bus import EventBus


def build_demo_monitor() -> LightweightMonitor:
    """构造一个带演示数据的 monitor（模拟半天运行期的累计）。"""
    bus = EventBus()
    mon = LightweightMonitor(thresholds=MonitorThresholds())
    attach_monitor(bus, mon)

    def _ev(to_state, i, prefix):
        return {"eventType": "apply.status.changed", "traceId": f"tr-{prefix}-{i}",
                "ts": 1700000000000, "producer": "demo",
                "payload": {"taskId": f"t{i}", "userId": "u", "platformId": "boss",
                            "jobId": f"j{i}", "fromState": "created",
                            "toState": to_state, "reason": "demo"}}

    # 模拟：10 次投递（8 成功 / 2 失败）+ 1 次 LLM 匹配成本 + 1 次封号
    for i in range(8):
        bus.publish(_ev("submitted", i, "ok"))
    for i in range(2):
        bus.publish(_ev("failed", i, "ng"))
    record_llm_cost(mon, 1200)        # LLM 匹配累计 ¥12.00
    mon.bans.set_active_accounts(100)
    record_ban(mon, 1)                 # 1/100 封号率 = 1%
    return mon


def to_prometheus(mon: LightweightMonitor) -> str:
    """把 snapshot 渲染为 Prometheus 文本 exposition 格式。"""
    s = mon.snapshot()
    lines = [
        "# HELP rat_apply_success_rate 投递成功率(0~1)",
        "# TYPE rat_apply_success_rate gauge",
        f"rat_apply_success_rate {s['apply_success_rate']}",
        "# HELP rat_ban_rate 账号封号率(0~1)",
        "# TYPE rat_ban_rate gauge",
        f"rat_ban_rate {s['ban_rate']}",
        "# HELP rat_error_rate 接口错误率(0~1)",
        "# TYPE rat_error_rate gauge",
        f"rat_error_rate {s['error_rate']}",
        "# HELP rat_llm_cost_cents LLM 当日累计成本(分)",
        "# TYPE rat_llm_cost_cents counter",
        f"rat_llm_cost_cents {s['llm_cost_cents']}",
        "# HELP rat_alert 护栏告警(1=有告警)",
        "# TYPE rat_alert gauge",
        f"rat_alert{{count=\"{len(s['alerts'])}\"}} {1 if s['alerts'] else 0}",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="同时输出 JSON")
    args = ap.parse_args()
    mon = build_demo_monitor()
    print(to_prometheus(mon))
    if args.json:
        print("--- JSON ---")
        print(json.dumps(mon.snapshot(), ensure_ascii=False, indent=2))
    print(f"指标导出完成 ✅  告警: {mon.snapshot()['alerts'] or '无'}")


if __name__ == "__main__":
    main()
