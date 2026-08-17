<!--
TRACE-BLOCK
role: 架构师(Architect)
package: U10 用户与登录 UI (A01/A02/A03)
upstream_read: [design/ui/roles/U10-pm.md, design/ui/00-design-system.html, design/contracts/auth-login.{request,response}.schema.json, design/contracts/user-me.response.schema.json]
downstream_write: [design/ui/screens/U10-auth.html, design/ui/interaction-U10.md, design/ui/roles/U10-qa.md]
status: DONE（Team Lead 代笔）
decisions:
  - 组件树：LoginGate(AuthGuard) → GuidePage + LoginCard(channel tabs); AccountPage → PlanCard(quota progress) + EmailRow + PrefEntry
  - 复用：Card、Button、Input、Tabs、Toggle、Toast、ProgressRing/Bar、Skeleton、ErrorState
  - 新增：AuthGuard（路由守卫，未登录遮业务）、LoginCard（三渠道）
  - A02 刷新：http 拦截器静默处理，无 UI 组件
-->
# U10 用户与登录 · 架构师组件设计（A01/A02/A03）

## 1. 组件树
```
App
├─ AuthGuard（未登录 → GuidePage；401 → A02 刷新 → 失败 LoginCard）
│  ├─ GuidePage（产品价值引导 + 登录入口）
│  └─ LoginCard
│     ├─ ChannelTabs（邮箱密码 / 邮箱验证码 / 微信扫码）
│     ├─ EmailPasswordForm
│     ├─ EmailCodeForm（发送验证码 + 60s 倒计时）
│     └─ WechatQRForm（失败回退提示）
└─ AccountPage（A03，已登录）
   ├─ PlanCard（plan: free/pro/team + quotaUsed/quotaLimit 进度条）
   ├─ EmailRow
   ├─ PrefEntry（推送偏好 → U9；策略 → U4）
   └─ LogoutButton（清令牌 + 本机 Agent Cookie）
```

## 2. 状态模型 ↔ 契约字段
| UI | 契约 | 说明 |
|---|---|---|
| 渠道 | A01 `channel` | email｜sms｜wechat |
| 双令牌 | A01 `accessToken/refreshToken/expiresIn/userId/plan` | 本地安全存（仅本机） |
| 刷新 | A02 `refreshToken → accessToken/expiresIn` | 拦截器静默 |
| 套餐 | A03 `plan` | free/pro/team |
| 配额 | A03 `quotaUsed/quotaLimit` | 进度条；limit=0→「不限」 |
| 邮箱 | A03 `email` | nullable |

## 3. 复用决策
- **复用**：Card、Button、Input、Tabs、Toggle、Toast、ProgressBar、Skeleton、ErrorState。
- **新增**：`AuthGuard`（路由守卫）、`LoginCard`（三渠道切换 + 设备绑定）。

## 4. A01/A03 字段映射表
| UI 元素 | 契约 | 类型 |
|---|---|---|
| 渠道切换 | `channel` | enum |
| 登录提交体 | email/phone/code/password + deviceId | 按渠道 |
| 令牌存储 | accessToken/refreshToken | 仅本机 |
| 套餐徽标 | `plan` | free/pro/team |
| 配额进度 | quotaUsed/quotaLimit | integer |

## 5. 关键状态流转
- 登录：渠道表单 → A01 → 存双令牌(+deviceId) → AuthGuard 放行 → 主页。
- 守卫：业务请求 401 → A02 刷新 → 成功重试 / 失败 → LoginCard。
- 登出：清令牌 + 触发本机 Agent 清 Cookie（PRD §1012）→ GuidePage。

## 上游引用
`U10-pm.md` §2 R1–R6、§3 AC1–AC5、§5 无障碍/动效。

## 下游交付
工程师（`screens/U10-auth.html` + `interaction-U10.md`）依组件树与映射实现；QA（`U10-qa.md`）依 AC1–AC5 + R1–R7 核查。
