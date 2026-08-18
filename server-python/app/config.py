"""config.py — server-python 运行期配置（ADR-002：服务端 Python FastAPI）

设计原则（与 scaffold 一致：契约/设计是真相源，配置只是注入项）：
- 内部鉴权令牌 INTERNAL_TOKEN 必须注入（生产缺失即 fail-closed 拒绝全部内部调用）；
- LLM_API_KEY 可选：缺失 → LLM 网关不可用 → 自动走三级降级链（降级优先，防生产事故）；
- 超时预算（SLA）直接复用设计契约注册表 ai-orchestrator.methods.json，不另写死。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

# server-python/app/config.py -> 上溯 3 级到仓库根（与 scaffold/src 同构）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONTRACTS_DIR = os.path.join(_REPO_ROOT, "design", "contracts")


@dataclass
class MethodSla:
    """单个 B 方法的 SLA（来自 ai-orchestrator.methods.json）。"""
    sync: bool
    timeout_ms: int
    degrade_to: str


@dataclass
class Settings:
    # 内部令牌：默认空（fail-closed）。生产/非 dev 必须显式设置 INTERNAL_TOKEN；
    # 未注入 → security.require_internal_token 一律 401 拒绝（防误配置裸奔，无后门/无 dev 兜底）。
    internal_token: str = field(default_factory=lambda: os.environ.get("INTERNAL_TOKEN", ""))

    # LLM 网关（主 DeepSeek + 备用）。缺失 API Key → 网关不可用 → 降级链兜底
    llm_api_key: str | None = field(default_factory=lambda: os.environ.get("LLM_API_KEY"))
    llm_base_url: str = field(default_factory=lambda: os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"))
    llm_primary_model: str = field(default_factory=lambda: os.environ.get("LLM_PRIMARY_MODEL", "deepseek-chat"))
    llm_backup_model: str = field(default_factory=lambda: os.environ.get("LLM_BACKUP_MODEL", "deepseek-chat"))

    # 结果发布器：local（默认，落本地记录器）/ rabbitmq（文档化接缝，未启用）
    result_publisher: str = field(default_factory=lambda: os.environ.get("RESULT_PUBLISHER", "local"))

    # 服务元信息
    service_name: str = "resume-ai-python"
    contract_version: str = "1.0.0"

    # —— 护栏 2：LLM 成本预算（DEMO 默认；生产值由部署方/用户按预算配置）——
    llm_daily_cap_cents: int = field(default_factory=lambda: int(os.environ.get("LLM_DAILY_CAP_CENTS", "50000")))
    llm_per_call_cents: int = field(default_factory=lambda: int(os.environ.get("LLM_PER_CALL_CENTS", "10")))
    breaker_threshold: int = field(default_factory=lambda: int(os.environ.get("LLM_BREAKER_THRESHOLD", "5")))
    cooldown_s: int = field(default_factory=lambda: int(os.environ.get("LLM_BREAKER_COOLDOWN_S", "60")))

    # —— 护栏 3：监控阈值（DEMO 默认；生产值由运维配置）——
    monitor_error_rate_max: float = field(default_factory=lambda: float(os.environ.get("MON_ERROR_RATE_MAX", "0.05")))
    monitor_ban_rate_max: float = field(default_factory=lambda: float(os.environ.get("MON_BAN_RATE_MAX", "0.02")))
    monitor_apply_success_min: float = field(default_factory=lambda: float(os.environ.get("MON_APPLY_SUCCESS_MIN", "0.80")))

    # —— 护栏 4/6：特性开关覆盖文件 + 审计日志路径（可选持久化）——
    feature_flags_overrides_path: str | None = field(default_factory=lambda: os.environ.get("FEATURE_FLAGS_OVERRIDES"))
    audit_log_path: str | None = field(default_factory=lambda: os.environ.get("AUDIT_LOG_PATH"))

    # 各方法 SLA（启动时从契约注册表加载，单一真相源）
    sla: dict[str, MethodSla] = field(default_factory=dict)

    def load_sla_from_contract(self) -> None:
        """从 ai-orchestrator.methods.json 加载超时/同步/降级配置（不写死）。"""
        path = os.path.join(_CONTRACTS_DIR, "ai-orchestrator.methods.json")
        with open(path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        self.contract_version = reg.get("contractVersion", self.contract_version)
        for mid, m in reg.get("methods", {}).items():
            self.sla[mid] = MethodSla(
                sync=bool(m.get("sync", False)),
                timeout_ms=int(m.get("timeoutMs", 5000)),
                degrade_to=str(m.get("degradeTo", "")),
            )


# 模块级单例（应用启动时 load_sla_from_contract）
settings = Settings()
