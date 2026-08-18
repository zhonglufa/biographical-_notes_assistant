"""guard/audit_log.py — 审计日志 / 法检复核痕迹（护栏 6 · 迁移自 scaffold audit_log.py）

设计目标（见 design/guardrails/legal-audit-trail.md）：
- 关键动作（合规相关、权限变更、删除请求、灰度开关、成本护栏熔断）写入追加式审计日志，
  逐条哈希并链接前一条(prev_hash)形成链条。
- 提供 verify_chain() 检测任何历史条目被篡改。

诚实边界（R4 / 用户决策点）：
- 本文件是 **审计链编排**（哈希链 + 校验），可独立单测。
- 真实生产需补：写入落库(append-only store)、写入方身份认证、专家复核动作由真实专家执行；
  本文件仅提供可验证的痕迹结构。迁移时逻辑保持不变。
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time


class AuditLog:
    def __init__(self, path: str | None = None) -> None:
        self._lock = threading.Lock()
        self._path = path
        self._entries: list[dict] = []
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = []

    def append(self, actor: str, action: str, target: str,
               decision: str = "", meta: dict | None = None) -> str:
        with self._lock:
            prev_hash = self._entries[-1]["hash"] if self._entries else "GENESIS"
            rec = {
                "ts": int(time.time() * 1000),
                "actor": actor,
                "action": action,
                "target": target,
                "decision": decision,
                "meta": meta or {},
                "prev_hash": prev_hash,
            }
            rec["hash"] = self._hash(rec)
            self._entries.append(rec)
            if self._path:
                self._persist()
            return rec["hash"]

    def verify_chain(self) -> bool:
        with self._lock:
            prev = "GENESIS"
            for e in self._entries:
                if e.get("prev_hash") != prev:
                    return False
                if e.get("hash") != self._hash(e):
                    return False
                prev = e["hash"]
            return True

    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    def _hash(self, rec: dict) -> str:
        payload = {k: rec[k] for k in ("ts", "actor", "action", "target", "decision", "meta", "prev_hash")}
        s = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(s).hexdigest()

    def _persist(self) -> None:
        if not self._path:
            return
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
