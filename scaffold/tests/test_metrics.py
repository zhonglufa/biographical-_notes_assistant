"""test_metrics.py — 指标汇接层单测（B2-1）"""
from base import check
from metrics import InMemoryMetrics


def main():
    m = InMemoryMetrics()
    m.record("A01 auth-login", 200, 0)
    m.record("A01 auth-login", 422, 0)
    m.record("A10 applications-list", 200, 5)
    s = m.snapshot()
    check("ok 计数=2", s["ok"] == 2)
    check("错误 计数=1", s["errors"] == 1)
    check("错误率=1/3", abs(s["error_rate"] - 1 / 3) < 1e-9)
    check("总成本=5分", s["total_cost_cents"] == 5)
    check("端点计数正确", s["per_endpoint"]["A01 auth-login"] == 2)
    print("test_metrics OK")


if __name__ == "__main__":
    main()
