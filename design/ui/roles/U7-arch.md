<!-- TRACE
role: Architect | software-architect
package: U7 支付与会员 UI (A20/A21)
agent_run: 2026-08-17T22:13
author_of_record: software-architect（本轮子 agent 调度瞬断风险，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U7-pm.md, design/ui/00-design-system.html, design/ui/01-app-shell.html, design/contracts/external-api.registry.json(A20/A21), design/contracts/payments-order.*.schema.json, design/contracts/payments-callback.request.schema.json, design/contracts/domain-events.event.schema.json, design/ui/ROLE-WORKBOOK.md §3]
downstream_write: [design/ui/screens/U7-payment.html, design/ui/interaction-U7.md]
decisions: 复用 U5 卡片壳(.shell/.card/.dot/.mask/.dialog/.toast)；新增 2 组件：PlanCompareCard(套餐对比列)、OrderStateBadge(订单5态色标)。订单状态机=待支付→已支付→已开通→已过期/已退款。UI↔契约映射：plan(enum free|pro|team|premium|admin, 其中前端展示 pro/team, 后端 premium 映射团队版)/orderNo/payUrl/amount(分)/expireAt(epoch ms)；A21 事件 paymentStatusChanged.orderNo+toState、memberPlanChanged.plan+effectiveAt 落到前端。
status: DONE
-->

# U7 支付与会员 UI · 架构师组件设计（A20 / A21）

> 角色：架构师（software-architect）｜包：U7 支付与会员 UI｜对应契约：A20、A21

## 1. 组件树
```
MyMembershipPage（页面）
├─ PageHeader（复用 U5 .top：标题"我的会员" + 当前套餐徽标 PlanBadge）
├─ CurrentPlanCard（当前套餐卡片）
│   ├─ PlanBadge（plan 徽标：free/pro/team）
│   ├─ QuotaSummary（配额：日上限/已用、面试次数，来自 A03 /users/me）
│   └─ DowngradeBanner（降级提示，仅过期态显示，PRD §789）
├─ PlanCompareSection（套餐对比区）
│   └─ PlanCompareCard ×3（免费/专业版/团队版；新组件①）
│       ├─ PlanBadge
│       ├─ PriceLabel（金额由 A20 响应换算展示，前端不计算）
│       └─ UpgradeButton（→ 下单面板）
├─ OrderPanel（下单面板，modal）
│   ├─ PeriodSelector（months：1/3/6/12）
│   ├─ CouponInput（coupon?，可选）
│   └─ ConfirmButton（→ POST A20）
├─ PaymentSheet（支付弹窗，modal）
│   ├─ QRPlaceholder（payUrl 占位，不渲染真实二维码）
│   ├─ OrderMeta（orderNo + amount(元) + expireAt 倒计时）
│   └─ MockPayButton（模拟 A21 回调成功）
├─ OrderListSection（我的订单）
│   └─ OrderRow ×N
│       └─ OrderStateBadge（订单5态色标；新组件②）
└─ Toast（复用 U5 .toast：权益生效/幂等提示）
```

## 2. 状态模型
- **套餐枚举**：`plan ∈ {free, pro, team}`（前端展示三档；后端事件含 `premium/admin`，前端映射：premium→团队版展示、admin 不展示给用户）。来源：`auth-login.response.schema.json`(plan enum free|pro|team) + `domain-events.memberPlanChanged`(free|pro|premium|admin)。
- **订单状态机**（对齐 PRD §22.2/§1505）：
  `pending(待支付) → paid(已支付) → active(已开通) → expired(已过期) | refunded(已退款)`
  - 进入 `pending`：A20 成功返回 orderNo+expireAt；超 expireAt（24h，§1168）→ `expired`。
  - `pending → paid`：A21 回调 paymentStatusChanged{toState:paid}。
  - `paid → active`：memberPlanChanged{plan,effectiveAt} → 前端刷新 CurrentPlanCard。
  - 退款：A21 退款事件 → `refunded`。
- **支付中兜底态**：A20 成功但 A21 未到账 → UI 展示"订单处理中"，由 15min 定时对账（§1168）最终修正，不阻塞。

## 3. 复用决策
- **复用**（设计系统/U5）：`.shell/.card/.dot/.mask/.dialog/.toast`、PlanBadge（扩展 enum）、按钮体系、动效 token（`02-motion-system.html`）。
- **新增组件①** `PlanCompareCard`：三档对比列，含权益要点列表 + 升级按钮；当前套餐列高亮。
- **新增组件②** `OrderStateBadge`：5 态色标（待支付=蓝/已支付=黄/已开通=绿/已过期=灰/已退款=红），色+文字双编码（无障碍）。
- 不新增全局样式表，沿用 U5 内联 `<style>` + CSS 变量，保证各屏独立可预览。

## 4. UI ↔ 契约字段映射表
| UI 字段 | 契约字段 | 来源 | 说明 |
|---|---|---|---|
| 当前套餐徽标 | `plan` | A03 `/users/me` 响应 / `auth-login.response` | free/pro/team |
| 配额摘要 | `quotaUsed/quotaLimit` | A03 响应 | 日上限等 |
| 升级套餐选择 | `plan`(pro\|team) | A20 请求 | 仅 pro/team 可下单 |
| 订购周期 | `months` | A20 请求 | 整数 |
| 优惠码 | `coupon?` | A20 请求 | 可选 |
| 订单号 | `orderNo` / `outTradeNo` | A20 响应 / A21 请求 | 幂等键 |
| 支付链接 | `payUrl` | A20 响应 | 仅展示占位，不真跳转 |
| 金额 | `amount`(分) | A20 响应 | 分→元仅展示，前端不计算 |
| 过期时间 | `expireAt`(epoch ms) | A20 响应 | 倒计时→expired |
| 支付状态变更 | `paymentStatusChanged{orderNo,toState,amount}` | A21→domain-events | 驱动订单状态机 |
| 权益变更 | `memberPlanChanged{userId,plan,effectiveAt,changeType}` | A21→domain-events | 驱动 CurrentPlanCard 刷新 |
| 升级受限 | `PLAN_REQUIRED`(403) | error-codes | 非 pro 操作拦截 |

## 5. 关键交互状态流转
- **下单闸门**：UpgradeButton → OrderPanel(选 months) → ConfirmButton → 调 A20（mock）→ 成功 → PaymentSheet（QR+倒计时+MockPay）→ MockPay → 模拟 A21{paymentStatusChanged.paid → memberPlanChanged.pro} → OrderStateBadge=active + CurrentPlanCard 刷新 + Toast。
- **幂等**：MockPay 二次点击 → 检测 orderNo 已 active → 提示"该订单已开通，无需重复支付"，不重复发事件。
- **降级**：将 mock plan 设为过期 → DowngradeBanner 出现 + 配置项 `disabled` 置灰。
