# LLD 详细设计：投递状态机模块 + 策略执行（服务端 Java 中枢）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合审查报告 P1「投递状态机」真缺失项）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD v3.24（§3.4 投递状态机模块 + 策略执行 / §4.2 A09 / §4.3 A11 / §6.13.2 幂等键 / ADR-008）× PRD v4.5 §20.2 Application 状态机 / §6.3 异常处理 / §6.2 平台上限
> 定位：LLD 序列之**投递状态机模块**（服务端 Java 中枢）；经 C2/C3/C4 与本机 Agent 协作，不执行浏览器操作
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

- **职责**（HLD §3.4）：管理 10 状态投递流转、生成投递任务并保证幂等。
- **边界**：不执行浏览器操作（下沉本机 Agent）；不决定平台选择细节（策略模块 §3.5）。
- **依赖**：MySQL（投递表 / 事件日志）、Redis（幂等令牌 / 分布式锁）、RabbitMQ、Python 适配器。

## 1. 10 状态机与转移矩阵（ADR-008）

| 当前态 | 允许转移到 | 触发 |
|------|------|------|
| `pending_confirm` | `autofilling` | 用户确认入队 |
| `autofilling` | `submitted`(成功) / `closed`(失败放弃/平台不可用) / `pending_confirm`(补验证码重投) | 浏览器执行结果回写 |
| `submitted` | `viewed` / `rejected` / `closed` | HR 轮询感知 / 平台拒绝 / 超时关单 |
| `viewed` | `contacting` / `rejected` / `closed` | HR 沟通 / 超时未沟通关闭 |
| `contacting` | `interview_invited` / `rejected` / `closed` | 面试邀请 / 沟通失败 / 超时关闭 |
| `interview_invited` | `interview_done` / `rejected` / `closed` | 完成面试 / 未通过 / 超时关闭 |
| `interview_done` | `offer` / `rejected` / `closed` | offer / 未通过 / 超时关闭 |
| `offer` | `closed` | 流程结束归档终态 |
| `rejected` | （无） | 终态 |
| `closed` | （无） | 终态 |

- **规则**：无回退边；HR 看率在 `submitted` 后任一中间态可能直接 `rejected`/`closed`；`offer` 后必须 `closed`（不保留"进行中"）；所有转移写 `application_event` 审计（ADR-008）。
- **HR 感知态**：由服务端经 C4 轮询最终裁决（超时 / 异常置 `unknown`，不入状态机）。

## 2. 幂等四元组与去重

- 幂等键 = `(user_id, platform, job_id, apply_date)`（HLD §6.13.2 / ADR-004），唯一索引防重复投递。
- Redis `SETNX` 前置检查：已执行直接返回原结果；中断恢复时按 key 查实际状态而非盲目重试（PRD 模块 3）。

## 3. 失败重试与限流

- 单平台失败不影响他平台；重试指数退避最大 3 次（PRD §6.3 / §835）。
- 限流：单次 ≤50、两次间隔 ≥30min、单平台日限 = 平台上限 70%（PRD 模块 3）；上限按角色动态计算（§9.1）。
- 排队超时：队列等待 >30min 标记"已过期"，用户收到通知可手动重试（PRD §490）。

## 4. 孤儿任务清扫（R2 闭环）

- 定时（每 5min）扫描 `autofilling`/`submitted` 且距变更 >30min 的记录；反查 `application_task` 实际结果（重投 B07 查询）；结果已知→推进状态机，未知且超 15min 宽限→标记 `closed` 并通知"投递状态未知，建议手动确认"。
- 仅 Java 侧执行（本机 Agent 不持业务库），复用 Redis 分布式锁防重入。

## 5. 事件日志与广播

- 每状态变更写 `application_event`（谁/何时/从何到何/原因），并广播 `apply.status.changed` 供通知/AI/推荐监听（ADR-008）。
- 生成投递任务经 C2 下发本机 Agent（载荷不含 Cookie），结果经 C3 回写（§3.4.1）。

## 6. 策略执行衔接

- 消费 `strategy.updated` 事件重读生效策略；投递前置 = 角色日限额 + 启用平台校验通过 + 幂等四元组未冲突（C1 前置，§3.4.1）。

## 7. 数据对齐

- `application`（10 态 ENUM，主键 + 四元组唯一约束）、`application_event`（溯源）、`application_task`（执行单元）。
- 与数据库设计 LLD 全对齐（§6.13.2 幂等键、§5.1 ER）。

## 8. 待决项登记（非静默）

| 项 | 说明 |
|----|------|
| T-DS-1 各态超时阈值 | viewed/contacting/interview_* 超时关单阈值编码期确认 |
| T-DS-2 跨阶段直达终态边界 | `rejected`/`closed` 直达边的异常组合用例 |
| T-DS-3 C4 HR 感知拉取频率 | 轮询窗口与成本权衡 |

## 9. 机器可读契约索引

- A09 `POST /apply/batch`（fully-detailed，§4.2）、A11 `GET /applications/{id}`（fully-detailed，§4.3）、A10 `GET /applications`（由 outlined 升 detailed，见 `applications-list.response.schema.json`）。
