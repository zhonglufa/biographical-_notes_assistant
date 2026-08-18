"""test_guardrails.py — 5 护栏迁移落地验证（护栏 2/3/4/5/6）

覆盖：
- 护栏 2（成本熔断）：CostGuard 超预算/失败熔断/冷却半开；LLMClient 成本门禁拦截 → 不触网 → 编排降级
- 护栏 3（监控）：错误率/封号率/投递成功率/LLM 成本计数 + 阈值告警；AgentTriggerService 上报
- 护栏 4（灰度开关）：kill-switch / override 关闭 llm_cost_guard → 成本门禁跳过
- 护栏 5（crypto-shred）：销毁 KEK 后历史备份不可解密
- 护栏 6（审计链）：append → verify_chain 检测篡改
"""
from __future__ import annotations

import pytest

from app.ai.content_safety import ContentSafety
from app.ai.llm_client import LLMClient
from app.ai.orchestrator import AIOrchestrator, LocalResultRecorder
from app.agent.service import AgentTriggerService
from app.agent.transport import LocalAgentTransport
from app.guard.audit_log import AuditLog
from app.guard.cost import BudgetPolicy, CostGuard
from app.guard.crypto_shred import CryptoShred
from app.guard.feature_flags import FeatureFlags
from app.guard.monitor import LightweightMonitor, MonitorThresholds


class FakeGateway:
    """返回固定文本；记录调用次数（验证成本门禁是否短路了网络）。"""
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls = 0

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None) -> str:
        self.calls += 1
        return self.text


class RefusingGateway:
    """若被调用则抛错（用于证明「拦截来自成本门禁」而非「网关缺失」）。"""
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None) -> str:
        self.calls += 1
        raise AssertionError("gateway 不应在成本门禁拦截后被调用")


# ---------- 护栏 2：CostGuard 纯逻辑 ----------
def test_cost_guard_over_budget_opens():
    g = CostGuard(daily_cap_cents=15)
    assert g.charge(10) is True
    assert g.charge(10) is False       # 10+10>15 → 开闸
    assert g.is_open is True
    assert g.remaining_cents() == 5


def test_cost_guard_failure_breaker():
    t = [1000.0]
    g = CostGuard(failure_threshold=3, cooldown_s=60, now=lambda: t[0])
    for _ in range(3):
        g.record_failure()
    assert g.is_open is True            # 连续失败达阈值 → 开闸
    g.record_success()                  # 仅清零失败计数，不闭合电路（仍在冷却内）
    assert g.is_open is True
    t[0] = 1000 + 60                    # 冷却结束 → 半开
    assert g.is_open is False
    assert g.charge(1) is True          # 半开态一次成功 charge → 保持闭合
    assert g.is_open is False


def test_cost_guard_cooldown_half_open():
    t = [1000.0]
    g = CostGuard(daily_cap_cents=5, cooldown_s=60, now=lambda: t[0])
    assert g.charge(10) is False       # 超预算 → 开闸 @1000
    assert g.is_open is True
    t[0] = 1000 + 59
    assert g.is_open is True           # 冷却内
    t[0] = 1000 + 60
    assert g.is_open is False          # 冷却结束 → 半开


def test_budget_policy_as_dict():
    p = BudgetPolicy(daily_cap_cents=100, per_call_cents=10, breaker_threshold=5, cooldown_s=60)
    d = p.as_dict()
    assert d["daily_cap_cents"] == 100
    assert d["per_call_cents"] == 10
    assert d["breaker_threshold"] == 5
    assert d["circuit_open"] is False
    assert d["remaining_cents"] == 100


# ---------- 护栏 2/4：LLMClient 成本门禁 ----------
def test_llm_client_cost_block_skips_gateway():
    gate = RefusingGateway()
    guard = CostGuard(daily_cap_cents=5)
    assert guard.charge(10) is False   # 耗尽预算 → 开闸
    client = LLMClient(gateway=gate, cost_guard=guard, per_call_cents=10)
    assert client.available() is True  # gateway 注入即视为可用
    assert client.complete(system="s", user="u", timeout_ms=1000) is None
    assert gate.calls == 0             # 门禁短路，绝不触网


