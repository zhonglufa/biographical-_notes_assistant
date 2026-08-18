"""
PIPL crypto-shred（护栏5 · Q3）— 密钥销毁使历史备份不可解密。

设计目标（见 design/guardrails/pipl-crypto-shred.md + design/PIPL合规设计补充.md §2.3）：
- 信封加密：数据用 DEK 加密，DEK 用 KEK 包装；删除用户时**销毁其 KEK** → 历史备份中该用户凭证不可解密（crypto-shred）。
- 本文件是 **crypto-shred 编排逻辑**：KEK 注册表 + 销毁 KEK → 标记 shredded → 拒绝解密。

诚实边界（R4 / 用户决策点）：
- 真实 KEK 派生必须用 密钥工程 LLD 的 Argon2id + HKDF + OS 安全区/信封，**真实 KMS/主密钥仅用户配置**（Q7/Q5 物理动作）。
- 本文件自带 MockCipher（XOR + HMAC，仅自测用，**非生产级**）；生产必须把 `Cipher` 换成 `cryptography`(AES-GCM) + 真实信封，否则不得上线。
"""
import hashlib
import hmac
import json
import os
import threading

class MockCipher:
    """自测用占位密码器：XOR 流 + HMAC。明确 NOT production-grade。"""
    def __init__(self, key: bytes):
        self._key = key
    def encrypt(self, plaintext: bytes) -> bytes:
        key = self._key
        ct = bytes((b ^ key[i % len(key)]) for i, b in enumerate(plaintext))
        return ct + hmac.new(key, ct, hashlib.sha256).digest()
    def decrypt(self, blob: bytes) -> bytes:
        ct, mac = blob[:-32], blob[-32:]
        exp = hmac.new(self._key, ct, hashlib.sha256).digest()
        if not hmac.compare_digest(exp, mac):
            raise ValueError("MAC 校验失败")
        key = self._key
        return bytes((b ^ key[i % len(key)]) for i, b in enumerate(ct))


class CryptoShred:
    def __init__(self, cipher_factory=None):
        self._lock = threading.Lock()
        self._keks = {}          # kek_id -> {"key": bytes, "shredded": bool}
        self._cipher_factory = cipher_factory or (lambda key: MockCipher(key))

    def register_kek(self, kek_id: str, key: bytes):
        with self._lock:
            self._keks[kek_id] = {"key": key, "shredded": False}

    def encrypt_with(self, kek_id: str, plaintext: bytes) -> bytes:
        with self._lock:
            kek = self._keks.get(kek_id)
            if not kek or kek["shredded"]:
                raise PermissionError(f"KEK {kek_id} 已销毁/不存在，拒绝加密")
            return self._cipher_factory(kek["key"]).encrypt(plaintext)

    def decrypt_with(self, kek_id: str, blob: bytes) -> bytes:
        with self._lock:
            kek = self._keks.get(kek_id)
            if not kek:
                raise PermissionError(f"KEK {kek_id} 不存在")
            if kek["shredded"]:
                # crypto-shred：销毁后历史备份不可解密
                raise PermissionError(f"KEK {kek_id} 已销毁（crypto-shred），历史备份不可解密")
            return self._cipher_factory(kek["key"]).decrypt(blob)

    def shred_user(self, kek_id: str):
        """销毁 KEK：使该用户所有历史加密备份（含离线备份）不可解密。"""
        with self._lock:
            kek = self._keks.get(kek_id)
            if kek:
                kek["shredded"] = True
                kek["key"] = b""  # 从内存清除

    def is_shredded(self, kek_id: str) -> bool:
        with self._lock:
            kek = self._keks.get(kek_id)
            return bool(kek and kek["shredded"])


def _self_test():
    cs = CryptoShred()
    cs.register_kek("user-kek-1", b"16bytesecretkey!!")
    blob = cs.encrypt_with("user-kek-1", b"resume-pii-data")
    assert cs.decrypt_with("user-kek-1", blob) == b"resume-pii-data"
    cs.shred_user("user-kek-1")
    assert cs.is_shredded("user-kek-1") is True
    try:
        cs.decrypt_with("user-kek-1", blob)
        raise AssertionError("shred 后仍可解密 → 失败")
    except PermissionError:
        pass
    print("crypto_shred 自测通过 ✅（编排逻辑；真实密钥派生待接 密钥工程 LLD + KMS）")


if __name__ == "__main__":
    _self_test()
