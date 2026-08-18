# D 阶段 · 合规基座（护栏4/5/6）— Q2/Q3/Q4 总览

> 阶段：D（R1 合规基座，循环自驱）｜2026-08-18 用户战略定位=真上线产品，护栏4/5/6 由「用户延后」升为「循环可备设计文档+代码骨架」。
> **重要诚实边界**：护栏4/5/6 此前由用户 2026-08-17 明确**延后**，非「排除」。本轮按 R1 补**设计文档 + 代码编排骨架**；但以下仍仅用户可做（不伪造完成）：
> - Q5 上线部署 / 真实凭据 / KMS 主密钥配置（物理动作）
> - Q7 PIPL 上线前法定最终签署（律师签字）
> - Q4 法检专家复核动作由真实专家执行
> 这些属「用户风险自担、由循环备基座」的显式分工，已如实登记，不伪称「已合规」。

## 交付物清单
| 护栏 | 任务 | 设计文档 | 代码骨架（已单测） |
|---|---|---|---|
| 4 | Q2 灰度+回滚 | `design/guardrails/gray-release.md` | `scaffold/src/feature_flags.py`（fail-safe 默认关 + kill-switch） |
| 5 | Q3 PIPL crypto-shred | `design/guardrails/pipl-crypto-shred.md`（引用 `PIPL合规设计补充.md`） | `scaffold/src/crypto_shred.py`（KEK 销毁→历史备份不可解密） |
| 6 | Q4 法检痕迹 | `design/guardrails/legal-audit-trail.md` | `scaffold/src/audit_log.py`（SHA256 哈希链，篡改可检） |

## 单测
`scaffold/tests/test_guardrails.py`：test_feature_flags / test_crypto_shred / test_audit_log — 三护栏编排逻辑全绿。

## 与既有设计对齐
- Q3 直接复用 `PIPL合规设计补充.md`（§24 + DSAR 全链路）与 `密钥工程 LLD`（Argon2id/HKDF/信封）——crypto-shred 是其落地环节。
- Q2 复用 `ci-cd.yml`（build+test+契约闸门）作发布门禁；kill-switch 为运行时止血。
- Q4 复用 `审计日志`（隐私 LLD 已提去标识）+ 本文件哈希链增强可验证性。

## 仍待用户决策点（询问区，未臆测）
- 灰度策略取值（百分比/白名单）→ 运维发布前配置。
- 真实 KEK 派生/KMS 主密钥 → 用户提供（Q5）。
- 律师 §24 适用性/告知文案/DSAR SLA 签字 → （Q7）。
- 法检专家复核 → 用户安排真实专家（Q4 法检动作）。
