<!-- TRACE
role: PM | software-product-manager
package: U7 支付与会员 UI (A20/A21)
agent_run: 2026-08-17T22:13
author_of_record: software-product-manager（本轮子 agent 调度瞬断风险，由 Team Lead 代笔，见 ROLE-DELIVERABLES.md 注）
upstream_read: [prd/PRD-简历自动投递与面试模拟-最终版.md §12(定价/套餐)/§20(订阅)/§22.2(支付对账)/§769-802(角色权限矩阵/降级)/§1167-1171(支付全局异常), design/contracts/external-api.registry.json(A20/A21), design/contracts/payments-order.request.schema.json, design/contracts/payments-order.response.schema.json, design/contracts/payments-callback.request.schema.json, design/contracts/domain-events.event.schema.json(paymentStatusChanged/memberPlanChanged), design/contracts/error-codes.json(PLAN_REQUIRED), design/ui/00-design-system.html, design/ui/ROLE-WORKBOOK.md §2]
downstream_write: [design/ui/roles/U7-arch.md, design/ui/screens/U7-payment.html, design/ui/interaction-U7.md]
decisions: 本包做"我的会员/支付中心"页（套餐展示+下单A20+支付状态+A21回调带来的权益生效+异常/降级）。A21 本身是渠道→服务端回调、不经本机 Agent、无用户直接 UI，但须把 payment.status.changed / member.plan.changed 事件落到前端状态（订单状态机+权益徽标）。金额由服务端权威计算（A20 响应 amount/分），客户端只传 plan/months，不从客户端取价（红线）。不做：真实支付商对接、退款审批后台、发票税务（PRD 标延后/非范围）。
status: DONE
-->

# U7 支付与会员 UI · 产品经理需求规格（A20 / A21）

> 角色：PM（software-product-manager）｜包：U7 支付与会员 UI｜对应契约：A20 创建会员订单、A21 支付渠道回调
> 配套：架构师产物 `U7-arch.md` ← 本文件被其引用；工程师产物 `U7-payment.html` + `interaction-U7.md` ← 本文件被其引用

## 1. 目标与范围
**目标**：让用户在 PC 端查看当前会员套餐与权益、对比并升级套餐（A20 下单）、跟踪支付状态、并在支付回调（A21）后看到权益即时生效；同时清晰呈现支付异常与会员降级的处理路径。
**范围（做）**：当前套餐卡片、套餐对比/升级入口、下单流程（A20）、支付状态展示、权益生效（A21 事件映射）、订单异常（失败/处理中/重复支付）、会员降级提示。
**范围（不做 · 边界）**：真实支付商（微信/支付宝）对接与密钥、退款审批后台、发票与税务细节、企业批量采购——这些属 PRD 延后/非范围能力，本包仅做前端状态与引导，标为后端联调阶段（V）再接。

## 2. 交互需求清单
| # | 交互 | 触发 | 行为 | 反馈 | 异常/边界 |
|---|------|------|------|------|-----------|
| R1 | 当前套餐展示 | 进入"我的会员"页 | GET /users/me(A03) 取 plan/quota | 卡片显示 free/pro/team 徽标 + 核心权益摘要 | 未登录→引导页（PRD §799）；配额超限→标红 |
| R2 | 套餐对比 | 渲染对比区 | 列出 免费/专业版/团队版 三档（价格/日上限30·100/面试次数3·10·∞/平台数等，对齐 §771-783、§479） | 三列卡片，当前套餐高亮 | — |
| R3 | 升级下单(A20) | 点某套餐"升级/续费" | 弹下单面板：选周期 months(1/3/6/12) → POST /payments/orders{plan,months,coupon?}(A20) | 返回 {orderNo,payUrl,amount(分),expireAt} → 展示支付二维码占位+订单号+倒计时 | 非登录→拦截；PLAN_REQUIRED(403)→提示升级；金额以响应为准，前端不计算 |
| R4 | 支付状态(A21) | 用户完成支付 / 轮询 | A21 回调→ payment.status.changed→ member.plan.changed → 前端刷新 plan 徽标+权益 | toast"已升级为专业版，权益已生效" | 回调未到账→"订单处理中"自动对账（§1168）；15min 定时对账兜底 |
| R5 | 订单状态机 | 订单卡片 | 状态：待支付→已支付→已开通→已过期→已退款（对齐 §22.2/§1505） | 每态对应色标+文案 | 待支付超 expireAt→已过期（24h 有效，§1168） |
| R6 | 支付失败/中断 | 下单后支付失败 | 展示"支付未完成"+「继续支付」回到 payUrl | 订单 24h 内有效（§1168） | 重复支付→同订单号直接返回既有权益（§1169），前端幂等提示 |
| R7 | 会员降级 | 套餐过期 | 自动降级 free，提示"配置已保留但不可修改，超限在途任务允许执行完毕"（§789/§802） | 降级横幅 + 配置项置灰 | 降级后升级→重新激活配置 |

## 3. 验收标准（逐条对应契约字段）
- AC1：下单仅向 A20 传 `{plan,months,coupon?}`，界面不展示/不传金额字段；下单成功后展示的 amount 直接来自 A20 响应（分→元换算仅展示）。
- AC2：订单状态机 5 态均可由 mock 数据驱动呈现（待支付/已支付/已开通/已过期/已退款），色标与文案正确。
- AC3：模拟 A21 回调（支付成功）后，会员徽标与权益摘要立即更新为对应 plan（free/pro/team/premium 映射一致）。
- AC4：重复支付场景——同一 orderNo 二次"支付完成"不重复开通、提示幂等（不报错、权益不变）。
- AC5：降级横幅在"过期"态出现，配置项置灰且不可点；升级后可恢复。

## 4. 边界与异常场景
- 离线/弱网：下单失败→错误态+重试；支付中网络恢复→订单处理中→对账兜底。
- 多设备：套餐以服务端为准（§788），前端仅展示；支付成功后多端通过事件刷新。
- 红线：绝不前端计算金额、绝不存储/展示支付密钥；A21 回调不经本机 Agent。

## 5. 无障碍 + 动效要求
- 套餐卡片对比用表格语义或 `role="list"`，状态色标必带文字（不止色）；焦点可见（`:focus-visible` 描边）。
- 下单面板/支付弹窗尊重 `prefers-reduced-motion`；倒计时与 toast 不依赖纯色彩传达（文字+图标）。
- 操作按钮 ≥40px 高（移动端），见 `UI-SELFCHECK.md §3` R4/R6。

## 上游引用
- PRD：§12 定价与套餐、§769-783 角色权限矩阵、§789/§802 会员降级、§1167-1171 支付全局异常、§22.2/§1505 订单状态机与对账。
- 契约：A20(`payments-order.*.schema.json`)、A21(`payments-callback.request.schema.json` + `external-api.registry.json`)、`domain-events`(paymentStatusChanged/memberPlanChanged)、`error-codes`(PLAN_REQUIRED)。
- 设计系统：`00-design-system.html`（色彩/间距/组件 token）。

## 下游交付
- 架构师(`U7-arch.md`)须读 §2 交互清单 + §3 验收，产出组件树与"订单状态机 + 套餐枚举 + UI↔A20/A21 字段映射表"。
- 工程师(`U7-payment.html` + `interaction-U7.md`)须读本文件 §2/§3/§5 与架构师字段映射，实现可交互 mock 原型。
