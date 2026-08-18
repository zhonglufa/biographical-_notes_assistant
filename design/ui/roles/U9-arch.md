<!--
TRACE-BLOCK
role: 架构师(Architect)
package: U9 每日日报 UI (A24/A25)
upstream_read: [design/ui/roles/U9-pm.md, design/ui/00-design-system.html, design/contracts/daily-report-today.response.schema.json, design/contracts/daily-report-preference.request.schema.json]
downstream_write: [design/ui/screens/U9-daily.html, design/ui/interaction-U9.md, design/ui/roles/U9-qa.md]
status: DONE（Team Lead 代笔）
decisions:
  - 组件树：DailyReportPage → SummaryHeader + StatGrid(StatCard×5) + PlatformDist + TrendMini; PreferencePanel(TimePicker+Toggle)
  - 复用：Card、StatCard、Toggle、Button、Skeleton、EmptyState、ErrorState、Toast、TimeInput
  - 新增：TrendMini（7 日迷你柱，附数据表）
-->
# U9 每日日报 · 架构师组件设计（A24/A25）

## 1. 组件树
```
DailyReportPage
├─ SummaryHeader（date + summary 文案）
├─ StatGrid
│  ├─ StatCard 今日投递总数 (appliedTotal)
│  ├─ StatCard 成功/失败 (success / failed)
│  ├─ StatCard HR 查看 (hrViews)
│  ├─ StatCard 面试邀请 (interviewInvites)
│  └─ StatCard 新增面试题 (newQuestions)
├─ PlatformDist（byPlatform 横向占比条）
├─ TrendMini（trend7d 7 柱 + 数据表）
└─ PreferencePanel（A25）
   ├─ TimePicker（pushTime HH:mm）
   └─ Toggle（enabled）
```

## 2. 状态模型 ↔ 契约字段
| UI | 契约字段 | 说明 |
|---|---|---|
| 日期 | `date` | YYYY-MM-DD |
| 摘要文案 | `summary` | 人类可读 |
| 总数/成功/失败 | `stats.appliedTotal/success/failed` | 整数 |
| HR 查看/邀请/新增题 | `stats.hrViews/interviewInvites/newQuestions` | 整数 |
| 平台分布 | `stats.byPlatform[]` | platformId/count |
| 7 日趋势 | `stats.trend7d[]` | date/count |
| 推送时间 | A25 `pushTime` | HH:mm |
| 推送开关 | A25 `enabled` | boolean |

## 3. 复用决策
- **复用**：Card、StatCard、Toggle、Button、Skeleton、EmptyState、ErrorState、Toast（设计系统）。
- **新增**：`TrendMini`（7 日柱 + 隐藏数据表，保障读屏）。

## 4. A24/A25 字段映射表
| UI 元素 | 契约 | 类型 |
|---|---|---|
| 统计卡数值 | `stats.*` | integer |
| 平台占比条 | `stats.byPlatform[].count` | integer |
| 趋势柱高 | `stats.trend7d[].count` | integer |
| 时间输入 | A25 `pushTime` | string HH:mm |
| 开关 | A25 `enabled` | boolean |

## 5. 关键状态流转
- 加载：A24 → loading(骨架) / data / empty(无活动) / error(重试)。
- 保存偏好：A25 PUT → loading → Toast「已保存」；非法时间前端拦截不请求。

## 上游引用
`U9-pm.md` §2 R1–R5、§3 AC1–AC5、§5 无障碍/动效。

## 下游交付
工程师（`screens/U9-daily.html` + `interaction-U9.md`）依组件树与映射表实现；QA（`U9-qa.md`）依 AC1–AC5 + R1–R7 核查。
