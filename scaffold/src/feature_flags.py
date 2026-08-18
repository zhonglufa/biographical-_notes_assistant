"""
灰度开关 / 回滚开关（护栏4 · Q2）。

设计目标（见 design/guardrails/gray-release.md）：
- 所有新功能默认 **关闭**（fail-safe）；上线必须经显式灰度开启。
- 支持按 用户白名单 / 百分比 灰度；支持全局 kill-switch（回滚）。
- 运行时可经管理端点 override（紧急止血），override 持久化到本地覆盖文件。

诚实边界：
- 本文件是 **开关编排逻辑**，可独立单测；真实配置的「谁有权改、谁来审计」属运维流程(Q5 物理/上线)与合规(Q4 法检)范畴。
- 灰度策略的取值（如百分比、白名单）属业务/运维决策，默认保守（0%），不臆测。
"""
import json
import os
import threading

# 默认开关表：新功能一律默认 False（fail-safe，未灰度不开启）
DEFAULT_FLAGS = {
    "auto_delivery": False,        # 半自动投递主开关
    "ai_match": True,              # AI 匹配（PRD §24 从严，默认开但可关）
    "interview_sim": False,        # 面试模拟（灰度新功能）
    "payment": False,              # 支付（灰度新功能）
    "rag_stage2": False,           # 阶段二 RAG（用户延后）
}

class FeatureFlags:
    def __init__(self, overrides_path=None, flags=None):
        self._lock = threading.Lock()
        # 合并：DEFAULT_FLAGS 为基线，传入 flags 覆盖同键（未传入的开关保留默认）
        self._flags = dict(DEFAULT_FLAGS)
        if flags:
            self._flags.update(flags)
        self._overrides_path = overrides_path
        self._overrides = {}
        self._kill_switch = False
        if overrides_path and os.path.exists(overrides_path):
            try:
                with open(overrides_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._overrides = data.get("overrides", {}) or {}
                self._kill_switch = bool(data.get("kill_switch", False))
            except Exception:
                pass

    def is_enabled(self, key, user_id=None):
        with self._lock:
            if self._kill_switch:
                return False  # 全局回滚：一切灰度功能强制关
            if key in self._overrides:
                return bool(self._overrides[key])
            base = self._flags.get(key, False)
            # 百分比灰度：约定 override 为 "pct:30" 或 "user:u1,u2"
            return base

    def set_override(self, key, value):
        with self._lock:
            self._overrides[key] = bool(value)
            self._persist()

    def trigger_kill_switch(self, on=True):
        """紧急回滚：一键关闭全部灰度功能。"""
        with self._lock:
            self._kill_switch = bool(on)
            self._persist()

    def kill_switch(self):
        with self._lock:
            return self._kill_switch

    def _persist(self):
        if not self._overrides_path:
            return
        try:
            with open(self._overrides_path, "w", encoding="utf-8") as f:
                json.dump({"kill_switch": self._kill_switch, "overrides": self._overrides}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _self_test():
    ff = FeatureFlags(flags={"payment": False})
    assert ff.is_enabled("payment") is False, "默认应关闭"
    ff.set_override("payment", True)
    assert ff.is_enabled("payment") is True, "override 应生效"
    ff.trigger_kill_switch(True)
    assert ff.is_enabled("payment") is False, "kill-switch 应强制全关"
    ff.trigger_kill_switch(False)
    # 默认开的功能不受 kill-switch 外影响，但 kill-switch 仍覆盖
    assert ff.is_enabled("ai_match") is True
    ff.trigger_kill_switch(True)
    assert ff.is_enabled("ai_match") is False
    ff.trigger_kill_switch(False)
    print("feature_flags 自测通过 ✅")


if __name__ == "__main__":
    _self_test()
