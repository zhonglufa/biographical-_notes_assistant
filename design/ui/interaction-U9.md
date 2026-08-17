<!--
TRACE-BLOCK
role: 工程师(Engineer)
package: U9 每日日报 UI (A24/A25)
upstream_read: [design/ui/roles/U9-pm.md, design/ui/roles/U9-arch.md, design/ui/00-design-system.html]
downstream_write: [design/ui/screens/U9-daily.html, design/ui/roles/U9-qa.md]
status: DONE（Team Lead 代笔）
-->
# U9 每日日报 · 交互规格（A24/A25）

## 1. 页面结构
- 摘要区：date + summary 文案 + 6 张统计卡（总数/成功/失败/HR 查看/面试邀请/新增题）。
- 平台分布：byPlatform 横向占比条。
- 趋势区：trend7d 7 根迷你柱 + 同步数据表（读屏可达）。
- 推送设置（A25）：pushTime 时间选择器 + enabled 开关 + 保存。

## 2. 关键交互
| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| 加载 | 进入 | A24 拉取 | 骨架/数据/空态/错误 |
| 空态 | 当日无活动 | stats 全 0 | 友好空摘要，无空图表 |
| 偏好保存 | 点保存 | 校验 pushTime → PUT A25 | Toast「已保存」 |
| 开关 | 点 Toggle | enabled 切换 | 副文案同步 |
| 非法时间 | 保存时 | 前端拦截 | Toast「时间格式不正确」 |

## 3. 状态机
`DailyReport`: loading → data / empty / error。
`Preference`: enabled(bool) + pushTime(string)。

## 4. 无障碍与动效
- 趋势图附数据表（th/td），色盲/读屏可达；统计卡数值+标签双呈现。
- 柱高过渡 200ms；Toast 200ms；尊重 reduced-motion。

## 5. 数据契约（mock 本地）
A24 `GET /daily-report/today` → date/summary/stats{appliedTotal,success,failed,byPlatform,hrViews,interviewInvites,newQuestions,trend7d}。
A25 `PUT /users/daily-report/preference` → {pushTime, enabled}。
