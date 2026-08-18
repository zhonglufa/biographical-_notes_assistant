"""
护栏4/5/6 合规基座单测（Q2/Q3/Q4 · R1 可自驱代码骨架）。
对应：feature_flags.py(灰度/kill-switch) / crypto_shred.py(PIPL crypto-shred) / audit_log.py(法检哈希链)。
注意：均为编排逻辑单测；真实密钥派生/KMS/落库/专家复核动作仍属用户决策点(Q5/Q7)。
"""
import sys
sys.path.insert(0, "src")
from base import check
from feature_flags import FeatureFlags
from crypto_shred import CryptoShred
from audit_log import AuditLog
import tempfile, os


def test_feature_flags():
    ff = FeatureFlags(flags={"payment": False})
    check("灰度默认关闭(fail-safe)", ff.is_enabled("payment") is False)
    ff.set_override("payment", True)
    check("override 生效", ff.is_enabled("payment") is True)
    ff.trigger_kill_switch(True)
    check("kill-switch 强制全关", ff.is_enabled("payment") is False)
    check("kill-switch 覆盖默认开功能", ff.is_enabled("ai_match") is False)
    ff.trigger_kill_switch(False)
    check("kill-switch 解除", ff.is_enabled("ai_match") is True)


def test_crypto_shred():
    cs = CryptoShred()
    cs.register_kek("u1", b"16bytesecretkey!!")
    blob = cs.encrypt_with("u1", b"pii")
    check("加密后可解密", cs.decrypt_with("u1", blob) == b"pii")
    cs.shred_user("u1")
    check("shred 标记置位", cs.is_shredded("u1") is True)
    try:
        cs.decrypt_with("u1", blob)
        check("shred 后拒绝解密", False)
    except PermissionError:
        check("shred 后拒绝解密(历史备份不可解密)", True)


def test_audit_log():
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        log = AuditLog(p)
        log.append("user", "dsar.delete.request", "u1", "pending")
        log.append("system", "dsar.purge", "u1", "done")
        log.append("legal", "review.approve", "a-1", "approved")
        check("初始哈希链有效", log.verify_chain() is True)
        log._entries[0]["decision"] = "tampered"
        check("篡改后链失效(可检测)", log.verify_chain() is False)
    finally:
        os.remove(p)


if __name__ == "__main__":
    test_feature_flags()
    test_crypto_shred()
    test_audit_log()
    print("\n✅ 护栏基座单测全部通过（Q2/Q3/Q4 编排逻辑）")
