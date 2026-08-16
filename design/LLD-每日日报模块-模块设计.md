# LLD 详细设计：每日日报与推送模块（服务端 Java）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合审查报告 P2「每日日报」业务子域真缺失项）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD v3.27（§3.12 每日日报与推送模块 / §3.11 通知推送 / §4.1 A 层）× PRD v4.5 模块 9（每日日报：投递/面试/HR 汇总 + 自定义推送时间 + 空日报边界）/ §11 验收
> 定位：LLD 序列之**每日日报与推送模块**（服务端 Java）；纯聚合+格式化+触发推送，不生成业务数据、不做 AI
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

- **职责**（HLD §3.12）：每日定时聚合投递/面试数据，生成日报并推送（移动端 + 邮件）。
- **边界**：不生成业务数据（纯聚合+格式化）；日报内容由各业务模块产出，本模块只汇总；不做 AI（趋势为统计非预测）；推送由 §3.11 通知模块承载。
- **依赖**：MySQL（`daily_report` / `user_preference` / `application` / `interview_*`）、通知推送模块（§3.11）、定时任务框架（Cron）。
- **职责补充（显式登记）**：HLD §3.12.1 提及 `GET /daily-report/aggregate`（内部聚合入口），与 A24 `GET /daily-report/today`（用户拉取）分离——aggregate 为内部定时动作，today 为用户查询，二者不混淆。

## 1. 定时聚合（Cron 20:00）

- **触发**：每日 20:00 定时任务 `GET /daily-report/aggregate`（内部，不入 A 层外部注册表），查询当日 MySQL 投递/面试/通知数据，聚合生成 `daily_report` 快照（total_applications / successful / failed / hr_views / interview_invitations / new_questions / platform_breakdown JSON）。
- **聚合口径**（[Data-backed] PRD 模块 9）：今日投递总数、成功/失败数、各平台分布、HR 查看记录、新增面试邀请、新增面试题、近 7 天趋势（trend7d 由历史 `daily_report` 行派生，非独立存储）。
- **幂等**：以 `(user_id, report_date)` 唯一，重复触发覆盖写入（upsert），不重复计数。

## 2. 空日报边界（PRD 模块 9 边界）

- 当日无投递活动时，仍生成"今日无投递活动"摘要（stats 全 0），但**不发送空日报推送**（[Data-backed] PRD 模块 9 边界）；用户经 A24 `GET /daily-report/today` 主动拉取时仍可见该摘要。
- 仅当 `successful+failed+interview_invitations+new_questions+hr_views > 0` 才触发推送。

## 3. 推送（经 §3.11 通知模块）

- **渠道/级别**：日报默认按用户 `user_preference.daily_report_push_time` 推送（覆盖默认 20:00）；经 §3.11 以 L2 级（聚合推送，受免打扰 22:00–08:00 约束）发送；不参与投递成功类聚合（§3.11 约定）。
- **失败处理**（[Data-backed] PRD 模块 9 边界）：移动端推送失败 → 站内信兜底展示；邮件发送失败 → 自动重试 3 次（指数退避），仍失败标记待站内展示，不静默丢失。
- **自定义时间**：用户可在「我的」页设 pushTime（A25），写入 `user_preference`，下次聚合按新时间推送。

## 4. 用户偏好（A25 → user_preference）

- **A25 请求/响应**：`daily-report-preference.request/response.schema.json`；写 `user_preference(user_id PK, daily_report_push_time, daily_report_enabled)`。
- **默认**：push_time=20:00:00、enabled=1；与 `strategy_config`（投递策略）分离，避免偏好污染策略快照。

## 5. 数据表对齐（数据库设计 LLD 收口）

- 复用 `daily_report`（§1/§2 字段已对齐；trend7d 派生）。
- **本 LLD 发现并闭合的真实缺口**：A25 日报推送时间偏好在数据库设计 LLD 中无持久化表（原仅 `strategy_config` 承载投递策略，不含通知偏好）。已在 `LLD-数据库设计-模块设计.md` §3.x 新增 `user_preference` 表 + ER/索引登记（非静默）。

## 6. 事件契约

- 发布：`daily-report.generated {userId, reportDate, stats}`（聚合完成，供通知模块订阅推送；若空日报则不发布推送事件，仅落库）。
- 订阅：无。

## 7. 错误码映射（复用 A 命名空间）

- `RESOURCE_NOT_FOUND` / `NOT_FOUND`：指定日期日报不存在（返回空摘要而非错误）。
- `INVALID_PARAM`：A25 pushTime 格式非法（schema 层 `^([01]\d|2[0-3]):[0-5]\d$` 拦截）。
- `QUOTA_EXCEEDED` / `PLAN_REQUIRED`：日报推送为免费能力，不限额；若未来高级日报（趋势预测）受限，复用此码。

## 8. 待决项登记（非静默）

| 项 | 说明 |
|----|------|
| T-DR-1 user_preference 表已补 | A25 存储已落数据库设计 LLD；与 strategy_config 分离的决策已固化 |
| T-DR-2 大用户量聚合性能 | 20:00 全量用户聚合的扫描/分批策略（建议按 user_id 分片并行 + 限速，防 DB 峰值）；编码期定 |
| T-DR-3 趋势窗口可配置 | trend7d 固定 7 天，是否可配置窗口（14/30）由产品拍板，关联 §27.4 埋点 |

## 9. 契约索引

| 端点/契约 | 文件 | 状态 |
|----------|------|------|
| A24 今日日报响应 | `contracts/daily-report-today.response.schema.json` | fully-detailed |
| A25 偏好请求/响应 | `contracts/daily-report-preference.request/response.schema.json` | fully-detailed |
