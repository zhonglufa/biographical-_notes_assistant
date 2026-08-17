<!--
TRACE-BLOCK
role: 工程师(Engineer)
package: U10 用户与登录 UI (A01/A02/A03)
upstream_read: [design/ui/roles/U10-pm.md, design/ui/roles/U10-arch.md, design/ui/00-design-system.html]
downstream_write: [design/ui/screens/U10-auth.html, design/ui/roles/U10-qa.md]
status: DONE（Team Lead 代笔）
-->
# U10 用户与登录 · 交互规格（A01/A02/A03）

## 1. 页面结构
- 登录引导页（未登录）：Hero 价值引导 + 登录卡（渠道 Tab：邮箱密码/邮箱验证码/微信扫码）+ 设备绑定(deviceId) + 错误提示。
- 账户与权益页（已登录）：套餐卡(plan) + 配额进度条(quotaUsed/quotaLimit) + 邮箱 + 推送偏好/策略入口 + 本机 Agent 登录态开关 + 登出。

## 2. 关键交互
| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| 渠道切换 | 点 Tab | 切换表单 | 高亮 |
| 登录(A01) | 提交 | 校验 → 双令牌存本机(+deviceId) | Toast 成功 → 跳转账户页 |
| 微信失败回退 | 扫码失败 | 回退邮箱登录 | 错误提示 |
| 发送验证码 | 点按钮 | 60s 倒计时防刷 | 提示已发送 |
| 配额展示 | 账户页 | quotaUsed/quotaLimit 进度条 | limit=0 显「不限」 |
| 登出 | 退出 | 清令牌 + 本机 Agent Cookie | 回引导页 |

## 3. 状态机 / 守卫
- `AuthGuard`：未登录 → GuidePage；业务请求 401 → A02 刷新 → 成功重试 / 失败 → LoginCard。
- `Session`：logged-out → logging-in → logged-in → logged-out(登出)。

## 4. 无障碍与动效
- 表单 label 关联 input；错误 `aria-live="polite"`。
- 登录成功转场 200ms；尊重 reduced-motion。

## 5. 数据契约（mock 本地）
A01 `POST /auth/login` → {channel, deviceId, email/phone/code/password} → {accessToken, refreshToken, expiresIn, userId, plan}。
A02 `POST /auth/refresh` → {refreshToken} → {accessToken, expiresIn}（拦截器静默）。
A03 `GET /users/me` → {userId, email, plan, quotaUsed, quotaLimit, preferences}。
