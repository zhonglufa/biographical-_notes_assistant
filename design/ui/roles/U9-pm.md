<!--
TRACE-BLOCK
role: PM
package: U9 每日日报 UI (A24 今日日报摘要 / A25 推送时间偏好)
upstream_read:
  - prd/PRD-简历自动投递与面试模拟-最终版.md 模块9 每日日报与推送（§806-830）
  - prd §6.4 渠道矩阵/频率聚合/免打扰（日报独立 20:00 推送，不参与聚合）
  - design/contracts/external-api.registry.json A24/A25 字段
  - design/contracts/daily-report-today.response.schema.json（date/summary/stats: appliedTotal/success/failed/byPlatform/hrViews/interviewInvites/newQuestions/trend7d）
  - design/contracts/daily-report-preference.request.schema.json（pushTime HH:mm / enabled）
  - design/ui/00-design-system.html / 01-app-shell.html / ROLE-WORKBOOK.md §2
downstream_write: [design/ui/roles/U9-arch.md, design/ui/screens/U9-daily.html, design/ui/interaction-U9.md, design/ui/roles/U9-qa.md]
status: DONE（Team Lead 代笔；子 agent 调度不稳定，依 UI-SELFCHECK §4 标注）
decisions:
  - U9 含两屏：① 今日日报摘要（只读展示 A24）② 推送偏好设置（A25 pushTime/enabled）
  - 当日无活动 → 展示「今日无投递活动」空摘要（PRD 边界，不发送空日报）
  - 趋势用近 7 天迷你柱状图（trend7d）
-->
# U9 每日日报 · 产品经理交互需求（A24/A25）

## 1. 目标与范围
**目标**：让用户每天清晰看到当日投递成效与近 7 天趋势，并自助配置日报推送时间/开关。
**范围**：今日日报摘要展示（A24）、日报推送偏好设置（A25：pushTime 默认 20:00、enabled 开关）。
**不做什么**：日报生成/聚合逻辑（服务端 Cron，PRD 模块9）；多通道兜底（通知中心 U8）；异常重试（服务端 15min 重试，前端不感知）。

## 2. 交互需求清单
- **R1 摘要加载**：进入「每日日报」→ A24 `GET /daily-report/today` → 渲染日期/摘要文案/统计卡（投递总数、成功/失败、HR 查看、面试邀请、新增面试题）/ 平台分布 / 近 7 天趋势。
- **R2 空态**：当日无活动（stats 全 0）→ 展示「今日无投递活动」友好摘要，不显示空图表（PRD 边界）。
- **R3 趋势图**：trend7d 渲染迷你柱状图（近 7 天投递量），hover/聚焦显示当日数值（无障碍：表格化数据并附 `aria-label`）。
- **R4 偏好设置（A25）**：「推送设置」入口 → 时间选择器（HH:mm，默认 20:00）+ 开关（enabled）→ 保存 PUT A25 → Toast「已保存」；非法时间（如 25:00）前端拦截。
- **R5 加载/错误**：骨架屏 + 错误态重试（A24 失败）；保存中按钮 loading 态。

## 3. 验收标准
- **AC1**：A24 stats 字段齐全时统计卡正确渲染；趋势 7 根柱对应 trend7d。
- **AC2**：当日无活动 → 空摘要态，无空图表。
- **AC3**：A25 保存 pushTime=20:00、enabled=true → 请求体匹配契约；保存成功后偏好持久（mock 本地）。
- **AC4**：时间非法 / 网络错误 → 拦截或错误态，不静默丢失。
- **AC5**（响应式）：375/768/1280 三档无横溢、统计卡网格自适应、按钮≥40px（R1–R7）。

## 4. 边界与异常
- A24 服务端生成失败 → 前端错误态 + 重试；不展示陈旧数据。
- A25 enabled=false → 明确提示「已关闭日报推送」。
- pushTime 与免打扰时段冲突 → 提示「推送时间位于免打扰时段，将顺延」。

## 5. 无障碍 + 动效
- 统计卡用数值 + 标签双呈现；趋势图附数据表（色盲/读屏可达）。
- 保存成功 Toast 200ms；卡片入场 200ms（尊重 reduced-motion）。

## 上游引用
PRD 模块9（日报内容 7 项、空日报边界、异常重试）；§6.4（日报独立推送、免打扰）；契约 A24/A25 字段。

## 下游交付
架构师（`U9-arch.md`）须读 §2 R1–R5 + §3 AC1–AC5 定组件树、StatCard/TrendMini 状态、A24/A25 字段映射表。
