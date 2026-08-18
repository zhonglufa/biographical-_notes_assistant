<!--
TRACE-BLOCK
role: PM
package: U10 用户与登录 UI (A01 登录 / A02 刷新令牌 / A03 当前用户与权益)
upstream_read:
  - prd/PRD-简历自动投递与面试模拟-最终版.md §754-798（注册登录/第三方/多设备/未登录引导/微信失败回退）
  - prd §797（未登录仅展示引导页，不暴露业务数据）
  - prd §12 套餐（free/pro/team，日限额权益）
  - design/contracts/external-api.registry.json A01/A02/A03 字段
  - design/contracts/auth-login.request.schema.json（channel: email|sms|wechat；deviceId；email/phone/code/password）
  - design/contracts/auth-login.response.schema.json（accessToken/refreshToken/expiresIn/userId/plan）
  - design/contracts/user-me.response.schema.json（userId/email/plan/quotaUsed/quotaLimit/preferences）
  - design/ui/ROLE-WORKBOOK.md §2
downstream_write: [design/ui/roles/U10-arch.md, design/ui/screens/U10-auth.html, design/ui/interaction-U10.md, design/ui/roles/U10-qa.md]
status: DONE（Team Lead 代笔；子 agent 调度不稳定，依 UI-SELFCHECK §4 标注）
decisions:
  - U10 含两屏：① 登录引导页（A01，多渠道）② 「我的」账户与权益（A03：plan/quota）
  - A02 刷新为静默后台（无独立 UI，仅在 401 时自动刷新并重试）
  - 未登录态：全站仅展示引导页，不暴露任何业务数据（PRD §797 红线）
  - 微信登录失败 → 回退邮箱/验证码（PRD §798）
-->
# U10 用户与登录 · 产品经理交互需求（A01/A02/A03）

## 1. 目标与范围
**目标**：提供安全的登录引导与账户/权益视图，且严格遵循「未登录不暴露业务数据」。
**范围**：登录（A01 邮箱/验证码/微信三渠道 + deviceId 绑定）、账户与权益（A03 plan/quotaUsed/quotaLimit）、刷新机制说明（A02）。
**不做什么**：真实 OAuth 接入、密码强度策略后端、多设备踢人管理（属后端/安全，前端仅展状态）。

## 2. 交互需求清单
- **R1 登录引导页（A01）**：未登录进入 → 展示产品价值引导 + 登录卡（渠道 Tab：邮箱密码 / 邮箱验证码 / 微信扫码）→ 提交 → A01 返回双令牌（accessToken 短期 + refreshToken 长期）→ 本地安全存（仅本机 Agent，不上传）→ 跳转主页。
- **R2 设备绑定**：提交携带 `deviceId`（本机 Agent 绑定 + 多端互斥，PRD §754），前端生成/读取设备标识。
- **R3 渠道回退**：微信登录失败 → 提示并回退到邮箱/验证码流程（PRD §798），不阻塞。
- **R4 未登录遮蔽**：全站未登录时路由守卫 → 仅渲染引导页；任何业务数据请求 401 → 触发 A02 刷新 → 失败则回登录页（不缓存业务数据）。
- **R5 账户与权益（A03）**：「我的」页展示 plan（free/pro/team）+ 套餐日限额 `quotaUsed/quotaLimit` 进度条 + 邮箱 + 推送偏好入口（接 U9/U4）。
- **R6 登出**：清除本地令牌（本机 Agent Cookie 一并清除，PRD §1012）→ 回引导页。

## 3. 验收标准
- **AC1**：A01 三渠道提交体匹配契约（channel + 对应凭证 + deviceId）；返回双令牌正确存储。
- **AC2**：未登录进入任一业务路由 → 重定向引导页，无业务数据泄漏。
- **AC3**：A03 返回 plan/quota 正确渲染进度条；quotaLimit=0 不除零（free 无上限显示「不限」）。
- **AC4**：401 → A02 刷新成功后续请求；刷新失败 → 登录页。
- **AC5**（响应式）：375/768/1280 无横溢、登录卡单列、按钮≥40px（R1–R7）。

## 4. 边界与异常
- 验证码渠道：发送验证码 → 倒计时 60s 防刷；错误码统一提示。
- 微信渠道：扫码超时 → 回退提示。
- 令牌过期：A02 自动轮转（前端静默），用户无感。

## 5. 无障碍 + 动效
- 渠道 Tab 用文字+图标；表单 label 关联 input；错误提示 `aria-live`。
- 登录成功转场 200ms；尊重 reduced-motion。

## 上游引用
PRD §754–798 登录/第三方/多设备/未登录引导/回退；§797 未登录不暴露数据（红线）；§12 套餐权益；契约 A01/A02/A03 字段。

## 下游交付
架构师（`U10-arch.md`）须读 §2 R1–R6 + §3 AC1–AC5 定登录卡/账户页组件树、AuthGuard 路由守卫、A01/A03 字段映射。