def test_llm_client_cost_allows_and_records():
    gate = FakeGateway('{"x":1}')
    guard = CostGuard(daily_cap_cents=1000)
    mon = LightweightMonitor()
    client = LLMClient(gateway=gate, cost_guard=guard, monitor=mon, per_call_cents=10)
    assert client.complete(system="s", user="u", timeout_ms=1000) == '{"x":1}'
    assert gate.calls == 1
    assert mon.llm_cost_cents == 10
    assert guard.remaining_cents() == 990


def test_feature_flag_disables_cost_guard():
    gate = FakeGateway('{"x":1}')
    guard = CostGuard(daily_cap_cents=5)
    assert guard.charge(10) is False   # 本会拦截
    ff = FeatureFlags(flags={"llm_cost_guard": False})  # 紧急止血开关
    client = LLMClient(gateway=gate, cost_guard=guard, feature_flags=ff, per_call_cents=10)
    assert client.complete(system="s", user="u", timeout_ms=1000) == '{"x":1}'
    assert gate.calls == 1             # 开关关闭 → 跳过门禁，仍调用


def test_orchestrator_degrades_on_cost_block():
    """编排层在成本护栏拦截时走规则兜底（model=rule），而非 LLM。"""
    gate = RefusingGateway()
    guard = CostGuard(daily_cap_cents=5)
    assert guard.charge(10) is False
    llm = LLMClient(gateway=gate, cost_guard=guard, per_call_cents=10)
    orch = AIOrchestrator(llm, ContentSafety(enabled=True), LocalResultRecorder(), {})
    resp = orch.match("jd", "resume")
    assert resp["model"] == "rule"
    assert gate.calls == 0


# ---------- 护栏 3：监控 ----------
def test_monitor_alerts():
    m = LightweightMonitor(thresholds=MonitorThresholds(
        error_rate_max=0.05, ban_rate_max=0.02, apply_success_min=0.80, llm_daily_cap_cents=50000))
    m.record_request("a", 200)
    m.record_request("a", 500)          # 错误率 0.5
    m.record_apply(False)               # 成功率 0
    m.bans.set_active_accounts(10)
    m.record_ban(1)                     # 封号率 0.1
    m.record_llm_cost(60000)            # 超 ¥500
    snap = m.snapshot()
    assert abs(snap["error_rate"] - 0.5) < 1e-9
    assert abs(snap["ban_rate"] - 0.1) < 1e-9
    assert abs(snap["apply_success_rate"] - 0.0) < 1e-9
    assert set(snap["alerts"]) >= {"error_rate_high", "ban_rate_high", "apply_success_low", "llm_cost_over_cap"}


def test_agent_service_records_monitor():
    mon = LightweightMonitor()
    svc = AgentTriggerService(LocalAgentTransport(), monitor=mon)
    svc.report_apply_result(True)
    svc.report_apply_result(False)
    svc.report_ban(1)
    mon.bans.set_active_accounts(10)
    snap = mon.snapshot()
    assert abs(snap["apply_success_rate"] - 0.5) < 1e-9
    assert abs(snap["ban_rate"] - 0.1) < 1e-9
    assert "apply_success_low" in snap["alerts"]


# ---------- 护栏 4：特性开关 ----------
def test_feature_flags_kill_switch():
    ff = FeatureFlags(flags={"payment": False})
    assert ff.is_enabled("payment") is False
    ff.set_override("payment", True)
    assert ff.is_enabled("payment") is True
    ff.trigger_kill_switch(True)
    assert ff.is_enabled("payment") is False
    ff.trigger_kill_switch(False)
    assert ff.is_enabled("ai_match") is True


# ---------- 护栏 5：crypto-shred ----------
def test_crypto_shred_blocks_after_shred():
    cs = CryptoShred()
    cs.register_kek("k1", b"16bytesecretkey!!")
    blob = cs.encrypt_with("k1", b"pii-data")
    assert cs.decrypt_with("k1", blob) == b"pii-data"
    cs.shred_user("k1")
    with pytest.raises(PermissionError):
        cs.decrypt_with("k1", blob)


# ---------- 护栏 6：审计链 ----------
def test_audit_log_detects_tamper():
    a = AuditLog()
    a.append("u", "dsar.delete", "user-1", "pending")
    a.append("sys", "purge", "user-1", "done")
    assert a.verify_chain() is True
    a.entries()[0]["decision"] = "tampered"
    assert a.verify_chain() is False
