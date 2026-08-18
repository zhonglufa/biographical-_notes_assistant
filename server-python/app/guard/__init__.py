"""guard/__init__.py — 5 护栏统一导出与装配门面（结构规范 §四 要求的 guard/ 包）

护栏清单（对应产品护栏 1–6 中落在本服务侧的部分）：
  - cost.BudgetPolicy / CostGuard           → 护栏 2：LLM 成本熔断
  - monitor.LightweightMonitor              → 护栏 3：封号率 / 投递成功率 / 错误率 / LLM 成本监控
  - feature_flags.FeatureFlags             → 护栏 4：灰度 / 回滚开关（含 kill-switch）
  - crypto_shred.CryptoShred               → 护栏 5：PIPL 凭证 crypto-shred（编排逻辑，真实 KMS 待接）
  - audit_log.AuditLog                     → 护栏 6：审计链（法检复核痕迹）

build_guardrails() 从 app.config.Settings 构造全部实例，供 main.lifespan 注入。
"""
from __future__ import annotations

from app.config import Settings
from app.guard.audit_log import AuditLog
from app.guard.cost import (
    DEFAULT_BREAKER_THRESHOLD,
    DEFAULT_COOLDOWN_S,
    DEFAULT_DAILY_CAP_CENTS,
    DEFAULT_PER_CALL_CENTS,
    BudgetPolicy,
    CostGuard,
    CostGuardOpen,
)
from app.guard.crypto_shred import CryptoShred
from app.guard.feature_flags import DEFAULT_FLAGS, FeatureFlags
from app.guard.monitor import (
    BanTracker,
    ApplyLedger,
    InMemoryMetrics,
    LightweightMonitor,
    MonitorThresholds,
)

__all__ = [
    "BudgetPolicy", "CostGuard", "CostGuardOpen",
    "DEFAULT_DAILY_CAP_CENTS", "DEFAULT_PER_CALL_CENTS",
    "DEFAULT_BREAKER_THRESHOLD", "DEFAULT_COOLDOWN_S",
    "LightweightMonitor", "InMemoryMetrics", "MonitorThresholds",
    "BanTracker", "ApplyLedger",
    "AuditLog", "FeatureFlags", "DEFAULT_FLAGS", "CryptoShred",
    "build_guardrails",
]


def build_guardrails(settings: Settings):
    """从 Settings 装配全部护栏实例（单一入口，便于 lifespan 注入与测试 override）。"""
    monitor = LightweightMonitor(
        thresholds=MonitorThresholds(
            error_rate_max=settings.monitor_error_rate_max,
            ban_rate_max=settings.monitor_ban_rate_max,
            apply_success_min=settings.monitor_apply_success_min,
            llm_daily_cap_cents=settings.llm_daily_cap_cents,
        )
    )
    budget = BudgetPolicy(
        daily_cap_cents=settings.llm_daily_cap_cents,
        per_call_cents=settings.llm_per_call_cents,
        breaker_threshold=settings.breaker_threshold,
        cooldown_s=settings.cooldown_s,
    )
    feature_flags = FeatureFlags(overrides_path=settings.feature_flags_overrides_path)
    audit = AuditLog(path=settings.audit_log_path)
    return {
        "monitor": monitor,
        "budget": budget,
        "cost_guard": budget.guard,
        "feature_flags": feature_flags,
        "audit": audit,
        "crypto_shred": CryptoShred(),
    }
