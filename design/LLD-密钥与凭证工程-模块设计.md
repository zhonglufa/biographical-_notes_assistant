# LLD-密钥与凭证工程-模块设计（v1.0）

> 重导出自 HLD §6.8 / §6.14.2 / §20.5 / §30.7 / §31.4 / §31.7 / ADR-018。
> 本文档闭环 HLD §9.4「§31.7 密钥轮换与泄露全量吊销工程」的 LLD 细化。本机 Cookie 金库的设备密钥派生（Argon2id / HKDF / OS 安全区）已在 HLD §6.14.8 与 `LLD-本机Agent与投递执行-模块设计.md` §5.2 落地，本文档仅引用，不重复。

## 0. 为什么单独成模块

密钥与凭证横跨服务端（KMS / 配置中心）、传输（JWT / token）、构建（签名 CRL）、本机（Cookie 金库），是安全红线模块。其"轮换 + 泄露全量吊销"是 PRD §31.7 明确要求但 HLD §6.8 仅给原则的工程流程，须独立 LLD 细化以便审计与编码落地。

## 1. 范围与边界

| 范围 | 内容 | 落地位置 |
|------|------|---------|
| 服务端密钥 | LLM Key / 推送证书 / 主密钥 / DEK | 本文档 §3–§5 |
| 信封加密 | AES-256-GCM + KMS(DEK 包裹 KEK) | HLD §6.14.2（算法套件已拍板），本文档 §3 引用 |
| API token | access(15min) + refresh(可吊销) | 本文档 §6 |
| Agent 签名密钥 | 更新签名密钥 CRL | 本文档 §7 |
| 本机 Cookie 金库 | 设备密钥派生 / KEK 合成 | 引用 HLD §6.14.8 + 本机Agent §5.2 |

**不在范围**：① 本机 Cookie 明文派生细节（已在别处落地）；② PIPL 数据携带权 / 被遗忘权（§25.6 / §31.11，属法务协同，用户已延后，本文档不展开）。

## 2. 模块分解与职责

| 类 | 职责 | 关键方法 |
|----|------|---------|
| `KeyVaultService` | 密钥版本化存储与读取（经 KMS） | `issueDataKey(version)` / `getActiveVersion(scope)` / `deprecate(version)` |
| `RotationScheduler` | 按策略触发轮换（默认 90 天） | `onSchedule()` / `forceRotate(scope)` |
| `RevocationEngine` | 泄露全量吊销编排 | `revokeKeyVersion(version)` / `reEncryptAffected(scope, fromVer, toVer)` |
| `TokenService` | API token 签发 / 校验 / 吊销 | `issue(userId)` / `validate(jti)` / `revoke(jti)` |
| `SigningCrlDist` | Agent 二进制签名密钥 CRL 分发 | `publish(revokedKidSet)` / `isRevoked(kid)` |

## 3. 信封加密与版本化轮换（§20.5 / §31.7）

```
pre:  业务敏感字段写入（简历原文等）
post: 密文 + DEK 版本号落库；KEK 经 KMS 包裹，主密钥与数据密钥分离
edge:  KMS 不可达→写操作失败(不降级明文)；轮换中旧版本保留解密能力

# 加密
dek      = KeyVaultService.issueDataKey(active_version)   # AES-256-GCM 随机 DEK
cipher   = AES-256-GCM.encrypt(dek, plaintext)
store(cipher, dek_version)                                 # 密文 + 版本号，KEK 不落库

# 轮换（默认 90 天，RotationScheduler.onSchedule）
new_ver  = KeyVaultService.issueDataKey(next_version)      # 新 DEK，旧版本保留
KeyVaultService.getActiveVersion(scope) = new_ver          # 新写入走新版本
# 旧版本不立即失效：历史密文仍可用旧版本解密（版本化，不重写历史）

complexity: O(1) 加密；轮换 O(1) 元数据切换
```

## 4. 泄露全量吊销工程（§31.7 核心，PRD §31.7）

触发：SIEM / 人工确认某 `dek_version` 或主密钥泄露。

