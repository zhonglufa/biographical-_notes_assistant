# 护栏6 · 法检专家复核痕迹（可追溯设计）— Q4

> 阶段：D（Q4，R1 合规基座）｜关联：`scaffold/src/audit_log.py`（防篡改哈希链，已落地单测）、`design/PIPL合规设计补充.md`
> 诚实边界：本文件提供**可验证的审计痕迹结构**；**专家复核动作本身由真实法检专家执行**（用户安排），本文件不替代专家判断。

## 1. 目标
关键动作（合规相关 / 权限变更 / 删除请求 / 灰度开关 / 支付）留**不可篡改、可验证**的痕迹，供法检/审计追溯。对齐行业审计日志实践（append-only + 哈希链）。

## 2. 审计链编排（`audit_log.py`）
- 每条记录：`{ts, actor, action, target, decision, meta, prev_hash, hash}`。
- `hash = SHA256(规整化记录 + prev_hash)`；逐条链接形成链。
- `verify_chain()`：重算每条哈希并比对 prev_hash，任一历史篡改即检出。

## 3. 须审计的动作清单（建议）
| 动作 | actor | 说明 |
|---|---|---|
| dsar.delete.request | user | 用户发起删除（被遗忘权） |
| dsar.purge | system | 系统执行 purge（含 crypto-shred） |
| ai_match.toggle | user | §24 自动化决策开关变更 |
| gray.kill_switch | admin | 灰度全局回滚 |
| payment.order | user | 支付下单 |
| legal.review | legal_expert | 法检专家复核结论 |

## 4. 生产必补（用户决策点）
- 写入落库（append-only store，非本地临时文件）。
- 写入方身份认证（actor 不可伪造）。
- 专家复核动作由真实法检专家经专家系统执行（Q4 法检）。

## 5. 验收
- [x] 审计哈希链单测通过（test_guardrails.py::test_audit_log：篡改可检测）
- [ ] 落库 + 身份鉴权 + 专家复核接入（用户安排法检）
