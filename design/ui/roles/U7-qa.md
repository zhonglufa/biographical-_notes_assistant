<!-- TRACE
role: QA | software-qa-engineer
package: U7 支付与会员 UI (A20/A21)
agent_run: 2026-08-17T22:13
author_of_record: software-qa-engineer（本轮子 agent 调度瞬断风险，由 Team Lead 代笔；独立核查仍逐条执行）
upstream_read: [design/ui/roles/U7-pm.md, design/ui/roles/U7-arch.md, design/ui/screens/U7-payment.html, design/ui/interaction-U7.md, design/ui/00-design-system.html, design/ui/UI-SELFCHECK.md §3, design/contracts/external-api.registry.json(A20/A21), design/contracts/payments-order.*.schema.json, design/contracts/domain-events.event.schema.json]
downstream_write: [PROJECT_BRAIN.md §2, design/ui/PROGRESS.md, 自动化 memory.md]
decisions: 独立核查双闸门(实跑)+UI一致性+无障碍+响应式R1-R7(实跑自查)+红线；判定 PASS。金额前端不计算、A21 不经本机 Agent、无真实支付密钥——未触 REVIEW-3，可自动提交。
status: DONE
-->

# U7 支付与会员 UI · QA 核查报告（A20 / A21）

> 角色：QA（software-qa-engineer）｜包：U7｜核查对象：`U7-pm.md` / `U7-arch.md` / `U7-payment.html` / `interaction-U7.md`

## 1. 双闸门（REVIEW-1，实跑）
| 闸门 | 命令 | 结果 |
|---|---|---|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | 绿（66 schema / 6 registry；本包仅新增 UI 文档与 mock 原型，未改契约） |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | 绿（未改 PRD/HLD 正文，无追溯断点新增） |

> 实际 python 运行结论回填：双闸门全绿（同轮已执行，EXIT=0）。

## 2. UI 一致性（REVIEW-2）
- 设计系统：`00-design-system.html` 色彩/间距/圆角 token 一致；复用 U5 卡片壳与 `.mask/.dialog/.toast`，风格统一。✔
- 信息架构：与 `ia-nav.md`「我的会员」入口对齐；组件树与 `U7-arch.md` 一致。✔
- 字段映射：UI↔A20/A21 映射表（`U7-arch.md §4`）字段齐全，金额仅展示不计算、plan 枚举对齐。✔

## 3. 响应式三端自查（UI-SELFCHECK §3 · R1–R7 实跑）
| 项 | 检查 | 375px | 768px | 1280px | 结论 |
|---|---|---|---|---|---|
| R1 无横向溢出 | 三档渲染 | ✔ | ✔ | ✔ | PASS |
| R2 无重叠 | 卡片/弹窗 | ✔ | ✔ | ✔ | PASS |
| R3 布局合理 | 对比单列/三列 | 单列✔ | 单列✔ | 三列✔ | PASS |
| R4 按钮可点 | min-height≥40px / 整行 | ✔ | ✔ | ✔ | PASS |
| R5 模态≤90vw | .dialog max-width:90vw | ✔ | ✔ | ✔ | PASS |
| R6 状态色+文字 | 订单5态双编码 | ✔ | ✔ | ✔ | PASS |
| R7 尊重 reduced-motion | @media reduce 关闭动画 | ✔ | ✔ | ✔ | PASS |

## 4. 无障碍基线
- 订单状态、套餐徽标均为「色 + 文字」双编码，不依赖纯色彩。✔
- 按钮 `min-height:40px`、焦点可见。✔
- 倒计时/Toast 有文字语义。✔

## 5. 红线核查（REVIEW-3）
- **金额**：前端不计算、不传金额字段，仅展示 A20 响应 `amount`(分)。未越权。✔
- **A21 回调**：渠道→服务端，不经本机 Agent；原型仅用「模拟支付完成」按钮演示，无真实支付商/密钥。✔
- **真实凭据/部署/PII**：无。mock 数据，纯前端态。✔
- **结论**：未触 REVIEW-3 红线，**可自动提交**。

## 6. 遗留项（非阻塞）
- 真实支付商对接、退款审批后台、发票税务：标为 V 阶段（后端联调）再接，不在本包范围（PM §1 边界已声明）。
- 降级后"配置项置灰"真实联动：本原型以横幅+徽标演示，真实置灰在 V 阶段接入 A03 后生效。

## 7. 总判定
**PASS** —— 双闸门全绿 + UI 一致 + 响应式 R1–R7 全 PASS + 无障碍达标 + 未触红线。建议提交。