```
pre:  revoke_key_version(version) 被调用（version 为已泄露版本）
post: 该版本停止用于新加密；受影响数据全量重加密到新版本；旧版本解密窗口关闭；全程审计留痕
edge: 重加密失败→重试≤3 + 告警升级；不阻塞读（旧版本保留解密直至重加密完成）

steps:
  1. deprecate(version)                  # 标记 deprecated，KeyVaultService 停止发放该版本新 DEK
  2. KMS.revoke(version)                 # KMS 层吊销该 DEK 版本（不可再 unwrap）
  3. affected = scan(scope, dek_version=version)   # 定位受影响记录（表/字段/时间窗）
  4. for rec in affected:
       plain = AES-256-GCM.decrypt(old_dek, rec.cipher)   # 旧版本仍可读（窗口内）
       new_cipher = AES-256-GCM.encrypt(new_dek, plain)
       store(rec, new_cipher, new_version)
  5. old_version.decrypt_enabled = false  # 重加密完成后关闭旧版本解密窗口
  6. audit_log(revocation: {version, affected_count, started_at, finished_at, operator})
  7. notify(SecOps) + 纳入 §6.6 Runbook「密钥泄露全量吊销」计 MTTD/MTTR（§24.6）

RTO 目标: 确认→重加密完成 ≤ 4h（建议值，由 SecOps SLA 定）
读取不中断: 步骤 4 完成前旧版本保留解密，保证业务可读
```

> 关键：吊销是"版本级"而非"密钥级销毁"——旧版本解密窗口在重加密完成后才关闭，避免"吊销即不可读"造成数据不可用。影响面收敛通过 `affected` 扫描的表/字段/时间窗精确界定，不盲目全表锁。

## 5. 主密钥与 KMS 隔离

- 主密钥（KEK）存 KMS，不入仓 / 不硬编码 / 不打日志（HLD §6.8 / §6.9 CI 密钥扫描门禁拦截）。
- 三环境（dev / staging / prod）KMS 域隔离，prod 凭证不进 dev / staging（HLD §6.8 三环境隔离）。
- 主密钥轮换同样走 §3 版本化流程，旧版本保留解密历史。

## 6. API token 短期化与吊销（§31.4）

```
pre:  用户登录成功
post: 签发 access(15min) + refresh(可吊销)；泄露窗口受限
edge:  refresh 入黑名单→校验拒绝；access 自然过期(15min)

access   = JWT.sign(RS256, {sub, exp=now+15min, jti})
refresh  = TokenService.issue(userId)          # jti 入 Redis 黑名单可吊销
on logout/泄露: TokenService.revoke(jti)        # refresh 入黑名单；access 等自然过期
middleware: validate(jti) → 黑名单命中即拒
```

## 7. Agent 二进制签名密钥 CRL（§30.7）

- 更新签名密钥设撤销列表（CRL），`SigningCrlDist.publish(revokedKidSet)` 分发。
- Agent 启动加载时 `isRevoked(kid)` 命中→拒绝该旧构建加载，强制升级到新签名构建。
- 密钥泄露即吊销，旧构建不可加载（与 break-glass / 自更新回滚协同，HLD §29.3 / §30.7）。

## 8. 错误处理设计

| 错误码 | 检测 | 恢复策略 |
|--------|------|----------|
| KEY_KMS_UNAVAILABLE | KMS 不可达 | 写操作失败（不降级明文）；读操作若版本可用则继续；告警 |
| KEY_REENCRYPT_FAILED | 重加密步骤异常 | 重试≤3 + 告警升级；保留旧版本解密窗口 |
| TOKEN_REVOKED | refresh jti 在黑名单 | 校验拒绝；要求重新登录 |
| SIGN_KID_REVOKED | Agent 签名 kid 在 CRL | 拒绝加载旧构建；提示升级 |

> 纪律：密钥相关错误一律 fail-closed（不降级明文、不绕过校验），与 HLD §6.14.1 受限安全模式一致。

## 9. 可追溯性（→ HLD / PRD）

| LLD | HLD | PRD |
|-----|-----|-----|
| §3 信封加密版本化 | §6.8 / §6.14.2 | §20.5 / §31.7 |
| §4 泄露全量吊销 | §6.8 | §31.7 |
| §6 token 短期化 | §6.8 | §31.4 |
| §7 签名 CRL | §6.8 | §30.7 |

## 10. 交付自检清单

- [x] 信封加密算法套件引用已拍板（AES-256-GCM + KMS，HLD §6.14.2）
- [x] 版本化轮换流程（§3）
- [x] 泄露全量吊销工程 7 步 + RTO 目标 + 不中断读（§4，闭合 §31.7）
- [x] API token 短期化 + 吊销列表（§6）
- [x] Agent 签名密钥 CRL（§7）
- [x] fail-closed 错误纪律（§8）
- [x] 可追溯性矩阵（§9）
- [ ] 图形化时序图（按《图交付标准》另出，不阻塞实现）

---

> 本文件为交付级 LLD v1.0：闭环 HLD §9.4「§31.7 密钥轮换与泄露全量吊销工程」；不含 PIPL 数据携带权 / 被遗忘权（§25.6 / §31.11，用户已延后，法务协同）。
