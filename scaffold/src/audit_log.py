"""
审计日志 / 法检复核痕迹（护栏6 · Q4）— 防篡改哈希链。

设计目标（见 design/guardrails/legal-audit-trail.md）：
- 关键动作（合规相关、权限变更、删除请求、灰度开关）写入追加式审计日志，逐条哈希并链接前一条(prev_hash)形成链条。
- 提供 verify_chain() 检测任何历史条目被篡改。

诚实边界（R4 / 用户决策点）：
- 本文件是 **审计链编排**（哈希链 + 校验），可独立单测。
- 真实生产需补：写入落库(append-only store)、写入方身份认证、专家复核动作由真实专家(Q4 法检)执行；本文件仅提供可验证的痕迹结构。
"""
import hashlib
import json
import os
import threading
import time

class AuditLog:
    def __init__(self, path=None):
        self._lock = threading.Lock()
        self._path = path
        self._entries = []
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = []

    def append(self, actor: str, action: str, target: str, decision: str = "", meta: dict = None):
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

    def entries(self):
        with self._lock:
            return list(self._entries)

    def _hash(self, rec):
        payload = {k: rec[k] for k in ("ts", "actor", "action", "target", "decision", "meta", "prev_hash")}
        s = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(s).hexdigest()

    def _persist(self):
        if not self._path:
            return
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _self_test():
    import tempfile, os as _os
    fd, p = tempfile.mkstemp(suffix=".json")
    _os.close(fd)
    try:
        log = AuditLog(p)
        log.append("user", "dsar.delete.request", "user-1", "pending")
        log.append("system", "dsar.purge", "user-1", "done")
        log.append("legal", "review.approve", "audit-2026-001", "approved")
        assert log.verify_chain() is True, "初始链应有效"
        # 篡改一条历史记录
        log._entries[0]["decision"] = "tampered"
        assert log.verify_chain() is False, "篡改后链应失效"
        print("audit_log 自测通过 ✅（哈希链可检测篡改）")
    finally:
        _os.remove(p)


if __name__ == "__main__":
    _self_test()
