"""delivery_state_machine.py — 10 态投递状态机（服务端中枢 · B2-2）

状态严格对齐 applications-list.response.schema.json 的 status 枚举：
  pending_confirm / autofilling / submitted / viewed / contacting /
  interview_invited / interview_done / offer / rejected / closed

转移矩阵对齐 LLD-投递状态机模块 v1.0 §1（ADR-008）：无回退边；
rejected / closed 为终态；所有转移写审计日志。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional


# 终态：不可再转移
TERMINAL = {"rejected", "closed"}

# 允许转移矩阵（当前态 -> 可到达的下一态集合）
TRANSITIONS: Dict[str, set] = {
    "pending_confirm": {"autofilling"},
    "autofilling": {"submitted", "closed", "pending_confirm"},
    "submitted": {"viewed", "rejected", "closed"},
    "viewed": {"contacting", "rejected", "closed"},
    "contacting": {"interview_invited", "rejected", "closed"},
    "interview_invited": {"interview_done", "rejected", "closed"},
    "interview_done": {"offer", "rejected", "closed"},
    "offer": {"closed"},
    "rejected": set(),
    "closed": set(),
}


class InvalidTransition(Exception):
    """非法状态转移（自环 / 回退 / 终态再转 / 未知态）。"""


@dataclass
class AuditEntry:
    task_id: str
    from_state: str
    to_state: str
    reason: Optional[str]
    ts: int


class DeliveryStateMachine:
    """内存版 10 态投递状态机（演示 + 单测；生产用 MySQL + Redis 幂等键）。"""

    def __init__(self, now=None) -> None:
        self._state: Dict[str, str] = {}
        self._audit: Dict[str, List[AuditEntry]] = {}
        self._now = now or (lambda: int(time.time() * 1000))

    # ---- 生命周期 ----
    def create(self, task_id: str, initial: str = "pending_confirm") -> str:
        if task_id in self._state:
            raise InvalidTransition(f"task {task_id} 已存在")
        if initial != "pending_confirm":
            raise InvalidTransition("初始态必须为 pending_confirm")
        self._state[task_id] = initial
        self._audit[task_id] = []
        return initial

    def state(self, task_id: str) -> str:
        if task_id not in self._state:
            raise KeyError(f"未知 task {task_id}")
        return self._state[task_id]

    def can_transition(self, task_id: str, to_state: str) -> bool:
        cur = self._state.get(task_id)
        if cur is None:
            return False
        return to_state in TRANSITIONS.get(cur, set())

    def transition(self, task_id: str, to_state: str, *, reason: Optional[str] = None) -> str:
        cur = self._state.get(task_id)
        if cur is None:
            raise KeyError(f"未知 task {task_id}")
        if to_state == cur:
            raise InvalidTransition(f"{task_id}: 自环 {cur} -> {to_state} 不允许")
        if to_state not in TRANSITIONS.get(cur, set()):
            raise InvalidTransition(f"{task_id}: 非法转移 {cur} -> {to_state}")
        self._state[task_id] = to_state
        self._audit.setdefault(task_id, []).append(
            AuditEntry(task_id, cur, to_state, reason, self._now()))
        return to_state

    def audit(self, task_id: str) -> List[AuditEntry]:
        return list(self._audit.get(task_id, []))

    @staticmethod
    def idempotency_key(user_id: str, platform: str, job_id: str, apply_date: str) -> str:
        """幂等四元组 (user_id, platform, job_id, apply_date)，对齐 HLD §6.13.2 / ADR-004。"""
        return f"{user_id}|{platform}|{job_id}|{apply_date}"
