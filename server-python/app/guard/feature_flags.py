"""guard/feature_flags.py — 灰度开关 / 回滚开关（护栏 4 · 迁移自 scaffold feature_flags.py）

设计目标（见 design/guardrails/gray-release.md）：
- 所有新功能默认 **关闭**（fail-safe）；上线必须经显式灰度开启。
- 支持全局 kill-switch（回滚）：一键关闭全部灰度功能。
- 运行时可经管理端点 override（紧急止血），override 持久化到本地覆盖文件。

诚实边界：
- 本文件是 **开关编排逻辑**，可独立单测；真实「谁有权改、谁来审计」属运维流程与合规范畴。
- 灰度策略取值（如百分比、白名单）属业务/运维决策，默认保守（False），不臆测。
- 迁移时新增 AI 网关相关开关（llm_cost_guard / ban_monitor），其余语义不变。
"""
from __future__ import annotations

import json
import os
import threading

# 默认开关表：新功能一律默认 False（fail-safe，未灰度不开启）
DEFAULT_FLAGS = {
    "ai_match": True,           # AI 匹配主开关（PRD §24 从严，默认开但可关）
    "llm_cost_guard": True,     # 护栏 2 成本熔断开关
    "ban_monitor": True,        # 护栏 3 封号率监控开关
    "interview_sim": False,     # 面试模拟（灰度新功能）
    "payment": False,           # 支付（灰度新功能）
    "rag_stage2": False,        # 阶段二 RAG（用户延后）
}


class FeatureFlags:
    def __init__(self, overrides_path: str | None = None, flags: dict | None = None) -> None:
        self._lock = threading.Lock()
        self._flags = dict(DEFAULT_FLAGS)
        if flags:
            self._flags.update(flags)
        self._overrides_path = overrides_path
        self._overrides: dict = {}
        self._kill_switch = False
        if overrides_path and os.path.exists(overrides_path):
            try:
                with open(overrides_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._overrides = data.get("overrides", {}) or {}
                self._kill_switch = bool(data.get("kill_switch", False))
            except Exception:
                pass

    def is_enabled(self, key: str, user_id: str | None = None) -> bool:
        with self._lock:
            if self._kill_switch:
                return False  # 全局回滚：一切灰度功能强制关
            if key in self._overrides:
                return bool(self._overrides[key])
            return bool(self._flags.get(key, False))

    def set_override(self, key: str, value: bool) -> None:
        with self._lock:
            self._overrides[key] = bool(value)
            self._persist()

    def trigger_kill_switch(self, on: bool = True) -> None:
        """紧急回滚：一键关闭全部灰度功能。"""
        with self._lock:
            self._kill_switch = bool(on)
            self._persist()

    def kill_switch(self) -> bool:
        with self._lock:
            return self._kill_switch

    def _persist(self) -> None:
        if not self._overrides_path:
            return
        try:
            with open(self._overrides_path, "w", encoding="utf-8") as f:
                json.dump({"kill_switch": self._kill_switch, "overrides": self._overrides}, f,
                          ensure_ascii=False, indent=2)
        except Exception:
            pass
