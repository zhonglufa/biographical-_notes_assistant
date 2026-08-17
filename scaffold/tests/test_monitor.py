"""test_monitor.py — 轻量监控单测（C2 · 护栏3）"""
from base import check
from metrics import InMemoryMetrics
from monitor import LightweightMonitor, MonitorThresholds


def main():
    metrics = InMemoryMetrics()
    metrics.record("A01 auth-login", 200, 0)
    metrics.record("A01 auth-login", 500, 0)  # 1 error / 2 = 0.5
    mon = LightweightMonitor(metrics=metrics,
                             thresholds=MonitorThresholds(error_rate_max=0.05))
    mon.record_apply(True)
    mon.record_apply(False)            # 成功率 0.5
    mon.bans.set_active_accounts(10)
    mon.record_ban(1)                  # 封号率 0.1
    mon.record_llm_cost(60000)         # 超 ¥500 上限

    snap = mon.snapshot()
    check("错误率=0.5", abs(snap["error_rate"] - 0.5) < 1e-9)
    check("封号率=0.1", abs(snap["ban_rate"] - 0.1) < 1e-9)
    check("投递成功率=0.5", abs(snap["apply_success_rate"] - 0.5) < 1e-9)
    check("LLM成本=60000", snap["llm_cost_cents"] == 60000)
    check("触发4项告警", set(snap["alerts"]) >=
          {"error_rate_high", "ban_rate_high", "apply_success_low", "llm_cost_over_cap"})

    # 正常情况无告警
    m2 = InMemoryMetrics()
    m2.record("A", 200, 0)
    mon2 = LightweightMonitor(metrics=m2)
    mon2.record_apply(True)
    mon2.record_apply(True)
    mon2.bans.set_active_accounts(100)  # 0 封禁
    snap2 = mon2.snapshot()
    check("正常无告警", snap2["alerts"] == [])

    print("test_monitor OK")


if __name__ == "__main__":
    main()
