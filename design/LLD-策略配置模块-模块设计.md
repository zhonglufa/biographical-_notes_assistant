# LLD 详细设计：策略配置模块（服务端 Java）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合审查报告 P1「策略配置」真缺失项）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD v3.24（§3.5 策略配置模块 / §4 / §3.1 A03 字段级权限）× PRD v4.5 §23.5 配置中心 / §18 NFR / §6 功能
> 定位：LLD 序列之**策略配置模块**（服务端 Java）；存取生效策略快照，供投递调度消费，不执行调度、不接触浏览器
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

- **职责**（HLD §3.5）：投递策略配置的存取与生效。
- **边界**：不执行调度（§3.4 消费）、不接触浏览器。
- **依赖**：MySQL（策略表）、用户权限模块（字段级权限 A03）。

## 1. 配置模型

- `strategy_config`（数据库设计 LLD）：`daily_limit`（免费 30 / 专业·高级 100）、`match_threshold`（默认 0.60）、`time_windows`、`enabled_platforms`、`blacklist`、免打扰、聚合粒度。
- `UserConfig`（PRD §20.3）：投递策略 / 匹配阈值 / 推送时间 / 免打扰 / 聚合粒度；多端同步，存服务端、本机 Agent 拉取。

## 2. 读写与冲突

- 端点：`GET /strategies`（A12）、`PUT /strategies`（A13）、`GET /strategies/effective`。
- 权限：PC 完整 / 移动端受限；冲突以 **PC 为准 LWW**（§23.10 / HLD §1206），字段级读写权限由 A03 强制。
- 版本向量防乱序：带时间戳后写覆盖并推送"配置已更新"，不静默（HLD §1206）。

## 3. 生效快照与事件

- 生效策略快照供投递调度（§3.4）消费；配置变更发 `strategy.updated` 事件，状态机模块重读（§3.5.1）。
- 写时主动失效缓存（用户策略 / 权益快照 TTL 5min，HLD §1427）。

## 4. 暂停开关与降级

- 平台 `enable` 热更（适配器 healthCheck 连续 3 次失败自动 disabled，§6.2）；限额动态计算（§9.1）。
- Feature Flag 经配置中心，作用域 global/platform/user_tag/device，单 flag 即时反转（kill switch，§1463）。

## 5. 数据对齐

- `strategy_config` 表：`uk(user_id)`，`daily_limit` 默认 30，`match_threshold` 默认 0.60（数据库设计 LLD §3.x）。
- 与 §3.4 调度消费链路、§3.1 字段级权限全对齐。

## 6. 待决项登记（非静默）

| 项 | 说明 |
|----|------|
| T-SC-1 配置版本化与迁移 | schema_version + 双写迁移策略（§1192）编码期确认 |
| T-SC-2 灰度/FF 对策略影响 | 部分平台灰度时策略生效范围 |

## 7. 机器可读契约索引

- A12 `GET /strategies`、A13 `PUT /strategies`（均由 outlined 升 detailed，见 `strategies.request/response.schema.json`）；A03 字段级权限见 §3.1/§4.1。
