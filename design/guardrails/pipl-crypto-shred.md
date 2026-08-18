# 护栏5 · PIPL crypto-shred + 合规设计 — Q3

> 阶段：D（Q3，R1 合规基座）｜关联：`design/PIPL合规设计补充.md`（§24+DSAR 全链路）、`scaffold/src/crypto_shred.py`（crypto-shred 编排，已落地单测）、`密钥工程 LLD`
> 诚实边界：**删除链路 DSAR 编排已闭环设计**；唯一剩余为**律师合规签字（Q7 法定签署，仅用户）**与**真实 KEK 派生/KMS（Q5 物理动作，仅用户配主密钥）**。本文件不替代法律意见。

## 1. 目标（PIPL §24 / 被遗忘权 / 备份凭证失效）
用户删除请求触发后：MySQL 软删→purge + 本机 SQLite 清 + 日志去标识 + **备份 crypto-shred（销毁该用户 KEK → 历史备份不可解密）**。对齐 `PIPL合规设计补充.md §2.3`。

## 2. crypto-shred 编排（`crypto_shred.py`）
- 信封加密：数据用 DEK 加密，DEK 用 KEK 包装。
- `shred_user(kek_id)`：销毁 KEK（内存清除 + 标记 shredded）→ 该用户所有历史加密备份（含离线）不可解密。
- `decrypt_with` 在 KEK 已销毁时抛 `PermissionError`（拒绝解密 = crypto-shred 生效）。

## 3. 真实密钥派生（生产必做，用户决策点）
- 必须用 **密钥工程 LLD** 的 Argon2id + HKDF 合成 KEK，存放于 **OS 安全区/信封**；主密钥经 **KMS/用户配置**（Q5）。
- `MockCipher`（XOR+HMAC）**仅自测用，非生产级**；生产必须把 `Cipher` 换成 `cryptography`(AES-GCM) + 真实信封，否则不得上线。

## 4. 删除链路（端到端，引用 PIPL补充 §2.3）
```
用户删除 → MySQL 软删(deleted_at, 7d 可逆) → 异步 purge(物理删，跳过 member_order 财务留存)
→ 本机 Agent 收 dsar.purge → 清本地 SQLite + 清 Cookie 信封
→ 日志 user_id 哈希去标识 → 备份 crypto-shred(销毁用户 KEK)
```

## 5. 验收
- [x] crypto-shred 编排单测通过（test_guardrails.py::test_crypto_shred：销毁后历史备份不可解密）
- [ ] 真实 KEK 派生接 密钥工程 LLD + KMS（用户配主密钥，Q5）
- [ ] DSAR 删除链路端到端联调（MySQL+本机+日志+备份）
- [ ] 律师签字：§24 适用性 + 告知文案 + DSAR SLA（Q7）
