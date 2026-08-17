<!-- TRACE
role: Engineer | software-engineer
package: U7 支付与会员 UI (A20/A21)
agent_run: 2026-08-17T22:13
author_of_record: software-engineer（本轮子 agent 调度瞬断风险，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U7-pm.md, design/ui/roles/U7-arch.md, design/ui/screens/U7-payment.html, design/ui/UI-SELFCHECK.md §3]
downstream_write: [design/ui/roles/U7-qa.md]
decisions: 交互规格对齐 PM R1-R7 与架构师状态机；含加载/空/错误、下单闸门、支付状态轮询、重复支付幂等、降级。纯前端 mock，A20/A21 为模拟调用。
status: DONE
-->

# U7 支付与会员 UI · 交互规格（A20 / A21）

> 角色：工程师（software-engineer）｜包：U7｜原型：`screens/U7-payment.html`｜契约：A20 创建订单、A21 支付回调

## 1. 页面结构（信息架构）
- 顶部：`我的会员` 标题 + 当前套餐徽标（free/pro/team，色点+文字）。
- 区块① 当前套餐：套餐名 + 权益摘要 + 「升级专业版」按钮（free 时显示；非 free 时显示「管理/续费」）。
- 区块② 套餐对比：三列卡片（免费/专业版/团队版），当前套餐列高亮，含价格、权益要点、升级按钮。
- 区块③ 我的订单：订单列表（订单号 + 描述 + 5 态色标徽标）+ 两个演示按钮（模拟过期/降级）。
- 弹窗 A 下单面板：选周期(months) → 确认（A20）。
- 弹窗 B 支付弹窗：二维码占位 + 订单号/金额/倒计时 + 模拟支付完成（A21）。

## 2. 状态与流程
### 2.1 加载 / 空 / 错误
- 进入页：`GET /users/me`(A03) 取 plan/quota → 渲染当前套餐卡片；mock 下直接渲染。
- 空态：无订单时列表显示「暂无订单」占位。
- 错误：下单(A20)失败 → 错误态 +「重试」；PLAN_REQUIRED(403) → 提示「请先登录/该操作需专业版」。

### 2.2 下单闸门（A20）
1. 点套餐「升级」→ 打开下单面板。
2. 选周期（1/3/6/12 个月，分段控件高亮当前）。
3. 点「确认下单」→ 调 `POST /payments/orders{plan,months,coupon?}`。
4. **金额不传客户端**：界面不展示金额输入；下单成功后金额直接来自 A20 响应 `amount`(分)→ 展示换算为元。**前端绝不计算价格**（红线，PRD §A20 描述）。
5. 成功 → 关闭下单面板，打开支付弹窗，写入订单号/金额/24h 倒计时。

### 2.3 支付与回调（A21）
- 支付弹窗展示 `payUrl` 二维码占位（**不真实跳转/不渲染真实支付商**）。
- 点「模拟支付完成」→ 模拟 A21 回调：
  - `paymentStatusChanged{orderNo,toState:paid}` → 订单徽标 待支付→已开通（mock 合并 paid→active 展示）。
  - `memberPlanChanged{plan,effectiveAt}` → 当前套餐卡片 + 顶部徽标刷新为目标 plan。
  - Toast「已升级为 X，权益已生效」。

### 2.4 重复支付幂等（PRD §1169）
- 同一 orderNo 已 `active` 后，再次点「模拟支付完成」→ 按钮置灰 + 提示「该订单已开通，无需重复支付」，不重复发事件、权益不变。

### 2.5 订单状态机（PRD §22.2/§1505）
`待支付(蓝) → 已支付(黄) → 已开通(绿) → 已过期(灰) | 已退款(红)`
- 倒计时归零（24h）→ 标记 `已过期`（演示按钮「模拟订单过期」可直接触发）。
- 「稍后支付」→ 关闭弹窗，订单保留为「待支付」，可再从订单区继续。

### 2.6 会员降级（PRD §789/§802）
- 演示按钮「模拟会员降级」→ 顶部出现降级横幅（配置保留不可改）+ 套餐回落免费版 + 配置项置灰（本原型以横幅+徽标演示；真实配置置灰在 V 阶段接入）。

## 3. 无障碍与动效
- 订单 5 态色标均为「色 + 文字」双编码，不依赖纯色彩（R6）。
- 倒计时、Toast 均有文字，不靠颜色单独传达。
- 按钮 `min-height:40px`（移动端可点，R4）；弹窗 `max-width:90vw`（R7）。
- 所有过渡尊重 `prefers-reduced-motion`（已加 `@media reduce`）。
- 焦点：按钮默认可见焦点环（浏览器默认 + 1px 边框）。

## 4. 响应式（UI-SELFCHECK §3）
- ≤768px：套餐对比三列 → 单列堆叠；头部/订单行可换行（R1/R2 无横溢）。
- ≤480px：按钮整行 100% 宽；分段控件换行；弹窗占满宽度（R4/R7）。
- 无横向溢出（已验证 375/768/1280 三档）。
