<!-- TRACE
role: Team Lead | 交付台账(工作留痕总账)
package: 多角色流水线 · 交付台账
agent_run: 2026-08-17T20:52
author_of_record: Team Lead
upstream_read: [design/ui/ROLE-WORKBOOK.md, PROJECT_BRAIN.md §9]
downstream_write: [PROJECT_BRAIN.md §2/§9, design/ui/PROGRESS.md]
decisions: U1–U4 为单 agent 时代产物(仅 screen+interaction，无四角色拆分)，如实标 legacy；U5 起按 ROLE-WORKBOOK 四角色齐全且互相引用。
status: DONE
-->

# 角色交付台账（工作留痕总账）

> 每行一个包，登记四角色产物与状态。这是"每人工作+互相参考+留痕"的可审计总账。
> 规范见 `ROLE-WORKBOOK.md`。⚠️ U1–U4 为**多角色升级前**由单 agent 产出，仅含 screen+interaction，**无独立 PM/架构师/QA 产物**，如实标注 `legacy`。

| 包 | 契约 | PM | 架构师 | 工程师(screen) | 工程师(interaction) | QA | 双闸门 | 状态 |
|---|---|---|---|---|---|---|---|---|
| U0 设计系统 | — | legacy | legacy | [00-design-system.html](00-design-system.html) | [ia-nav.md](ia-nav.md) | legacy | 绿 | ✅ |
| U-动效 | — | legacy | legacy | [02-motion-system.html](02-motion-system.html) | — | legacy | 绿 | ✅ |
| U1 简历工作台 | A04/05/06 | legacy | legacy | [screens/U1-resume.html](screens/U1-resume.html) | [interaction-U1.md](interaction-U1.md) | legacy | 绿 | ✅ |
| U2 岗位浏览 | A07/08 | legacy | legacy | [screens/U2-jobs.html](screens/U2-jobs.html) | [interaction-U2.md](interaction-U2.md) | legacy | 绿 | ✅ |
| U3 投递管理 | A09/10/11 | legacy | legacy | [screens/U3-applications.html](screens/U3-applications.html) | [interaction-U3.md](interaction-U3.md) | legacy | 绿 | ✅ |
| U4 策略配置 | A12/13 | legacy | legacy | [screens/U4-strategy.html](screens/U4-strategy.html) | [interaction-U4.md](interaction-U4.md) | legacy | 绿 | ✅ |
| **U5 适配器管理** | **A14/15** | [roles/U5-pm.md](roles/U5-pm.md) | [roles/U5-arch.md](roles/U5-arch.md) | [screens/U5-adapter.html](screens/U5-adapter.html) | [interaction-U5.md](interaction-U5.md) | [roles/U5-qa.md](roles/U5-qa.md) | ✅ 绿(实跑) | ✅ 四角色齐全 |
| U6 面试模拟 | A16–19 | — | — | — | — | — | — | ⏳ |
| U7 支付会员 | A20/21 | — | — | — | — | — | — | ⏳ |
| U8 通知中心 | A22/23 | — | — | — | — | — | — | ⏳ |
| U9 每日日报 | A24/25 | — | — | — | — | — | — | ⏳ |
| U10 用户登录 | A01/02/03 | — | — | — | — | — | — | ⏳ |
| U11 交互总纲 | — | — | — | — | — | — | — | ⏳ |

**图例**：✅ 完成｜🔄 进行中｜⏳ 待续｜legacy = 多角色升级前的单 agent 产物（无四角色拆分）
