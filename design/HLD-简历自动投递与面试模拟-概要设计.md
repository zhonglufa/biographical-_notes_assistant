# 概要设计文档（HLD）：AI 简历助手 — 自动投递与面试模拟

> 2026-08-15 · v3.3（设计深度补强：B1–B7 决策落成 + 修 D 类文档卫生；继承 v3.2 图文字对齐 PRD v4.5）
> 上游文档：[PRD v4.5 最终版](../prd/PRD-简历自动投递与面试模拟-最终版.md)
> 关联 ADR：001/002/003/004/006/008/009/010/011/012/014/015/016/017/018/021/022/023
>
> **⚠ 重大架构修订（v1.1 → v2.0）**：本版将执行模型从「服务端集中式浏览器自动化」重构为「用户本机 Agent 执行」，对齐 PRD §15.1（核心决策：本机 Agent 执行）与 §C.1（本机执行）/ §C.5（Cookie 本地化不上云）。原 HLD v1.1 中「服务端执行投递 + 服务端加密存储 Cookie」两处表述（记为 **C1 / C2 矛盾**）于本版消解。
> **⚠ 重导出修订（v2.0 → v3.0）**：v2.0 仅消解 C1/C2，正文仍为 PRD v3.0 时代框架，导致 PRD v4.x 新增的「生产事故防线」（§17–§35）在 HLD 整体缺席（§1.2 追溯矩阵也停在 v3.0 章节集）。本版**基于 PRD v4.5 全文重导出**：扩展 §6（新增 §6.5–§6.10）将 PRD §17–§35 的事故预防/可靠性/本机 Agent 安全/发布治理机制落成 HLD 设计决策，并刷新 §1.2 追溯矩阵至全覆盖。对齐经 `check_prd_hld_traceability.py` 门禁校验（见 `PRD-HLD-对齐规范.md`）。
> - **C1（执行模型）**：浏览器自动化（Playwright 投递/采集/面试模拟浏览器动作）不再部署在服务端 Python 引擎，下沉到用户本机 Agent（桌面守护进程）。
> - **C2（Cookie）**：用户平台 Cookie 不再以密文存储于服务端数据库，改为仅本机 Agent 本地加密（信封加密）、不上传、不备份云端。
> - **图待重绘**：`fig-c1-system-context.svg`（HR→系统 箭头 + 平台列不全）、`fig-c2-container.svg`、`fig-2-3-deployment.svg`、`fig-2-2-apply-flow.svg`（前四张仍描绘服务端浏览器沙箱）、`fig-2-4-hr-status.svg`（服务端适配器直连，需改为本机 Agent 经 B08 执行）、`fig-2-5-ai-match.svg`（缺 LLM 主备 failover 一级，需补 §34.2）需按本版正文重绘（已在相关章节标注 `⚠ 图待重绘`）。

---

## 1. 设计概览

### 1.1 目的与范围

本文档描述"AI 简历助手 — 自动投递与面试模拟"系统的**概要设计（HLD）**，回答"如何架构与契约"：系统模块如何拆分、模块间如何交互、对外与对内的接口契约、数据模型概要、运行时与部署形态、非功能设计以及错误处理策略。

**本设计覆盖**：PC 端 + 移动端的全部 9 个功能模块（简历工作台、岗位浏览与投递、投递策略引擎、平台适配器、面试备战、AI 面试模拟、投递联动、用户与多端同步、每日日报与推送），以及会员支付、通知推送等支撑能力。

**本设计不覆盖**（属于 LLD / 后续文档）：
- 各模块类级别的实现细节（类图、方法签名）→ LLD
- 逐表 DDL 与索引定义 → 数据库设计文档
- 前端组件规范与页面级交互 → 前端设计文档
- 测试计划、部署运维手册 → P2 交付项

### 1.2 需求追溯矩阵

| 设计目标 | 来源（PRD） | 落地位置（本文档） |
|---------|-------------|-------------------|
| 每日批量投递 80-100 份（含移动端确认） | §3 指标 / 模块 2、3 | §2 架构 / §3.3 投递链路 / §4.5 批量投递接口 |
| 自动投递成功率 ≥ 90%，幂等不重复 | §11 验收 / 模块 3 | §3.4 执行层 / §5 幂等键 / §7.4 |
| 新平台接入 ≤ 2 人天 | §11 验收 / 模块 4 | §3.6 适配器框架 / §4.5 适配器接口 |
| AI 匹配度 / 面试题 / 作答评估 | §7 AI 专项 / 模块 5、6 | §3.5 AI 服务 / §4.6 AI 契约 |
| 投递成功 5 分钟内联动生成面试题 | §11 验收 / 模块 7 | §3.7 联动流程 / §5.6 异步事件 |
| HR 状态感知为 Best-Effort，不阻塞主流程 | 模块 7 消除歧义 / distill-002 | §3.7 getApplicationStatus() 轮询 / §7.2 兜底 |
| 移动端浏览、确认、通知、轻量备战 | §5.2 场景 6-10 | §2.5 多端架构 / §4 接口分层 |
| 摄像头本地画中画，不评估不录制不上传 | 模块 6 消除歧义 / distill-002 | §3.5.3 摄像头约束 |
| 高级版"优先支持"SLA 可量化 | 模块 8 消除歧义 / distill-002 | §3.2 用户与权限 / §4.1 工单契约 |
| 角色权限矩阵（免费/专业/高级/管理员） | 模块 8 | §3.1 / §4.3 鉴权设计 |
| 并发浏览器实例 ≤ 3，OOM/崩溃可恢复 | 模块 3 全局异常 | §3.4.3 实例池 / §7.3 |
| LLM 全场景降级链 | §7.3 / 模块 3 全局异常 | §7.1 |
| 支付异常（24h 有效/对账/宽限期） | §12 全局异常 | §3.8 / §7.5 |
| 每日 20:00 自动生成投递日报并推送 | §5.3 场景十一 / 模块 9 | §3.12 日报模块 / §5.7 日报数据 |
| 日报推送失败时站内消息 + 邮件重试兜底 | 模块 9 边界与异常 | §3.12 边界 / §7.4 降级 |
| 合规应急 / 最坏情况 / 泄露通报（PIPL 57） | §17 / §24.4 / §24.8 | §6.2 安全 / §6.6 事件响应 / §6.8 密钥 |
| 非功能需求 NFR（含 deadman / SLI） | §18.4 | §6.4 可观测性 / §6.5 / §6.9（deadman、SLI/SLO） |
| 范围外与待定项登记 | §19 | §9.4 / §9.6（延后项显式登记） |
| 系统核心实体与数据模型 | §20 | §5 数据设计 / §6.8 密钥与凭证 |
| 系统基建（采集/限流/灾备） | §21.3 | §6.5 F 弱网/配置 / §6.7 本地库 corruption / §6.5 O 支付双源 |
| 系统缺口补足（环境/支付/审计/缓存/资源） | §22 | §6.2 限流 / §6.5 O 依赖韧性 / §6.9 审计 |
| 系统韧性、兼容与安全（S1–S13） | §23 | §6.5 A–K（版本兼容/安全模型/迁移/DR/配置/fail-closed/弱网/混沌/日志/缓存/冲突/A-B） |
| 事件响应与韧性运营（P1–P11） | §24 | §6.6（分级/Runbook/误投撤回/泄露/kill switch/复盘/状态页/Game day） |
| 新手激活与产品细节 | §25 | §3.1 / §4 / §6.7（兼容与签名） |
| AI 产品细节（Prompt 回归/价值观/ASR） | §26 | §3.8 / §3.9 / §6.9（Prompt 版本管理与回归） |
| 增长、可观测性与多端细节 | §27 | §5.3 离线冲突 / §6.5 J 配置冲突 / §6.5 O 依赖韧性 |
| 生产事故预防补全（护栏/门禁） | §28 | §6.5 L（LLM 双闸/熔断/诈骗/发布门禁） |
| 本机 Agent 事故预防（A–F） | §29 | §6.5 M（看门狗/凭证/自更新/留痕/睡眠/不确定就停）/ §6.7 |
| 生产事故最小化兜底（Q1–Q12） | §30 | §6.5 A 最小版本 / N（fail-closed/UTC+8/离线锁/break-glass/硬上限/脱敏/资源感知） |
| 系统工程补充（R1–R12） | §31 | §6.5 O/P/Q / §6.6 guardrail / §6.8 / §6.9 |
| 资深 PM 工程补充（上线前因素） | §34 | §6.7（EV 签名/功耗/兼容）/ §6.9 / §6.5 |
| 发布治理与运营闭环 | §35.1 / §35.2 | §6.10（OSS 合规 / Beta 计划） |
| 数据与指标 | §10 | §6.4 可观测性 / §6.9（SLI/SLO、合成监控、埋点对齐） |
| 系统架构与执行模型决策 | §15 | §2 架构（本机 Agent 执行模型）/ §4.5 内部契约 / 全文对齐 |
| 商业化测算与单位经济 | §16 | §1.3 容量与成本基线 / §6.5 L（LLM 成本双闸）/ §6.9（成本护栏） |
| 设计深度补强（语义检索 / 埋点 schema / 多环境 / 权益矩阵 / 匹配度模型 / 内容安全 / 离线同步） | §7.5 / §10.2 / §10.3 / §12 / §22.1 / §26.4 / §27.2 / §31.2 | §6.11（B1–B7 逐项落成）/ §3.1（权益矩阵） |
| **不在本档范围（产品/商业/背景类，有意排除）** | §1 需求分类 / §2 背景 / §3 目标 / §4 竞品 / §13 引导 / §14 术语 / §32 商业论证 / §33 北极星增长 | 商业论证、增长模型、竞品调研、术语表属产品/运营职责，不纳入技术设计；§35.3–§35.6/§35.8 运营闭环同此 |

### 1.3 设计目标与约束

**目标**：

| 目标 | 度量 | 证据 |
|------|------|------|
| 投递可靠性 | 单任务成功率 ≥ 90%（排除网络与平台限流） | [Data-backed] PRD §11 |
| 写操作幂等 | 同一 idempotency_key 不产生重复投递 | [Data-backed] PRD §11 |
| 平台扩展效率 | 新平台适配器 ≤ 2 人天 | [Data-backed] PRD §11 |
| AI 交互及时性 | 匹配度 ≤5s、作答评估 ≤3s、联动 ≤5min | [Data-backed] PRD §7.4 |
| 推送时效 | 面试邀请通知 ≤ 10s 触达 | [Data-backed] PRD §11 |
| 容量基线 | 当前定位单用户自用/极早期小规模；架构可平滑演进至 500 DAU（届时再拆服务，触发线非起步承诺）；浏览器池"≤3"为单 Agent 进程约束 | [Data-backed] ADR-009 / 修订说明 |

**约束**：

| 约束 | 说明 | 证据 |
|------|------|------|
| 模块化单体 | 用户过万前不拆微服务，模块边界必须清晰 | [Expert judgment] ADR-001 |
| 双语言异构 | Java(Spring Boot) 业务 + Python(FastAPI) AI/自动化 | [Expert judgment] ADR-002 |
| 数据库 | MySQL 8.0 主从 + Redis 7；不引入 PostgreSQL/Mongo | [Expert judgment] ADR-003 |
| 异步基础 | RabbitMQ 承载异步任务/幂等/延迟队列 | [Expert judgment] ADR-004 |
| 状态机 | 10 状态投递状态机，单向不可逆 | [Expert judgment] ADR-008 |
| 反风控 | 三阶段：指纹随机化 → 代理 IP → 日上限 | [Expert judgment] ADR-018 |
| 隐私 | 系统不存储平台账号密码，仅加密 Cookie | [Data-backed] PRD §8.1 |

### 1.4 关键术语

| 术语 | 定义 |
|------|------|
| 投递任务（ApplicationTask） | 一次原子投递动作的单元，携带全局唯一 idempotency_key |
| 投递记录（Application） | 用户视角的投递业务实体，走 10 状态机 |
| 适配器（PlatformAdapter） | 实现统一接口契约的单平台插件 |
| 浏览器实例池 | Python 侧管理 ≤3 个并发放浏览器实例的资源池 |
| 尽力感知（Best-Effort） | HR 查看状态通过轮询/通知解析获取，失败不阻塞主流程 |
| PoC | 关键风险前置验证：先行单平台投递闭环试验 |

---

## 2. 系统架构

### 2.1 架构风格

采用 **前后端分离 + 模块化单体 + 双语言异构 + 本机 Agent 执行** 的组合：

- **模块化单体**：Java Spring Boot 单进程承载全部业务模块，按领域边界组织模块，进程内调用为主（ADR-001）。
- **双语言异构（服务端）**：AI/LLM 编排能力独立为 Python FastAPI 服务（仅 LLM 网关，调用外部大模型 API），与 Java 业务服务通过 REST + RabbitMQ 解耦（ADR-002）。**注意：浏览器自动化（Playwright 投递/采集）不在此 Python 服务内**，已下沉到用户本机 Agent（部署形态见 §2.6，对齐 PRD §15.1）。
- **本机 Agent（用户 PC 桌面守护进程）**：独立轻量进程，负责持有平台 Cookie（本地加密）、运行 Playwright 浏览器实例池（≤3）、落地执行投递/采集/面试模拟的浏览器动作。通过长连接/推送从服务端拉取任务，本地执行后回写状态。服务端不代执行、不持有用户登录态（PRD §C.1）。
- **瘦客户端（Web PC 端 / 移动端 App）**：仅做配置、确认、查看，非执行体（PRD §25.1 / §31.1）。
- **异步优先**：一切耗时/外部依赖操作（投递执行、AI 生成、通知推送）异步化，客户端通过任务状态接口查询进度，避免阻塞用户操作。

理由：独立开发者单人可部署维护，先跑起来再演进；AI 生态与业务生态分离，各自独立迭代互不阻塞 [Expert judgment]。浏览器算力下沉到用户机器，服务端无大规模浏览器集群瓶颈，且 Cookie 永不出本机、各用户从各自 IP 发起投递，规避集中式合规与反封禁风险（PRD §15.1）。

**图交付标准**（本项目图表统一规范，适用于全部交付文档）：

- **方法论**：采用 C4 模型分层制图（Context → Container → Component → Code），一图一层次，禁止多层混合。时序图遵循 UML 2.5 规范（激活条、同步/异步箭头区分）。
- **绘图方式**：全部手绘 SVG，白底 `#ffffff` 风格，不依赖 Mermaid 等自动布局工具。
- **质量标准**：连线不穿卡、标注带底板、虚线加粗对比、命名一目了然；每张图必须带编号标题 + 逐层/逐步说明文字。
- **完整图清单**：见下方 2.2~2.5 节。

### 2.2 系统架构图（C4 分层）

**C1 系统上下文图** — 展示系统边界和外部交互方

![图 C1 系统上下文图](figures/fig-c1-system-context.svg)

**图 C1 系统上下文图 · 依次说明**

1. 左侧为外部用户：**求职者（个人用户）** 执行投递简历、管理策略等操作，日投递量为 **专业版及以上 80–100 份 / 免费版 30 份**（目标值，需 v0.9 灰度验证，详见 PRD §3 / §6.2 / §12；用户画像见 PRD §5.1）。
2. 中心为系统边界：**简历自动投递与面试模拟系统**（AI 简历助手），对用户屏蔽内部技术细节。
3. 右侧为外部依赖：**招聘平台** 作为投递目标，首期支持 BOSS直聘 / 猎聘 / 智联招聘 / 前程无忧 / 拉勾（详见 PRD §6.2，后续扩展高校就业平台 / 国聘网等见 PRD §4.2）；**邮件服务（SMTP）** 发送通知；**AI 大模型服务** 提供匹配分析与面试模拟能力；**文件存储服务** 存放简历附件及缓存。
4. 同步调用（实线箭头）共 4 条：求职者→系统、系统→招聘平台（内含 **HR 状态尽力感知**，并非 HR 主动回推，见 PRD §7.3）、系统→AI 大模型、系统→文件存储；异步消息（虚线箭头）共 2 条：系统→邮件服务、AI 大模型→系统。

> ⚠ **图待重绘（一致性）**：`fig-c1-system-context.svg` 当前仍绘有「HR→系统」实线箭头且招聘平台仅标注 BOSS/猎聘/智联；按本版对齐 PRD §7.3 / §6.2，需移除 HR→系统 箭头（并入系统→招聘平台 的 HR 感知语义），并补齐首期 5 平台（前程无忧 / 拉勾）。

**C2 容器图** — 展示系统内部可部署单元及其通信方式

![图 C2 容器图](figures/fig-c2-container.svg)

**图 C2 容器图 · 依次说明**

1. **业务层（服务端）**：Java 后端服务（Spring Boot）提供 REST API 和业务逻辑编排；Python LLM 编排服务（FastAPI）仅承载 AI/LLM 网关（调用外部大模型 API），**不含浏览器自动化**。
2. **数据层**：MySQL 8.0（主从）存储主业务数据，**仅 Java 业务侧直连读写**（落实 ADR-002 双语言解耦，Python 经 REST/MQ 访问业务数据，不直连业务库）；Redis 负责缓存、分布式锁与幂等令牌（**不承载任务队列**，任务队列由 RabbitMQ 承担）；**用户平台 Cookie 不落此层**——本地加密存储于本机 Agent（见 §C.5）。
3. **本机 Agent 层（用户 PC，⚠ 图待重绘）**：独立桌面守护进程，持有本地加密 Cookie、运行 Playwright 浏览器实例池（≤3）、执行投递/采集/面试模拟的浏览器动作；经长连接/推送从服务端拉取任务，本地执行后回写状态。
4. **基础设施层**：RabbitMQ 作为异步消息总线解耦服务端与本机 Agent；服务端**不再部署浏览器沙箱**（原 Docker 容器方案已废弃，见 §2.6）。

> ⚠ **图待重绘**：`fig-c2-container.svg` 当前将「Python 自动化引擎承载浏览器自动化」与「浏览器沙箱 Docker」绘入服务端容器内，与本版 C1 矛盾，需重绘为「本机 Agent 层（用户侧）承载浏览器实例池」。

5. 配色说明：蓝色=应用容器（服务端），绿色=数据存储，黄色=本机 Agent 层（用户侧），红色=消息中间件，灰色=基础设施。



![图 2-2 批量投递闭环时序图](figures/fig-2-2-apply-flow.svg)

**图 2-2 批量投递闭环时序图 · 依次说明**

1. 用户在 PC/移动端确认投递队列（批量选择岗位）。
2. Java 状态机先自查：角色权益、当日限额、幂等键合法性，不满足直接拒绝。
3. 校验通过后把投递任务（携带全局唯一 `idempotency_key`）写入任务表并通知本机 Agent（长连接/推送；Agent 离线则入队，上线后拉取）。
4. **本机 Agent** 从任务通道拉取投递任务（而非服务端消费执行）。
5. 本机 Agent 从**本地**浏览器实例池分配一个空闲实例（≤3），加载**本地加密 Cookie**。
6. 实例在用户机器上执行表单填充与提交（带行为模拟，防检测）。
7. 实例返回执行结果：成功、失败、或验证码（验证码将触发暂停）。
8. 执行结果经 Agent 回写至调度服务（状态事件回写）。
9. 调度服务推进 10 状态机并触发联动（面试题生成）。
10. 用户侧收到状态与通知（WebSocket/邮件/短信）[Expert judgment]。

> ⚠ **图待重绘**：`fig-2-2-apply-flow.svg` 当前步骤 4–6 描绘「Python 调度中心从队列消费并分配服务端浏览器实例执行」，与本版 C1 矛盾，需重绘为「本机 Agent 拉取任务 → 本地实例池 + 本地 Cookie 执行」。

**流程二：HR 状态感知（Best-Effort 轮询）**

![图 2-4 HR 状态感知时序图](figures/fig-2-4-hr-status.svg)



**图 2-4 HR 状态感知时序图 · 依次说明**

1. Java 状态机按平台配置触发轮询（默认 6h/次，高频平台可配置 2–4h，见 §4.5 B08），经**内部契约下发轮询指令至本机 Agent**——规避"HR→系统"反模式（外部平台不主动回推，见 §7.3 / C1）。
2. **本机 Agent** 上的平台适配器以浏览器会话（**加载本地加密 Cookie**）查询招聘平台"投递记录/沟通过"页面（行为模拟防检测，感知通道 1，见 PRD §7.3）。
3. 平台页面展示状态时，适配器解析出状态：viewed（已查看）/ contacting（沟通中）/ unknown（平台未展示或无法确认）。
4. 本机 Agent 将状态码 + 证据快照（页面截图等，留存供人工复核）经状态事件回写服务端。
5. 分支A 感知到 viewed/contacting：状态机推进（viewed→contacting），触发增强型推送（WebSocket/邮件/短信）。
6. 分支B unknown/失败：保持原状态，记日志静默跳过，不阻塞任何流程（与 §7.3"尽力感知不构成硬依赖"一致）。

轮询不构成硬依赖：`getApplicationStatus()` 由本机 Agent 执行，超时/异常一律记日志并静默跳过，状态机允许 `unknown`，面试题在生成完成时直接标记"可查看" [Expert judgment]。

> ⚠ **图待重绘**：`fig-2-4-hr-status.svg` 当前若描绘"Java 直连 Python 适配器（服务端）执行查询"，与本版矛盾，需重绘为「服务端经 B08 下发轮询 → 本机 Agent 适配器加载本地 Cookie 查询平台页面 → 回写」。

**流程三：AI 匹配与降级**

![图 2-5 AI 匹配与降级时序图](figures/fig-2-5-ai-match.svg)



**图 2-5 AI 匹配与降级时序图 · 依次说明**

1. Java 岗位模块发起同步匹配请求 `POST /internal/ai/match`（≤5s 预算，见 §4.5 B01）。
2. Python AI 编排先做配额/超时检查，超预算直接走降级链路。
3. 调用**主 LLM**（境内合规大模型，如 DeepSeek）进行匹配打分。
4. **主模型不可达（超时 / 5xx 比例超阈值）→ 自动切换至备用 LLM**（1 主 + 1–2 备用，见 §34.2）；切换时 prompt 适配层做供应商差异归一（§26.1），并跑 golden set 质量回归确认评分一致性（κ 容差内）。
5. 分支A：主/备 LLM 5s 内成功 → 返回分数 + 理由。
6. 分支B：主备均不可用 / 质量回归偏差超 κ 容差 → 触发降级 1，调用规则引擎做关键词匹配。
7. 规则引擎返回分数 + 理由（基于岗位 JD 关键词与简历文本）。
8. Python 统一响应结构返回 Java：`match_score`、`reason`、`model`（deepseek | backup | rule）、`elapsed_ms`；前端与调用方不感知降级/切换路径。

> ⚠ **图待重绘**：`fig-2-5-ai-match.svg` 当前若仅描绘"主 LLM → 规则引擎"两级降级，与本版矛盾，需补充「主 LLM 不可达 → 自动切备用 LLM（golden set 回归）」这一级（§34.2）。

### 2.5 技术选型与理由

| 技术 | 用途 | 理由 | 证据 |
|------|------|------|------|
| Java 17 + Spring Boot 3.x | 业务服务 | 企业级事务/安全/运维生态成熟，长期维护成本低（Java 17 为 Spring Boot 3 的最低基线，非锁定版本） | [Expert judgment] ADR-002 |
| Python 3.x + FastAPI | AI/自动化引擎 | LLM/Playwright/爬虫生态原生，异步高并发桥接（Python 版本以部署环境为准） | [Expert judgment] ADR-002 |
| MySQL 8.0 主从 | 业务关系数据 | 强一致/事务/关系查询，云厂商支持完善 | [Expert judgment] ADR-003 |
| Redis 7 | 缓存/分布式锁/幂等令牌 | 一专多能，减少中间件数量 | [Expert judgment] ADR-003 |
| RabbitMQ | 异步任务/事件/延迟队列 | 投递任务＝天然异步队列，需死信/延迟语义 | [Expert judgment] ADR-004 |
| Vue 3 + Element Plus | PC 前端 | 生态成熟，组件库覆盖中后台 | [Expert judgment] ADR-010 |
| uni-app | 移动端 | 一套代码出 H5/小程序，覆盖碎片场景 | [Expert judgment] ADR-010 |
| OSS + MinIO | 文件存储 | 生产云存储，本地开发自托管 | [Expert judgment] ADR-011 |
| Playwright | 浏览器自动化（**运行于用户本机 Agent**，非服务端） | 竞品验证全平台无公开 API，需模拟真人操作 | [Data-backed] PRD §4.2 / §15.1 |
| Prometheus/Grafana/Loki | 可观测性 | 指标/日志一体化，轻量自托管 | [Expert judgment] ADR-015 |
| DeepSeek（V4-Flash 档） | LLM | 成本模型 ¥2500-3000/500DAU/月 | [Data-backed] ADR-009 |

**版本标注**：所有框架主版本沿用 ADR 已采纳结论；精确小版本号在 LLD 阶段以依赖锁定文件为准，此处不虚构 [Unverified — requires human review]。

### 2.6 部署架构（运行时视图）

**单机起步**（符合模块化单体约束，ADR-001）：

![图 2-3 部署架构图](figures/fig-2-3-deployment.svg)



**图 2-3 部署架构图 · 依次说明（自上而下四层）**

① **入口层**：Nginx 统一接收 Web/API 请求，负责 TLS 终止与反向代理；H5 静态资源走 OSS，业务 API 走 Nginx。
② **应用层（服务端）**：Java 服务（事务/状态机/支付）与 Python 服务（LLM 编排网关）同机双进程部署，经 Host 内部总线互调（REST `/internal/*` + 事件），遵守 ADR-002 双语言异构约束，不共享数据库。**浏览器自动化不在此层**——已下沉至用户本机 Agent（见 §2.2 ③ 与 PRD §15.1）。
③ **Host 内数据**：Redis 7 提供缓存、分布式锁、幂等令牌，Java（Lettuce）与 Python（redis-py）共享访问；只存可重建数据，不落持久化业务数据。
④ **云服务**：MySQL 主从存业务关系数据（**仅 Java 经 JDBC 直连**；Python 不直接连业务库，需访问业务数据时经 REST `/internal/*` 或订阅 MQ 事件，落实 ADR-002 存储层解耦，修正原"Java/Python 共享"表述）、RabbitMQ 承载投递/对账任务与事件队列（AMQP，含延迟与死信）、OSS 存简历导出与证据快照（S3，Python 直连）；本地开发以 MinIO 自托管替代，契约不变。
⑤ **演进路径**：用户过万后先拆 Python LLM 编排服务独立集群（AI 可横向扩展），再按热点模块（通知、支付）拆分 Java 侧；**浏览器自动化始终随用户本机 Agent 横向扩展，服务端无浏览器算力瓶颈** [Hypothesis]。

> ⚠ **图待重绘**：`fig-2-3-deployment.svg` 当前在「应用层/Host 内」绘有「Python 服务（Playwright 自动化）+ 浏览器沙箱（Docker）」，与本版 C1 矛盾，需重绘为「浏览器实例池仅存在于用户侧本机 Agent，服务端仅 Java + Python(LLM 网关)」。

**容量模型与浏览器实例池口径（修订说明，落实 §1.3 / 修正 H3）**：
- 本系统当前定位为**单用户自用 / 极早期小范围**（非多租户 SaaS）。据此，§1.3"500 DAU 容量基线"调整为**架构演进上限目标**（即"模块化单体可平滑支撑到 500 DAU，届时再拆服务"），不作为上线初始承诺。
- 浏览器实例池"≤3 并发"是**单 Agent 进程（单用户本机/单节点）** 的资源约束（与 PRD 反风控"单账号并发 ≤3 实例"一致），非系统级总量。
- 扩展方式：用户规模上升时，按"每用户/每节点 1 个浏览器 Agent 实例 + 自有账号 + 住宅/移动代理 IP"横向增节点，投递吞吐随节点数线性扩展；该路径由 §2.6 ⑤ 演进路径承载，无需改单体架构。
- 结论：3 实例/单节点 与 80-100 份/天/人的目标在"单用户自用"定位下自洽（3 实例 × 全天 ≈ 数百份/天余量充足）；"500 DAU"仅作为未来拆服务的触发线，删除其"起步基线"语义。

---

## 3. 模块设计

模块按"Java 业务侧（服务端）+ 本机 Agent 执行侧 + 共享契约"三维组织。每个模块给出职责（单句，无"和"）、输入、输出、依赖、边界。其中 AI/LLM 网关仍由服务端 Python 服务承载（§3.8/§3.9），浏览器自动化模块（§3.6/§3.7）归属本机 Agent 执行侧；依赖方向无环：业务模块 → AI 接口；Java ↔ Python(服务端 LLM 网关) 仅经 REST/MQ；本机 Agent 经任务通道与服务端交互，不直连业务库（ADR-001/002 约束）。

### 3.1 用户与权限模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 管理账号生命周期、登录态与角色权益的判定。 |
| **输入** | 注册/登录请求、第三方授权码、令牌校验请求、会员变化事件 |
| **输出** | JWT 令牌、用户画像、权益上下文（权限矩阵判定结果） |
| **依赖** | MySQL（用户表）、Redis（会话/黑名单）、支付模块（会员事件） |
| **边界** | 不负责支付订单创建；不改写平台 Cookie（仅存取密文） |

关键点：
- 登录方式：邮箱/手机验证码/微信扫码，JWT RS256 无状态令牌 [Expert judgment] ADR-017/018。
- 权限判定在服务端每次接口调用时强制执行，前端仅做展示隐藏 [Data-backed] PRD 模块 8。
- 会员降级：过期自动降级免费版，存量配置保留不可改，进行中任务允许执行完毕 [Data-backed] PRD 模块 8。
- **特权 SLA 落地**：高级版"优先支持"映射为 3 个可操作指标——工单响应 48h（免费/专业 7d）、适配器 beta 抢先、新平台接入优先队列 [Data-backed] PRD 模块 8。

**订阅权益矩阵（功能 × 套餐，驱动权限系统设计的总制品；完整决策与 LLD 依赖见 §6.11 B4）**：

| 功能 | 免费版 | 专业版 | 高级版 | 管理员（后台角色） |
|------|--------|--------|--------|-------------------|
| 接入平台数 | ≤3 | 全部 | 全部 | 全部 |
| 日投递上限 | 30 | 100 | 100 | 100 |
| 移动端 | 仅查看 | 完整 | 完整 | 完整 |
| AI 面试模拟 | — | ✓ | 无限 | ✓ |
| 语音练习（麦克风） | 文本仅查看 | ✓ | ✓ | ✓ |
| 多简历版本 | — | — | ✓（创建 + 平台绑定，见 §25.2） | ✓ |
| 优先适配器支持 | — | — | ✓（SLA 量化，见本模块关键点） | ✓ |
| 策略编辑 / 平台开关 | 只读 | ✓ | ✓ | ✓ |
| 适配器安装 / 配置入口 | 隐藏 | ✓ | ✓ | ✓ |
| 管理后台 | — | — | — | ✓ |

> 说明：「管理员」为产品运营后台角色（非付费套餐）；权限判定由 §4.1 A03 返回 `permissions`、§4.3/§4.5 字段级校验强制执行 [Data-backed] PRD §12 / 模块 8。

### 3.2 简历工作台模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 简历内容与版本资产的存取、快照 diff、ATS 评分触发。 |
| **输入** | 编辑保存请求、模板切换请求、ATS 评分请求、导入请求 |
| **输出** | 简历版本、结构化 diff、评分报告、导出的 PDF/HTML |
| **依赖** | MySQL（简历表）、OSS（导出文件）、AI 编排（优化/评分） |
| **边界** | 不做文本润色（交 Python）；不管理模板 CSS 的视觉细节（前端） |

关键点：
- 内容与样式分离存储：内容 JSON 独立，模板仅换 CSS 修饰器 [Data-backed] PRD 模块 1。
- 快照式版本管理 + 结构化 diff（ADR-012）；冲突以最后保存版本为准 [Data-backed] PRD 模块 8。
- ATS 评分：LLM + 规则综合，降级为纯规则 [Data-backed] PRD §7.3。

### 3.3 岗位浏览模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 岗位聚合展示、匹配度获取、收藏/忽略/浏览记录。 |
| **输入** | 搜索/筛选请求、匹配度请求、收藏操作 |
| **输出** | 岗位列表（含来源平台与匹配度）、匹配理由 |
| **依赖** | MySQL（岗位表）、AI 匹配服务（同步 ≤5s） |
| **边界** | 不抓取岗位（Python 采集器）；不执行投递（状态机模块） |

关键点：
- 岗位来源聚合所有已接入平台，每条标注来源 [Data-backed] PRD 模块 2。
- 匹配度标签色彩：绿 ≥80 / 蓝 60-79 / 灰 <60 [Data-backed] PRD 模块 2。
- 离线缓存：移动端缓存最近 50 条岗位，无网可看 [Data-backed] PRD 模块 8。

### 3.4 投递状态机模块 + 策略执行（Java 中枢）

| 项 | 内容 |
|----|------|
| **职责** | 管理 10 状态投递流转、生成投递任务并保证幂等。 |
| **输入** | 投递确认（批）、任务结果事件、适配器状态同步、轮询结果 |
| **输出** | 投递记录状态变更、投递任务（RabbitMQ）、联动触发事件 |
| **依赖** | MySQL（投递表/事件日志）、Redis（幂等令牌/分布式锁）、RabbitMQ、Python 适配器 |
| **边界** | 不执行浏览器操作；不决定平台选择细节（策略模块） |

关键点：
- **10 状态机与允许转移矩阵**（落实 ADR-008，修订"单向不可逆"为"无回退边、但有跨阶段直达终态边"，修正 R3）：

  | 当前态 | 允许转移到 | 触发 |
  |--------|-----------|------|
  | `pending_confirm` | `autofilling` | 用户确认入队 |
  | `autofilling` | `submitted`（成功）/ `closed`（失败且用户放弃或平台不可用）/ `pending_confirm`（需人工补验证码后重投） | 浏览器执行结果回写 |
  | `submitted` | `viewed` / `rejected` / `closed` | HR 轮询感知 / 平台明确拒绝 / 长时间无响应超时关单 |
  | `viewed` | `contacting` / `rejected` / `closed` | HR 主动沟通 / 超时未沟通关闭 |
  | `contacting` | `interview_invited` / `rejected` / `closed` | 收到面试邀请 / 沟通失败 / 超时关闭 |
  | `interview_invited` | `interview_done` / `rejected` / `closed` | 完成面试 / 未通过 / 超时关闭 |
  | `interview_done` | `offer` / `rejected` / `closed` | 收到 offer / 未通过 / 超时关闭 |
  | `offer` | `closed` | 流程结束（接受或婉拒均归档终态） |
  | `rejected` | （无） | 终态 |
  | `closed` | （无） | 终态 |

  规则：无"回退边"（如 `viewed` 不可回 `submitted`）；HR 看率在 `submitted` 后任一中间态可能直接 `rejected`/`closed`；`offer` 后必须 `closed`（不保留"进行中"语义）；所有转移写 `application_event` 审计日志 [Expert judgment] ADR-008。
- **孤儿任务清扫（修订新增，闭环 R2）**：投递链路为"Java 写 pending → 任务通道下发本机 Agent → 本机 Agent 执行 → 结果经 Agent 回写 → Java 推进"。若本机 Agent 在"已投递但结果未回写"前崩溃/离线，`application` 会卡在 `autofilling`/`submitted`。机制：
  1. 定时任务（每 5min）扫描 `application` 处于 `autofilling`/`submitted` 且距状态变更 > 设定阈值（默认 30min）的记录；
  2. 反查对应 `application_task` 实际结果（重投 B07 查询，或在途则按幂等键重查平台）；
  3. 结果已知 → 推进状态机；结果未知且超 15min 宽限 → 标记 `closed` 并通知用户"投递状态未知，建议手动确认"；
  4. 仅 Java 侧执行清扫（本机 Agent 不持业务库），复用 Redis 分布式锁防重入。该机制与 §3.7"排队超 30min 过期"互补，覆盖"在途丢失"而非仅"排队超时" [Expert judgment]。
- 每个状态变更写事件日志（谁/何时/从何到何/原因），并广播事件供通知、AI、推荐监听 [Data-backed] ADR-008。
- 幂等：投递前置检查 idempotency_key（Redis SETNX），已执行则直接返回原结果；中断恢复时用 key 查实际状态而非盲目重试 [Data-backed] PRD 模块 3。
- 失败恢复：单平台失败不影响他平台；重试指数退避最大 3 次 [Data-backed] PRD 模块 3。
- 限流与上限：单次 ≤50，两次间隔 ≥30min，单平台日限=平台上限 70% [Data-backed] PRD 模块 3。上限数值按角色动态计算（见 §9.1）。

### 3.5 策略配置模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 投递策略配置的存取与生效。 |
| **输入** | 配置读写请求（PC 完整/移动端受限） |
| **输出** | 生效策略快照（供调度消费）、配置变更事件 |
| **依赖** | MySQL（策略表）、用户权限模块 |
| **边界** | 不执行调度，不接触浏览器 |

配置项与 PRD 模块 3 一致：每日投递上限、匹配度阈值、投递时段、启用平台、自动简历选择、投递后自动面试准备、平台扩展入口。移动端仅"查看 + 开关控制"，配置以 PC 端为准（冲突处理 [Data-backed] PRD 模块 8）。

### 3.6 平台适配器系统（本机 Agent 执行侧 · 服务端编排）

| 项 | 内容 |
|----|------|
| **职责** | 管理平台适配器全生命周期与投递任务分发。**适配器代码包部署并运行于本机 Agent（执行侧）**；服务端负责适配器元数据、版本、启停编排与状态回收。 |
| **输入** | 投递任务（经任务通道下发至本机 Agent）、定时健康检查、登录态事件、适配器 CRUD（服务端元数据） |
| **输出** | 执行结果事件（经 Agent 回写服务端）、平台状态快照、健康状态 |
| **依赖** | 任务通道（长连接/推送）、Redis（锁）、本机浏览器实例池、各平台 |
| **边界** | 不定义业务流程状态机（Java 侧）；不做内容 AI 生成；浏览器动作一律在用户本机执行，服务端不代执行（PRD §C.1） |

关键点：
- 统一契约 `PlatformAdapter`：`login / checkLoginStatus / logout / searchJobs / getJobDetail / applyJob / checkApplyStatus / getDailyQuota / isAvailable / healthCheck` [Data-backed] PRD 模块 4。契约方法在**本机 Agent 内**调用平台页面，服务端不直接触达招聘平台。
- **`getApplicationStatus(applyId)`**（新增契约成员，落实 HR 感知通道 1）：返回 `viewed|contacting|interview_invited|unknown` + 证据快照；超时/异常由调用方静默降级 [Expert judgment] 衍生自 distill-002。
- 健康检查连续 3 次失败自动停用并通知用户，恢复需手动重启用 [Data-backed] PRD 模块 4。
- 登录态失效（本地 Cookie 过期）自动暂停该平台任务 + 推送"需重新登录"（Cookie 仅本地，见 §C.5）[Data-backed] PRD 模块 4。
- 新适配器默认"测试模式"灰度，验证后转正式 [Data-backed] PRD 模块 4。
- 高校平台：通用模板（就业宝/完美校园/云研等）覆盖约 80% 同构平台，余 20% 自定义适配器，模板覆盖率标注为估算值 [Hypothesis] PRD 模块 4。

### 3.7 浏览器实例池（本机 Agent 执行层）

| 项 | 内容 |
|----|------|
| **职责** | 在**用户本机**分配与回收 ≤3 个并发浏览器实例，防检测执行。 |
| **输入** | 本机 Agent 内的适配器执行请求 |
| **输出** | 页面执行结果（成功/失败/验证码/风控） |
| **依赖** | 本机 Playwright、实例租约（本地）、代理 IP 池（用户侧/住宅） |
| **边界** | 不感知业务语义，仅执行"填充+点击"动作序列；实例与 Cookie 均驻留本机 |

关键点：
- 实例池上限 3（**每用户本机**约束，与 PRD §15.5 一致），独立隔离防单实例崩溃拖垮全部投递 [Data-backed] PRD 模块 3。
- 防检测五重保障：正态分布随机延迟 3-8s、贝塞尔鼠标轨迹、随机 UA、验证码检测暂停、Cookie 本地加密持久化；叠加代理 IP 池/指纹随机化（ADR-018 三阶段）[Data-backed] PRD 模块 3 / ADR-018。
- OOM/高水位：暂停新任务入队，执行中任务放行；告警后 5min 自动重启空闲实例；崩溃任务携幂等键 15min 内重试，不重复投递 [Data-backed] PRD 模块 3。
- 排队任务超 30min 标记过期，通知用户可手动重试 [Data-backed] PRD 模块 3。

### 3.8 AI 编排服务（服务端 Python LLM 网关）

| 项 | 内容 |
|----|------|
| **职责** | 统一承接 LLM 调用：模型路由、降级链、配额与超时。 |
| **输入** | `/internal/ai/*` 请求、LLM 响应 |
| **输出** | 统一结构 AI 结果（分数/题目/评估/文案/理由） |
| **依赖** | LLM（DeepSeek）、Redis（配额计数） |
| **边界** | 不落业务数据（结果回写经 MQ 由 Java 侧负责） |

关键点：
- 降级链按场景逐级回退（匹配→规则引擎→随机；面试题→题库→模板；评估→建议→不评分）[Data-backed] PRD §7.3。
- 全实例不可用：AI 功能降级，非 AI 功能（简历编辑/浏览/投递）照常，顶栏"AI 服务维护中"横幅 [Data-backed] PRD §7.3。
- 单次调用超时重试 1 次，仍失败降级；面试对话保留上下文可断点续聊 [Data-backed] PRD §7.3。
- 配额耗尽：紧急任务（投递联动）优先配额，非紧急（优化/生成）降级规则引擎 [Data-backed] PRD §7.3。

### 3.9 面试题生成 / AI 面试（服务端 Python）

| 项 | 内容 |
|----|------|
| **职责** | 生成面试题、驱动对话式模拟面试并多维评估。 |
| **输入** | JD + 简历片段（生成）、作答文本/语音转写（评估） |
| **输出** | 题目列表+参考答案+难度、维度评分+建议、评估报告 |
| **依赖** | AI 编排（LLM）、Redis（会话缓存） |
| **边界** | 题目/报告的存储由 Java 侧负责 |

关键点：
- 面试题覆盖 JD ≥80% 技术关键词为成功标准 [Data-backed] PRD §7.2；生成上限延迟 30s（异步）[Data-backed] PRD §7.4。
- 作答评估 ≤3s（对话式交互）[Data-backed] PRD §7.4；维度：完整性/技术准确性/结构化表达/岗位匹配度（1-5）[Data-backed] PRD 模块 6。
- AI 面试仅 PC 端完整版；移动端只查看评估报告 [Data-backed] PRD 模块 6。

### 3.10 会员支付模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 会员订单创建、支付回调接收与对账、权益激活。 |
| **输入** | 下单请求、支付渠道回调、定时对账任务 |
| **输出** | 支付订单、权益变更事件、对账修正 |
| **依赖** | MySQL（订单表）、支付渠道、Redis（订单幂等） |
| **边界** | 权益判定在用户权限模块，本模块只产出权益事件 |

关键点：
- 订单 24h 有效可续付；重复支付直接返回原权益；回调未到账展示"处理中"由对账兜底 [Data-backed] PRD §12。
- 自动续费：扣款前 3 天提醒，失败保留 7 天宽限期后按降级规则处理 [Data-backed] PRD §12。
- 订单状态以支付平台回调为准，定时对账 15min 内修正本地 [Data-backed] PRD §12。

### 3.11 通知推送模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 通知模板渲染、多渠道分发与触达统计。 |
| **输入** | 业务事件（MQ 订阅：状态变更/联动触发） |
| **输出** | 移动端推送、邮件、短信、站内信 |
| **依赖** | RabbitMQ、推送渠道、MySQL（通知表） |
| **边界** | 生成通知内容由各业务模块负责，本模块不做 AI |

关键点：
- 渠道：WebSocket + 邮件 + 短信 + 微信模板消息 [Expert judgment] ADR-014。
- 面试邀请通知从服务端触发到触达 ≤10s [Data-backed] PRD §11。
- "HR 已查看/面试邀请"推送为增强型：感知到才发，感知不到不影响功能 [Data-backed] PRD 模块 7。

### 3.12 每日日报与推送模块（Java）

| 项 | 内容 |
|----|------|
| **职责** | 每日定时聚合投递/面试数据，生成日报并推送。 |
| **输入** | 定时任务（Cron 20:00）、投递记录/面试邀请数据（MySQL 查询） |
| **输出** | 日报推送（移动端）、日报邮件 |
| **依赖** | MySQL（投递/面试/通知表）、通知推送模块、定时任务框架 |
| **边界** | 不生成业务数据，纯聚合+格式化；日报内容由各业务模块负责，本模块不做 AI |

关键点：
- 每日 20:00 定时任务触发，查询当日投递/面试数据，聚合生成日报摘要 [Data-backed] PRD 场景十一。
- 日报内容：今日投递总数、成功/失败数、各平台分布、HR 查看记录、新增面试邀请、新增面试题、近 7 天趋势 [Data-backed] PRD 模块 9。
- 用户可在「我的」页面自定义推送时间 [Data-backed] PRD 模块 9。
- 用户当日无投递活动时生成"今日无投递活动"摘要，不发送空日报 [Data-backed] PRD 模块 9 边界。
- 推送发送失败时站内消息展示，邮件发送失败时自动重试 3 次 [Data-backed] PRD 模块 9 边界。

---

## 4. 接口设计

接口分三层：**(A) 外部 API**（客户端 → Java，REST）、**(B) 内部服务契约**（B01–B05 为 Java → Python(LLM 网关) 服务端内网；B06–B09 为服务端 → 本机 Agent，经任务通道）、**(C) 事件消息**（RabbitMQ，异步契约）。所有外部 API 均要求 JWT Bearer 鉴权；权限判定服务端强制 [Data-backed] PRD 模块 8。统一错误结构：`{ code, message, traceId }`，HTTP 语义 + 业务错误码。

### 4.1 接口清单（外部 API，A 层）

| ID | 方法 | 路径 | 用途 | 鉴权 |
|----|------|------|------|------|
| A01 | POST | `/api/v1/auth/login` | 登录（邮箱/验证码/微信） | 无（验证码校验） |
| A02 | POST | `/api/v1/auth/refresh` | 刷新令牌 | Bearer |
| A03 | GET | `/api/v1/users/me` | 当前用户与权益 | Bearer |
| A04 | POST | `/api/v1/resumes` | 创建简历 | Bearer |
| A05 | GET | `/api/v1/resumes/{id}/versions` | 版本列表 + diff | Bearer |
| A06 | POST | `/api/v1/resumes/{id}/ats` | 触发 ATS 评分 | Bearer |
| A07 | GET | `/api/v1/jobs` | 岗位列表（筛选/分页） | Bearer |
| A08 | POST | `/api/v1/jobs/{id}/favorite` | 收藏/忽略 | Bearer |
| A09 | POST | `/api/v1/applications/batch` | 批量发起投递（确认队列） | Bearer + 角色限额 |
| A10 | GET | `/api/v1/applications` | 投递记录列表 | Bearer |
| A11 | GET | `/api/v1/applications/{id}` | 单条投递详情（含状态机） | Bearer |
| A12 | GET | `/api/v1/strategies` | 读取策略配置 | Bearer |
| A13 | PUT | `/api/v1/strategies` | 更新策略配置（PC） | Bearer + 专业版 |
| A14 | GET | `/api/v1/adapters` | 适配器列表与状态 | Bearer |
| A15 | POST | `/api/v1/adapters/{id}/enable` | 启用/停用适配器 | Bearer + 专业版 |
| A16 | GET | `/api/v1/interviews/questions` | 面试题列表（备战） | Bearer |
| A17 | POST | `/api/v1/interviews/sessions` | 创建 AI 面试会话 | Bearer |
| A18 | POST | `/api/v1/interviews/sessions/{id}/answer` | 提交作答（文本/语音） | Bearer |
| A19 | GET | `/api/v1/interviews/sessions/{id}/report` | 评估报告 | Bearer |
| A20 | POST | `/api/v1/payments/orders` | 创建会员订单 | Bearer |
| A21 | POST | `/api/v1/payments/callback` | 支付渠道回调 | 渠道签名 |
| A22 | GET | `/api/v1/notifications` | 通知列表 | Bearer |
| A23 | GET | `/api/v1/notifications/ws` | WebSocket 连接（推送） | Bearer(Query) |
| A24 | GET | `/api/v1/daily-report/today` | 获取今日日报摘要 | Bearer |
| A25 | PUT | `/api/v1/users/daily-report/preference` | 设置日报推送时间偏好 | Bearer |

### 4.2 核心契约：批量投递（A09）

| 字段 | 值 |
|------|-----|
| **操作** | `POST /api/v1/applications/batch` |
| **用途** | 用户确认投递队列，服务端异步执行 |
| **鉴权** | Bearer；服务端校验角色日限额（免费 30/专业 100）、启用平台数、策略生效 |
| **请求体** | `{ jobIds: string[](1..50), resumeVersionId?: string, idempotencyKey: string }` |
| **校验** | `jobIds` 1-50 个；`idempotencyKey` 必填（UUID，前端生成，冲突返回既有任务） |
| **成功响应** | `202 Accepted`；`{ batchId, accepted: 1..50, rejected: [{jobId, reason}] }` |
| **错误码** | `400 INVALID_JOBS`、`401 UNAUTHORIZED`、`403 QUOTA_EXCEEDED`（超角色限）、`403 PLATFORM_DISABLED`、`409 DUPLICATE_REQUEST`（幂等冲突）、`429 RATE_LIMITED` |
| **幂等** | `idempotencyKey` Redis SETNX；同一 key 重复请求返回首次结果（200 而非再执行） |
| **约束** | 移动端免费用户仅可查看不可提交（权限矩阵）；提交后任务异步执行不阻塞 [Data-backed] PRD 模块 2/3/8 |

### 4.3 核心契约：投递详情与状态（A11）

| 字段 | 值 |
|------|-----|
| **操作** | `GET /api/v1/applications/{id}` |
| **用途** | 查询投递记录（状态机当前态 + 时间线） |
| **鉴权** | Bearer；仅可查本人数据（数据隔离） |
| **成功响应** | `{ id, jobId, platformId, status, timeline: [{from, to, at, reason}], evidence?: {viewedSnapshotUrl?...} }` |
| **状态枚举** | `pending_confirm / autofilling / submitted / viewed / contacting / interview_invited / interview_done / offer / rejected / closed` |
| **错误码** | `401 UNAUTHORIZED`、`403 FORBIDDEN`（他人数据）、`404 NOT_FOUND` |
| **说明** | `viewed/contacting` 来自 Best-Effort 感知，允许 `unknown` 缺失，不影响读取 [Expert judgment] |

### 4.4 外部告警契约：适配器状态（A14）

| 字段 | 值 |
|------|-----|
| **操作** | `GET /api/v1/adapters` |
| **用途** | 平台适配器列表、健康状态、登录态、版本 |
| **鉴权** | Bearer；免费用户"仅查看状态"，安装/配置需专业版+（字段级隐藏） |
| **成功响应** | `{ adapters: [{ platformId, name, type, version, status: ok|needs_login|disabled|testing, dailyQuota: {used,total}, healthOk }] }` |
| **错误码** | `401 UNAUTHORIZED` |

### 4.5 内部服务契约（B 层）

统一前缀 `/internal/v1`。本版区分两类契约：
- **B01–B05（AI/LLM 网关，Java → Python 服务端内网）**：仅内网可达（Nginx 不暴露），鉴权用服务间共享密钥（Header `X-Internal-Token`），结果经 MQ 回写。
- **B06–B09（投递/采集执行，服务端 → 本机 Agent）**：经任务通道（长连接/推送）下发至用户本机 Agent；**本机 Agent 不在服务端内网，采用设备级鉴权（设备令牌 + 任务签名），Cookie 不随契约传输**（见 §C.5）。全部为异步友好：耗时操作返回 `taskId`，结果经 Agent 回写。

| ID | 方法 | 路径 | 用途 | 同步/异步 | 端 |
|----|------|------|------|----------|-----|
| B01 | POST | `/internal/v1/ai/match` | JD×简历匹配打分 | 同步 ≤5s | Java→Python(服务端) |
| B02 | POST | `/internal/v1/ai/questions` | 生成面试题 | 异步 ≤30s | Java→Python(服务端) |
| B03 | POST | `/internal/v1/ai/evaluate` | 作答评估 | 同步 ≤3s | Java→Python(服务端) |
| B04 | POST | `/internal/v1/ai/resume/optimize` | 简历优化/自我介绍 | 异步 ≤10s | Java→Python(服务端) |
| B05 | POST | `/internal/v1/ai/ats` | ATS 评分 | 异步 ≤10s | Java→Python(服务端) |
| B06 | POST | `/internal/v1/apply/tasks` | 下发投递任务至本机 Agent | 异步 | 服务端→本机 Agent |
| B07 | GET | `/internal/v1/apply/tasks/{taskId}` | 查询投递任务结果（Agent 回写） | 同步 | 服务端→本机 Agent |
| B08 | POST | `/internal/v1/apply/status` | 批量触发 getApplicationStatus 轮询（本机 Agent 执行） | 异步 | 服务端→本机 Agent |
| B09 | POST | `/internal/v1/adapters/health` | 全适配器健康检查触发（本机 Agent 上报） | 异步 | 服务端→本机 Agent |

**B06 契约要点**（⚠ 对 PRD 模块 4 适配器契约的落地，执行侧为本机 Agent）：

| 字段 | 值 |
|------|-----|
| 请求体 | `{ taskId, idempotencyKey, platformId, jobId, resumeVersionId, behavioralProfile: {delaySeed, ua} }`（**不含 Cookie**；Cookie 由本机 Agent 从本地加密存储加载，绝不上传服务端，见 §C.5） |
| 处理 | 本机 Agent 接收任务 → 校验本地适配器健康 → 从**本地**浏览器实例池分配实例 → 加载**本地 Cookie** → 执行 `applyJob` → 结果经 Agent 回写服务端 |
| 结果事件 | `{ taskId, idempotencyKey, outcome: success|failed|captcha|risk_blocked|need_login, platformApplyId?, failReason?, evidence? }` |
| 关键规则 | `captcha` → 暂停全部任务+通知用户（人机协同兜底，人工处理验证码）；`need_login` → 暂停该平台+推送重新登录（本地 Cookie 失效）；`risk_blocked` → 停止所有任务 [Data-backed] PRD 模块 3/9 |

**B08 契约要点**（HR 感知通道落地的接口化，执行侧为本机 Agent）：

| 字段 | 值 |
|------|-----|
| 请求体 | `{ checks: [{ platformId, applyId }...] }` |
| 响应 | `{ results: [{ platformId, applyId, status: viewed|contacting|interview_invited|unknown, evidence?: {snapshotUrl, occurredAt} }] }`（证据快照存于本机或限时回传，不长期留存明文凭证） |
| 超时 | 单平台 8s，整体超时 20s；异常项置 `unknown` 不入状态机 [Expert judgment] |
| 触发频率 | 定时轮询，默认 6h/平台，BOSS/猎聘可配置 2-4h（高频平台）[Expert judgment] |
| 幂等推进 | `viewed` 后不再轮询该条（状态机已前进）；`unknown` 保持现状 |

### 4.6 事件消息契约（C 层，RabbitMQ）

| 事件 | 生产者 | 消费者 | 载荷要点 | 用途 |
|------|--------|--------|---------|------|
| `apply.task.created` | Java 状态机 | 本机 Agent（经任务通道） | taskId, idempotencyKey, platformId… | 投递执行（本机） |
| `apply.task.result` | 本机 Agent | Java 状态机 | 上述结果事件 | 状态推进 |
| `apply.status.changed` | Java 状态机 | 通知/AI/推荐 | applicationId, from, to, at | 联动/推送 |
| `interview.questions.generated` | Java 联动 | 通知 | questionSetId, userId | 静默入备战 |
| `hr.viewed.detected` | Java 轮询回调 | 通知 | applicationId, platformId | 增强推送 |
| `member.plan.changed` | 支付模块 | 用户权限 | userId, plan, effectiveAt | 权益切换 |
| `adapter.health.degraded` | Python 健康检查 | Java 状态机/通知 | platformId, reason | 停用+通知 |

消息语义：投递结果与联动类事件开启 RabbitMQ 手动 ack + 死信队列，重复消费依靠 `idempotencyKey`/业务表唯一键去重 [Expert judgment] ADR-004。

### 4.7 错误码总表（业务）

| 码段 | 含义 | 代表码 |
|------|------|--------|
| 400xx | 参数/状态非法 | `40001 INVALID_PARAM`、`40002 INVALID_STATE_TRANSITION` |
| 401xx | 未认证/登录失效 | `40101 TOKEN_EXPIRED`、`40102 CREDENTIAL_MISSING` |
| 403xx | 无权限/超限 | `40301 QUOTA_EXCEEDED`、`40302 PLAN_REQUIRED`、`40303 DATA_ISOLATION_VIOLATION` |
| 404xx | 不存在 | `40401 RESOURCE_NOT_FOUND` |
| 409xx | 冲突/幂等 | `40901 DUPLICATE_REQUEST`、`40902 ALREADY_APPLIED` |
| 429xx | 限流 | `42901 RATE_LIMITED` |
| 502xx | 依赖降级 | `50201 LLM_DEGRADED`、`50202 ADAPTER_UNAVAILABLE`、`50203 BROWSER_OVERLOADED` |
| 503xx | 服务维护 | `50301 MAINTENANCE` |

---

## 5. 数据设计

### 5.1 ER 图（核心实体）

![图 5-1 核心实体关系图](figures/fig-5-1-er.svg)

**图 5-1 核心实体关系图 · 依次说明**（表结构细化留待数据库设计文档）

1. 实体 ① `USER` 用户：系统根实体，承载认证信息与会员套餐归属，是"谁在投递"的起点。
2. 实体 ② `RESUME` 简历：由用户创建，一份简历可沉淀多个历史版本。
3. 实体 ③ `RESUME_VERSION` 简历版本：保存简历内容快照，投递时锁定当时版本，保证"投出去的版本"可追溯。
4. 实体 ④ `PLATFORM_ACCOUNT` 平台账号：绑定用户在招聘平台的账号元信息（平台标识、账号标识、登录态标记、多账号标签）。**Cookie 密文不存于服务端数据库**——仅由本机 Agent 本地加密存储（信封加密，不上传、不备份云端，见 §C.5）；服务端仅记录「已登录 / 需重登 / 已停用」状态供编排与推送使用。
5. 实体 ⑤ `MEMBER_ORDER` 会员订单：记录购买的服务套餐与支付状态，投递限额等权益据此判定。
6. 实体 ⑥ `JOB` 岗位：由适配器从各平台抓取，`external_id + platform_id` 全局去重。
7. 实体 ⑦ `PLATFORM_ADAPTER` 平台适配器：以代码包（`ADAPTER_CODE`）形式安装启停，解析各平台页面差异。
8. 实体 ⑧ `STRATEGY_CONFIG` 投递策略：用户自定义每日限额、匹配阈值、时段与启用平台。
9. 实体 ⑨ `APPLICATION` 投递单（枢纽）：`user_id + job_id + platform_id` 唯一约束，携带全局幂等键 `idempotency_key`，是投递域的中心实体。
10. 实体 ⑩ `APPLICATION_TASK` 投递任务：与投递单 **1:1**，是状态机驱动的最小执行单元，任务失败不影响投递单本身。
11. 实体 ⑪ `APPLICATION_EVENT` 投递事件：每次状态流转（from→to）追加一条事件流水，构成幂等与审计的时间线依据。
12. 实体 ⑫ `INTERVIEW_QUESTION_SET` 面试题集：投递成功后由 AI 联动生成，绑定 `application_id`，驱动面试模拟模块。
13. 实体 ⑬ `DAILY_REPORT` 日报记录：每日定时聚合生成，记录用户当日投递/面试统计数据，`user_id + report_date` 唯一约束，每日一条。

关系组依次说明：用户域（①→②③④⑤⑧⑫⑬）为 1:N 拥有/配置关系；投递主线汇聚于 ⑨ 投递单：③ 简历版本供投递引用、⑥ 岗位为投递对象、④ 账号提供投递身份、⑦ 适配器执行投递动作；投递单派生 ⑩ 任务（1:1）、沉淀 ⑪ 事件（1:N）、触发 ⑫ 题集（1:N）。主链路（①→⑨）以绿色加粗标识，全链路靠 `idempotency_key` 保证不重不漏 [Expert judgment]。

### 5.2 核心表与关键字段（概要）

| 表 | 关键字段 | 索引/约束 | 说明 |
|----|---------|----------|------|
| `user` | id, email, phone, password_hash, plan | uk(email), uk(phone) | BCrypt 哈希 |
| `platform_account` | id, user_id, platform_id, login_state(ok\|need_login\|disabled), account_label | uk(user_id, platform_id) | 仅存账号元信息与登录态；Cookie 密文存本机 Agent 本地，不上云 [Data-backed] PRD §8.2 / §15 / §C.5 |
| `resume` / `resume_version` | content JSON / snapshot JSON | idx(resume_id) | 快照式版本 [Expert judgment] ADR-012 |
| `job` | platform_id, external_id, jd_raw JSON | uk(platform_id, external_id) | 去重键防重复采集 |
| `application` | user_id, job_id, platform_id, status, idempotency_key | uk(idempotency_key), idx(user_id,status) | 状态机承载表 |
| `application_task` | task_id, application_id, idempotency_key, state | uk(idempotency_key) | 幂等执行单元 |
| `application_event` | application_id, from→to, reason | idx(application_id) | 事件溯源/审计 |
| `strategy_config` | user_id, daily_limit, match_threshold… | uk(user_id) | 策略快照 |
| `interview_question_set` | application_id, state, questions JSON | idx(user_id) | 状态：generating→ready |
| `member_order` | order_no, plan, status, paid_at | uk(order_no) | 支付对账 |
| `adapter_registry` | platform_id, version, status | uk(platform_id) | 适配器元数据 |
| `daily_report` | id, user_id, report_date, total_applications, successful, failed, hr_views, interview_invitations, new_questions, platform_breakdown JSON, sent_at | uk(user_id, report_date) | 日报快照，每日一条 |

### 5.3 数据一致性规则

| 规则 | 实现 |
|------|------|
| 投递幂等 | `application.idempotency_key` 与 `application_task.idempotency_key` 双唯一键；Redis SETNX 前置 [Data-backed] PRD 模块 3 |
| 状态机一致性 | 状态变更在同一事务内写 `application` + `application_event`；Redis 分布式锁防并发推进 [Expert judgment] ADR-008 |
| 读写分离 | Java 侧写主库读从库；支付回调后强制读主库 [Data-backed] ADR-003 |
| 大字段隔离 | 简历快照 JSON 不放主业务表；文件走 OSS 外链 [Data-backed] ADR-003 |
| 跨服务一致性 | Java/MySQL 与 Python(LLM 网关) 不共享库：Python 结果经 MQ 事件回写，Java 侧事务落库，利用幂等键收敛重复（最终一致）[Expert judgment] ADR-002 |
| 本机 Agent ↔ 服务端一致 | 投递任务状态以服务端为权威（10 状态机）；本机 Agent 执行结果经任务通道回写，断网/崩溃由服务端孤儿任务清扫（§3.4）+ Agent 上线补拉收敛；Cookie 仅本地、不参与跨端一致（§C.5）[Expert judgment] 对齐 PRD §15 / §23.4 |
| 离线冲突 | 简历冲突以最后保存为准；投递操作冲突后发者提示"已在投递中" [Data-backed] PRD 模块 8 |
| 保留期限 | 简历/面试记录：注销后 30 天；Cookie：登出清除 [Data-backed] PRD §8.2 |

---

## 6. 非功能设计

### 6.1 性能

| 场景 | 目标 | 设计策略 | 证据 |
|------|------|---------|------|
| 匹配度 | ≤5s | 同步调用 B01，LLM 超时 4s 降级规则引擎 | [Data-backed] PRD §7.4 |
| 作答评估 | ≤3s | 同步调用 B03，流式输出可选 | [Data-backed] PRD §7.4 |
| 面试题生成 | ≤30s | 异步 B02，结果 MQ 回写 | [Data-backed] PRD §7.4 |
| 投递联动 | ≤5min | `apply.status.changed` 事件立即触发生成，独立队列 | [Data-backed] PRD §7.4 |
| 推送触达 | ≤10s | 通知模块直连推送渠道，短链路 | [Data-backed] PRD §11 |
| 浏览接口 | 日均 500 DAU 场景 p95 < 500ms | MySQL 索引 + Redis 热点岗位缓存 | [Expert judgment] ADR-009 容量基线 |

### 6.2 安全

| 域 | 措施 | 证据 |
|----|------|------|
| 认证 | JWT RS256 无状态；私钥存 KMS/配置中心不落库 | [Expert judgment] ADR-018 |
| 密码 | BCrypt strength ≥10，禁止 MD5/SHA1 | [Data-backed] ADR-018 |
| 敏感数据 | **Cookie 本地加密（信封加密）存于本机 Agent，不上传服务端、不备份云端**（§C.5，对齐 PRD §15.1）；简历 AES-256 服务端加密；密钥与业务库分离、定期轮换 | [Data-backed] PRD §8.2 / §15 / ADR-018 |
| 数据隔离 | 所有查询携带 userId 条件；管理员仅审计只读 | [Data-backed] PRD 模块 8 |
| 限流 | Sentinel 按接口/用户/IP 多维限流，登录/投递/支付单独阈值 | [Data-backed] ADR-018 |
| 传输 | 全链路 TLS；内部契约 `X-Internal-Token` 共享密钥 | [Expert judgment] ADR-018 |
| 合规 | 不存储平台密码仅存 Cookie 密文；用户可导出/删除全部数据；隐私政策首启确认 | [Data-backed] PRD §8.3 |
| 摄像头 | 本地画中画，不评估/录制/上传；拒绝授权不影响功能 | [Data-backed] PRD 模块 6 |

### 6.3 可用性

| 场景 | 策略 | 证据 |
|------|------|------|
| LLM 不可用 | 全场景降级链；非 AI 功能不受影响 | [Data-backed] PRD §7.3 |
| 单适配器故障 | 3 次健康失败自动停用，其余平台照常 | [Data-backed] PRD 模块 4 |
| 浏览器 OOM | 暂停入队、执行中放行、5min 自愈 | [Data-backed] PRD 模块 3 |
| Java/Python 进程 | 单机 systemd 守护 + 健康探针自动拉起；云主机快照备份 | [Expert judgment] ADR-015 |
| 数据库 | 云 MySQL 主从，自动备份，RPO ≤30min | [Expert judgment] ADR-003/015 |
| 定时任务 | 状态轮询/对账/续费提醒由 Java Scheduler + Redis 锁防重入 | [Expert judgment] |

### 6.4 可观测性

| 域 | 实现 | 关键指标 |
|----|------|---------|
| 指标 | Prometheus + Grafana | 投递成功率、队列积压、浏览器池水位、LLM 延迟/配额、适配器健康 |
| 日志 | Loki（集中采集） | 双服务统一格式含 traceId；投递任务全链路日志 |
| 追踪 | 双服务透传 `X-Trace-Id`（HTTP Header + MQ 属性） | 从用户请求到浏览器执行的链路串联 |
| 告警 | Alertmanager | 成功率 <90%、队列积压 >100、浏览器 OOM、适配器批量停用、LLM 全降级 |

指标来源与 PRD §10.1 核心指标对齐；埋点事件（投递发起/结果/面试题生成/采纳/推送触达）保持两端一致 [Data-backed] PRD §10.2；**埋点事件名与字段 schema 见 §6.11 B2（v3.3 落成）**。

### 6.5 韧性、兼容与安全体系（重导出自 PRD §23 / §28 / §29 / §30 / §31.3 / §31.4 / §31.9）

> 本节将 PRD 的「五层生产事故防线」（§23 韧性 · §24 响应 · §28 预防 · §29 本机 · §30 最小化）落成 HLD 设计决策。本产品最强约束即「先保证不出现生产事故」，故可靠性设计权重高于常规 HLD。

**A. 三端版本兼容与契约管理（PRD §23.1 + §30.2）**
| 项 | 设计决策 | 证据 |
|----|---------|------|
| 版本号 | 本机 Agent（A）/ 移动端壳（M）/ 后端 API（S）各自语义化版本 + 独立 `contract_version`（后端声明） | [Data-backed] PRD §23.1 |
| 兼容承诺 | 后端对最近 2 个主版本向后兼容；破坏性变更经双写/双读过渡 ≥1 周期 | [Data-backed] PRD §23.1 |
| 协商握手 | 启动时上报 `client_version + contract_version`，后端返回 `negotiated_capabilities` 裁剪功能 | [Data-backed] PRD §23.1 |
| 安全下线 | 后端下发 `minimum_supported_version`；低于此版本的 Agent **拒绝其自动投递信令**，仅允许手动/查看（修正 §23.1 缺安全下线） | [Data-backed] PRD §30.2 |

**B. 本机 Agent 安全模型（PRD §23.2）**
| 威胁面 | 设计决策 |
|--------|---------|
| 最小权限 | Agent 以普通用户权限运行，文件系统仅限自身目录（`%APPDATA%/ResumeAgent` 或 `~/Library/Application Support/ResumeAgent`）；不请求管理员 |
| 网络白名单 | 出向仅招聘平台域名 + 后端域名 + 配置中心域名，其余拒绝 |
| 内容注入 | 岗位/简历文本走纯文本或受控组件，禁止 `innerHTML`；JD 链接默认不自动打开 |
| 供应链 | Playwright/浏览器二进制固定版本 + 哈希校验（SBOM），自动更新经签名校验，禁远程脚本 |
| 防远程滥用 | 远程信令仅"唤醒"，投递指令须用户侧二次确认，不可被远程强制注入 |
| 自校验 | 启动校验自身二进制/配置完整性（签名+哈希），异常拒绝运行 |

**C. Schema 演进与数据迁移（PRD §23.3）**：持久化表带 `schema_version`；迁移脚本版本化、幂等、可回滚；字段变更先双写 ≥1 周期再切读；大表分批限流迁移；迁移失败一键回滚至上一 `schema_version` [Data-backed] PRD §23.3。

**D. 服务端 DR + Agent 本地降级（PRD §23.4）**：核心无状态服务跨 AZ 部署，有状态 DB 异步复制（RPO≤24h）；故障切换 RTO≤30min；**后端宕机时本机 Agent 纯本地降级**——已确认投递照常执行（本地队列），仅"查看/同步/推送"受损，不卡死、不重复投递，恢复后经信令通道增量重连 [Data-backed] PRD §23.4。

**E. 配置中心 fail-closed（PRD §23.5 + §30.1）**：配置中心（Nacos/Apollo/自研 KV）与 Feature Flag 共用通道；可热更限流/匹配权重/熔断/采集频率/文案；Agent 启动拉全量 + 长连接/轮询增量（≤5min）。**fail-closed 默认（修正 §23.5 fail-open）**：本地配置校验失败/缺失/签名不符时，默认套用最严限流 + 暂停自动投递，而非沿用旧值；校验先于执行（签名+schema+阈值合理性），异常即拒并告警 [Data-backed] PRD §23.5 / §30.1。

**F. 弱网/代理/离线队列（PRD §23.6）**：长连接心跳 30s、连续 3 次丢失判断线、指数退避重连（加 jitter 防惊群）；重要操作先本地落盘再异步上报；支持系统代理，公司网络屏蔽时提示切网，**不自动翻墙**；离线队列上限 500 条，超限丢弃最旧非关键项（关键投递优先） [Data-backed] PRD §23.6。

**G. 压测与混沌（PRD §23.7）**：上线前按容量模型 1.5× 压测（P99/错误率门禁）；混沌注入（后端宕/DB延迟/Agent崩溃/网络分区）；压测不过不发布，季度 DR 演练复用 [Data-backed] PRD §23.7。

**H. 日志留存与 trace 采样（PRD §23.8）**：应用日志 30 天、审计日志 24 月、trace 7 天；trace 默认 10% 采样 + 错误 100%；高成本日志（LLM 请求体）仅记 token 计数控成本 [Data-backed] PRD §23.8。

**I. 缓存击穿/雪崩（PRD §23.9）**：TTL 加随机抖动；热点 key singleflight 回源；多级缓存（本地+Redis），Redis 不可用降级本地并限流 [Data-backed] PRD §23.9。

**J. 多端配置冲突（PRD §23.10）**：服务端为配置权威；冲突按 LWW + 版本向量防乱序；PC/移动端同改以带时间戳后者覆盖并推送"配置已更新"，不静默 [Data-backed] PRD §23.10。

**K. A/B 实验（PRD §23.12）**：用户级随机分流（user_id hash）；实验配置走配置中心灰度；指标口径对齐 PRD §10.3；护栏：实验不影响核心安全（自动投递仍需用户确认） [Data-backed] PRD §23.12。

**L. 事故预防护栏（PRD §28）**
| 机制 | 设计决策 | 证据 |
|------|---------|------|
| LLM 成本双闸（§28.1） | 单用户实时速率+日预算双限；日耗 70%/90% 内/外告警，100% 自动降级规则匹配；单会话最大调用轮次；全局成本突增 +300% 告警 | [Data-backed] PRD §28.1 |
| 反滥用/投递速率熔断（§28.2） | 账号共享/多设备异常 → 二次验证或冻结；黑产评分拦截；本机 Agent 连续失败/平台风控 → 自动暂停该平台并冷却，不无限重试 | [Data-backed] PRD §28.2 |
| 诈骗/虚假岗预警（§28.3） | 收费/高薪异常/私下转账岗打风险标签；高风险默认不投，需二次确认；批量诈骗岗触发 §24.3 撤回 | [Data-backed] PRD §28.3 |
| 发布门禁（§28.4） | 涉及投递/限流/配置中心的变更须过灰度门禁+自动化回归+配置校验；动态基线异常自动升 SEV | [Data-backed] PRD §28.4 |

**M. 本机 Agent 事故预防（PRD §29）**
| 机制 | 设计决策 | 证据 |
|------|---------|------|
| 看门狗/强制终止（§29.1/§30.6） | 内置心跳+关键线程自检，超时自愈；资源限流失效兜底强制降级/终止；用户一键强杀（普通权限可随时结束）；启动环境校验；OS 级看门狗（launchd/任务计划/systemd）兜底失联；强杀级联回收 Playwright 子进程树 | [Data-backed] PRD §29.1 / §30.6 |
| 凭证失效停手+状态分流（§29.2/§30.11） | 每次请求前校验会话；失效立即停该平台所有重试+推重登；401/403/风控退避上限转"待人工"；区分真失效/风控挑战/临时失败三类状态 | [Data-backed] PRD §29.2 / §30.11 |
| 自更新回滚（§29.3/§30.7） | 更新走"下载→签名校验→保留上一版→切换"；启动失败自动回滚上一版；连续回滚 N 次失败进受限安全模式+显式报错；更新密钥 CRL 吊销；构建隔离防同源 bug | [Data-backed] PRD §29.3 / §30.7 |
| 本地留痕防篡改（§29.4） | 关键动作写本地 append-only 日志（时间戳+平台+jobId+结果），只读+校验和；不含明文 Cookie/密钥；与服务端审计互补 | [Data-backed] PRD §29.4 |
| 睡眠/唤醒补偿（§29.5） | 检测错过调度窗口；唤醒后补投（仍有效期）；补投前按 idempotency_key 去重；计入当日限额不突破 | [Data-backed] PRD §29.5 |
| "不确定就停"（§29.6） | 任意不确定场景默认暂停并提示用户，而非盲目重试/继续；用户可显式覆盖（如高风险岗） | [Data-backed] PRD §29.6 |

**N. 机制级兜底（PRD §30）**
| 机制 | 设计决策 | 证据 |
|------|---------|------|
| 权威时钟（§30.3） | 日限额/日预算/定时调度以服务端 UTC+8 为准；本机偏差>5min 暂停自动投递并提示 | [Data-backed] PRD §30.3 |
| 离线多设备锁（§30.4） | 后端不可达时同账号多 Agent 走本地选举+单设备自动投递；恢复后按 idempotency_key 幂等去重收敛 | [Data-backed] PRD §30.4 |
| break-glass 自动止血（§30.5） | 量化条件（全网误投率>X%/同版本崩溃率>Y%/成本突增>Z 倍）命中即自动 kill+全网暂停，无需等人工；事后补授权+审计，与双授权并存 | [Data-backed] PRD §30.5 |
| LLM 硬上限（§30.8） | 单次调用 `max_tokens` 硬上限（匹配<512/面试题<1024/评估<2048）+ 总超时 15s + 重试≤2；超时即降级规则匹配 | [Data-backed] PRD §30.8 |
| 脱敏强制拦截层（§30.9） | 日志写入经脱敏过滤器（Cookie/token/身份证/手机号正则掩码）；落盘日志定期 PII 扫描告警；本地日志同走过滤器 | [Data-backed] PRD §30.9 |
| 诈骗误杀兜底（§30.10） | 诈骗识别误判率上限（正常岗被拦≤0.5%）纳入指标；用户可"仍要投递"覆盖并反哺样本 | [Data-backed] PRD §30.10 |
| 前台资源感知（§30.12） | 以 CPU/前台活跃进程/电源状态/勿扰模式判定高负载；命中降速或暂停非紧急任务，结束后自动恢复；阈值对用户透明 | [Data-backed] PRD §30.12 |

**O. 第三方依赖韧性（PRD §31.3）**：支付状态双源校验（轮询+webhook，超时转"待确认"不重复扣）；推送送达率监控跌破阈值切备用通道（站内信/邮件）；**招聘适配器健康分=DOM 解析成功率，失败率>20% 持续 5min 自动降级该平台，选择器/规则走配置中心热更无需发版** [Data-backed] PRD §31.3。

**P. API 鉴权模型（PRD §31.4）**：本机 Agent/移动端用 OAuth2 客户端凭证 + 短期 access token（15min）+ 可轮换 refresh token；每设备一会话，单账号并发设备数受限；refresh token 支持服务端吊销列表；API 网关统一限流+WAF+bot 防护，Agent↔服务端可选 mTLS [Data-backed] PRD §31.4。

**Q. 容量弹性（PRD §31.9）**：无状态服务上 K8s + HPA（CPU+自定义 QPS）；有状态纵向扩容+只读副本；秋招峰值用定时扩容预案；扩缩上限接单位经济预算 [Data-backed] PRD §31.9。

### 6.6 事件响应与韧性运营（重导出自 PRD §24 + §31.12）

| 项 | 设计决策 | 证据 |
|----|---------|------|
| 事件分级（§24.1） | SEV1（致命，5min 确认/15min 止血）/ SEV2（严重，15min/1h）/ SEV3（一般，30min/当日）；7×24 Oncall 双备份；SEV1/2 指定唯一事故指挥（IC）；区分"生产事故 SEV"与"工单 P1–P3" | [Data-backed] PRD §24.1 |
| Runbook（§24.2） | 通用 SOP：发现→定级→止血→诊断→恢复→告知→复盘；专属 Runbook（误投/坏更新/密钥泄露/支付多扣）按图处置 | [Data-backed] PRD §24.2 |
| 误投/过量撤回（§24.3） | 全局暂停队列+圈定影响范围（idempotency_key+时间窗）；平台支持则调撤回接口，否则标记"异常投递"置顶提醒；标准通知模板+责任/补偿区分 | [Data-backed] PRD §24.3 |
| 泄露应急（§24.4） | 触发 PIPL 第 57 条：≤1h 启动补救（吊销凭证/隔离/评估面）；向网信部门报告+告知个人；全过程入审计 | [Data-backed] PRD §24.4 |
| kill switch（§24.5） | 配置中心下发"冻结自动更新+回滚上一稳定版"/"一键熔断配置"/"全局急停投递"；仅 SEV1 IC+技术负责人双授权触发，动作入审计 | [Data-backed] PRD §24.5 |
| 指标/复盘（§24.6） | MTTD/MTTR 按 SEV 分档（SEV1 MTTR≤1h）；错误预算=月度可用性基线；SEV1/2 强制 blameless postmortem，改进项入 backlog | [Data-backed] PRD §24.6 |
| 状态页（§24.7） | 独立状态页 + 应用内横幅 + SEV1/2 每 30min 播报；统一由 IC/公关口径发布 | [Data-backed] PRD §24.7 |
| 责任边界三维（§24.8） | 产品 bug（平台担责+补偿）/ 用户操作（引导自查不补偿）/ 平台行为（协助申诉不担责），以审计+配置版本+通知日志为证据链 | [Data-backed] PRD §24.8 |
| 依赖中断统一升级（§24.9） | 依赖中断纳入 SEV；状态页+横幅统一播报；恢复后自动解除降级 | [Data-backed] PRD §24.9 |
| 故障域隔离（§24.10） | 依赖拓扑图标注；Blast Radius：后端宕→Agent 本地降级、单平台失效→隔离、单用户异常→天然隔离 | [Data-backed] PRD §24.10 |
| Game day（§24.11） | SEV1 剧本每季度≥1 次桌面推演+可控注入（测试坏配置验证 kill switch）；覆盖误投/泄露/坏更新/支付多扣 | [Data-backed] PRD §24.11 |
| 灰度自动回滚 guardrail（§31.12） | 错误率>2% 持续 5min / p99>基线 2 倍 / 误投率>0.1% / 成本突增>3 倍 / Agent 崩溃率>1% → 自动回滚上一良好版；与 break-glass 协同 | [Data-backed] PRD §31.12 |

### 6.7 本机 Agent 安全、资源与分发（重导出自 PRD §21.3 / §29 / §34.1 / §34.3 / §34.4）

| 项 | 设计决策 | 证据 |
|----|---------|------|
| 本地库 corruption 恢复（§21.3） | 不备份 Cookie/在途进度；PC 损坏重装后拉非敏感配置+用户重登各平台；投递/日报历史由服务端持有可恢复；**本地 SQLite 每次启动+每 30min 跑 `PRAGMA integrity_check`，WAL+原子事务；每日轻量快照（结构+任务状态+去重 key）；损坏进受限安全模式+显式弹窗，绝不静默；去重丢失时宁可重登重确认也不自动续投** | [Data-backed] PRD §21.3 |
| EV 代码签名防误报（§34.1）🔴 | 采用 EV 代码签名证书过 SmartScreen；上线前跑主流安全软件云查杀加白并留存工单号；误报响应 SOP（1 工作日内提交复核+官网说明页） | [Data-backed] PRD §34.1 |
| 功耗电量硬预算（§34.3） | 空闲 CPU<[X]%、内存常驻<[Y]MB、磁盘 I/O 限流；**绝不阻止系统睡眠**（任务改唤醒后补投）；仅电池且<[Z]% 暂停非紧急采集；目标值待 v0.9 回填 | [Data-backed] PRD §34.3 |
| 浏览器/OS 兼容矩阵（§34.4） | 支持 Win10 22H2+ / Win11 / macOS 12+；Chromium 内核 110+；Playwright 绑定版本随 Agent 发布；EOL 系统提前 [N] 月公告并停新功能 | [Data-backed] PRD §34.4 |

### 6.8 密钥与凭证工程（重导出自 PRD §20.5 / §30.7 / §31.4 / §31.7）

| 项 | 设计决策 | 证据 |
|----|---------|------|
| KMS 信封加密+轮换（§20.5/§31.7） | 服务端密钥（LLM Key/推送证书/主密钥）经 KMS 存储，禁硬编码/入仓/打日志；主密钥与数据密钥分离，自动轮换（90 天）+ 版本化（旧版可解密历史）；泄露时吊销该数据密钥版本并重加密 | [Data-backed] PRD §20.5 / §31.7 |
| Agent 二进制签名密钥 CRL（§30.7） | 更新签名密钥设撤销列表，泄露即吊销、旧构建拒绝加载 | [Data-backed] PRD §30.7 |
| API token 短期化+吊销（§31.4） | access token 15min 短命降低泄露窗口；refresh token 支持服务端吊销列表 | [Data-backed] PRD §31.4 |
| 本机 Cookie 隔离 | Cookie 不离开用户设备、不上云、不进 Secrets 管理（与 API token 分层） | [Data-backed] PRD §20.5 |

### 6.9 测试、质量门禁与可观测性深化（重导出自 PRD §18.4 / §26.1 / §31.5 / §31.8 / §35.7）

| 项 | 设计决策 | 证据 |
|----|---------|------|
| SLI/SLO + 合成监控（§31.5） | SLI：API p99 延迟/可用性/错误率/队列积压/Agent 心跳存活率；SLO 分组件（API 可用性 99.9%、匹配 p99≤5s），接错误预算；**服务端定时经推送通道向 Agent 发探活 probe 度量用户侧实际可用**（被动心跳补充） | [Data-backed] PRD §31.5 |
| deadman 告警（§18.4） | 监控 agent/采集管道失联、指标长期无更新即触发「无数据告警」；关键看板（Agent 在线率、投递成功率）缺失数据本身作为 P2 告警，而非默认正常 | [Data-backed] PRD §18.4 |
| 桌面 E2E + 平台 Mock（§31.8） | Playwright 驱动 Agent 自身 UI 跑"连接→匹配→投递→撤回"全链路；建录制/回放层（真实 DOM fixtures），适配器改动先过选择器回归；CI 含 E2E 门禁 | [Data-backed] PRD §31.8 |
| 代码质量门禁 CI（§35.7） | 静态检查+单测覆盖率≥[阈值]%+集成/E2E 冒烟+依赖与密钥扫描；主干保护强制 review+门禁通过方可合入；门禁失败阻断发布 | [Data-backed] PRD §35.7 |
| Prompt 版本管理与回归（§26.1） | Prompt 模板版本化+golden set 回归评测（Cohen's κ≥0.6 匹配口径）；LLM 主备切换时跑质量回归确认评分一致性 | [Data-backed] PRD §26.1 |

### 6.10 发布治理与合规（重导出自 PRD §35.1 / §35.2）

| 项 | 设计决策 | 证据 |
|----|---------|------|
| OSS 许可证合规（§35.1）🔴 | 上线前跑 SBOM+许可证扫描（pip-licenses/FOSSA/ScanCode）；白名单仅允许 MIT/BSD/Apache-2.0/PSF，**禁 AGPL 与未声明许可证**；pyinstaller 打包 Chromium/Playwright 单独确认分发授权并保留 NOTICE；法务 v0.9 前出具开源合规确认 | [Data-backed] PRD §35.1 |
| 正式 Beta / v0.9 验证计划（§35.2）🔴 | 招募 [N] 名代表性用户（应届/社招×Win/macOS×首期 5 平台）；准入/退出标准（关键假设回填：HR 查看率/面试邀请率首样、错投率≤10%、误报加白完成、崩溃率<[X]%）；假设回填清单映射 §2.1/§3/§16；缺陷分级 triage 接工单 | [Data-backed] PRD §35.2 |
| 运营/品牌/增长类（§35.3–§35.6 / §35.8） | VoC 闭环、分析数据管道与 BI、定价弹性实验、危机公关预案、竞品监测飞轮属**产品运营职责**，不在本技术设计档范围，由产品/运营另行闭环（见 §1.2 标注） | [Out-of-scope] PRD §35 |

> 说明：§6.5–§6.10 为 v3.0 基于 PRD v4.5 重导出新增，将 PRD §17–§35（原 v2.0 HLD 整体遗漏的事故预防/可靠性/本机 Agent 安全/发布治理机制）补为 HLD 设计决策，并经 `check_prd_hld_traceability.py` 门禁校验全覆盖。SVG 架构图按用户决策暂不动（图待重绘见 §2.2/§2.6）。

### 6.11 设计深度补强（v3.3 基于 PRD 缺口审计 B1–B7 落成）

> 本节将上一轮「PRD × HLD 逐章缺口审计」识别的 7 项 HLD 级缺口（B1–B7）落成设计决策。这些项 PRD 已给出要求，但 v3.2 HLD 仅引用章节号、未落设计，故在进 LLD 前于本版拍板，避免下游模块缺乏统一架构约束。「本机优先 / 单用户自用」的产品形态是本版决策的总基调（见 §1.3 / §2.6）。

**B1. 语义检索 / embedding 架构决策（PRD §7.5 / §16.4 / §20 / §27.2）**

| 项 | 决策 |
|----|------|
| 向量检索选型 | **v1.0 不引入独立向量服务**：匹配主路径为「LLM 语义匹配 + 规则层（加权余弦 / Jaccard）」；仅当候选岗位规模化（跨用户语义检索量上升）时再评估**本地向量存储**（SQLite + 向量扩展，随 Agent 或后端），避免简历向量上云（PIPL §8.4） |
| 本地检索预算 | 若启用向量检索，单用户岗位—简历匹配检索 ≤500ms（PRD §27.2）；v1.0 不走向量，此预算留作后续扩展验收基线 |
| embedding 成本 | 计入 §16.4 LLM/推理项（单用户日解析 ~100 份，约 ¥0.5–2/月）；v1.0 主路径不依赖 embedding，该项成本为 0 |
| 增量更新 | 简历/岗位变更触发增量重算，避免全量（与 §21.1 采集节奏一致） |
| 扩展点 | §2.5 技术选型预留「本地向量扩展」接口位，LLD 阶段按实际规模决策是否落地 |

依据：[Data-backed] PRD §27.2 / §7.5 / §16.4

**B2. 埋点事件 schema 与指标口径（PRD §10.2 / §10.3 / §33）**

v3.2 §6.4 仅述「埋点事件保持两端一致」，本版落事件名 + 字段 + 口径（采集经 SDK → MQ → 数仓 ODS→DWD→DWS 物化；管道 SLA 接 §18.4 可观测性；隐私合规走 §31.10 / §8.3 最小化）：

| 事件名 | 触发时机 | 关键字段 | 口径 / 可信度 |
|--------|---------|---------|--------------|
| `apply.initiated` | 用户点一键投递 | `job_count`, `platform_dist[]` | 投递转化率 |
| `apply.result` | 单次投递完成 | `outcome(success/failed)`, `fail_reason`, `platform` | 定位高失败率平台（高） |
| `interview.questions.generated` | 联动触发 | `job_id`, `q_count`, `elapsed_ms` | AI 生成质量 |
| `interview.questions.adopted` | 用户点模拟作答 | `q_type`, `difficulty` | 用户兴趣度 |
| `mobile.apply.confirmed` | 移动端确认队列 | `job_count`, `confirm_ratio` | 移动端效率 |
| `push.delivered` | 推送到达 | `push_type`, `clicked` | 推送有效性（高） |
| `adapter.registered` | 新适配器上线 | `platform_type`, `onboarding_sec` | 扩展效率 |
| `page.view` | 进入页面 | `page_path`, `dwell_ms` | 移动端分布 |

指标口径严格对齐 §10.3（HR 查看率 / 面试邀请率标「估算值」，投递成功率 / 封号率「高」）；增长漏斗（激活/留存/付费转化）见 §10.3 衔接 §33。

依据：[Data-backed] PRD §10.2 / §10.3

**B3. 多环境隔离模型（PRD §22.1）**

| 项 | 决策 |
|----|------|
| 三环境隔离 | dev / staging / prod 的后端、数据库、Secrets（KMS 域）、消息通道相互隔离；prod 凭证不进 dev / staging |
| 本机 Agent 环境 tag | 构建时注入环境标识；仅 **prod 版 Agent** 连接 prod 后端与真实招聘平台；dev / staging 连沙箱 |
| 防误投硬约束 | 非 prod 环境（含本地调试）**一律禁止连接真实招聘平台**，统一 mock 适配器或平台沙箱账号；CI / 自测触发投递时目标平台校验环节拦截真实域名 |
| 灰度租户隔离 | 受邀灰度用户归入 prod 独立租户标签，其采集 / 投递行为可单独观测与回滚，不影响全量 |

依据：[Data-backed] PRD §22.1

**B4. 订阅权益矩阵（功能 × 套餐）（PRD §12 / 模块 8）**

> 完整矩阵见 §3.1（权限模块，驱动权限系统设计的总制品）。本版决策要点：
> - **矩阵是权限系统的唯一权威来源**：§4.1 A03 返回 `permissions`、§4.3/§4.5 字段级校验据此强制执行；LLD 权限模块直接消费该矩阵，不得另行硬编码阈值。
> - **「管理员」非付费套餐**：为产品运营后台角色，与免费/专业/高级三档互斥叠加。
> - **数量型权益动态上限**：日投递上限（30/100/100）与 §9.1 滑块动态上限联动；接入平台数（≤3 / 全部）与 §15.5 本机实例池「≤3 并发」语义不同（前者为套餐权益、后者为资源约束），已在 §15.5 澄清。

依据：[Data-backed] PRD §12 / 模块 8

**B5. 匹配度模型设计（PRD §7.5 / §11 验收）**

| 项 | 决策 |
|----|------|
| 输出 | 0–100 匹配度 + 可解释标签（Top-3 匹配点 / Top-1 不匹配点），作为「是否投递（>60%）」与面试准备依据 |
| 方法 | v1.0 规则 + 模型混合：结构化解析（技能栈/行业/城市/经验/学历）→ 规则层硬性过滤（城市不符/经验差>3 年/学历不满足→低分+原因）+ 软性加权（技能 40% / 行业 20% / 城市 20% / 经验 20%）；模型层（v1.1 可选）LLM 语义匹配 + 理由（§7.1 / §26.1） |
| 冷启动 | 无历史先用规则层 + 默认权重，灰度采集「实际是否投递 / 是否收到面试」回流正样本 |
| 可解释 + 覆盖 | 每次展示匹配点 / 不匹配点，用户可「强制投递 / 排除」，覆盖行为回流为训练信号 |
| 验收 | 分桶与人工标注一致性 Cohen's κ≥0.6；错投率≤10%（§11）；「排序一致性≥70%」为辅助观测，非门槛 |

依据：[Data-backed] PRD §7.5 / §11

**B6. LLM 输出内容安全 / 价值观对齐（PRD §26.4 / §17.4）**

| 项 | 决策 |
|----|------|
| 过滤层 | AI 输出（面试题 / 评估 / 话术）经内容安全审核，拦截政治敏感 / 违法 / 歧视 / 骚扰；不鼓励造假夸大（呼应 §17.4 伦理） |
| 价值观可测口径 | 不输出歧视性（性别 / 年龄 / 地域）表述；以 §26.1 golden set「歧视性表述抽检命中率 = 0」为验收；「中立 / 专业 / 鼓励性」为取向非硬指标 |
| 审核失败处理 | 触发内容不展示，提示「内容不可用，请换种问法」，记审计（§22.3） |
| 衔接 | 在 §8.4 脱敏 / 授权框架内执行；LLM 主备切换（§2.5 / §34.2）不影响安全层 |

依据：[Data-backed] PRD §26.4

**B7. 离线优先同步引擎（PRD §31.2 / §23.10 / §27.1）**

| 项 | 决策 |
|----|------|
| v1.0 范围 | **纯本地优先 + 服务端权威**：仅「设置 / 收藏」走双向同步；简历编辑强制单设备编辑（避免冲突面）；投递任务锁见 §27.1 / §30.4 |
| 同步模型 | 每条用户数据带 `version + updated_at + device_id`；字段级 LWW + 版本向量；简历多版本为不可变快照、仅 active 切换可变，冲突 LWW + 用户合并提示（呼应 §23.10 用户可感知） |
| 同步通道 | 本地变更入待同步队列（复用 §23.6 离线队列），恢复后 delta 同步；服务端为权威 |
| 冲突可视化 | 合并时弹「X 在手机改了、Y 在电脑改了，请选择 / 已保留两者」，不静默覆盖 |
| 延后项 | 全量用户数据双向同步（含面试记录）标 v1.1+，工作量中等，不阻塞 v1.0 |

依据：[Data-backed] PRD §31.2

> 说明：B1–B7 为 v3.3 新增设计决策，补全 v3.2「仅引用未设计」的 HLD 级缺口；§C 五大约束与 §1.2 矩阵不受影响。SVG 架构图仍按用户决策暂不动（图待重绘见 §2.2/§2.6），其中 B6 内容安全层、B3 环境 tag、B7 同步队列可作后续图补充点。

---

## 7. 错误处理

### 7.1 错误分类与总体策略

| 类别 | 示例 | 策略 |
|------|------|------|
| 客户端错误 | 参数非法、状态机非法转换 | 40002 拒绝并返回原因，前端提示 |
| 权限类 | 超限、未订阅 | 403xx，前端引导升级/等待 |
| 依赖类 | LLM 不可用、适配器故障、实例池满 | 降级链 / 隔离 / 重试，返回 502xx 语义 |
| 基础设施 | 网络、数据库抖动 | 指数退避重试 + 熔断，事务回滚 |
| 平台风控 | 验证码、封禁风险 | 暂停 + 人工介入（人机协同兜底） |

### 7.2 降级链与兜底（继承 PRD §7.3 并落地）

| 场景 | 主路径 | 降级 | 兜底 | 依据 |
|------|--------|------|------|------|
| 匹配度 | LLM 语义匹配 | 规则引擎关键词 | 随机排序 | [Data-backed] PRD §7.3 |
| 面试题生成 | LLM + 题库 | 纯题库 | 预设模板题 | [Data-backed] PRD §7.3 |
| 面试评估 | LLM 多维评分 | 仅参考建议 | 不评分 | [Data-backed] PRD §7.3 |
| ATS 评分 | LLM + 规则 | 纯规则 | 完整度展示 | [Data-backed] PRD §7.3 |
| 简历优化 | LLM 改写 | 多版本候选 | 语法检查 | [Data-backed] PRD §7.3 |
| HR 状态感知 | 轮询 getApplicationStatus | unknown 静默跳过 | 状态机允许 unknown | [Data-backed] PRD 模块 7 |
| 投递执行 | 自动浏览器模拟 | 验证码→人工处理 | 封禁→停止 | [Data-backed] PRD 模块 3 |

> 匹配度打分特征、权重与验收口径（Cohen's κ≥0.6 / 错投率≤10%）见 §6.11 B5（v3.3 落成），本表降级链据此实现。

### 7.3 熔断与隔离（投递/适配器）

| 保护对象 | 阈值/规则 | 动作 |
|----------|----------|------|
| 适配器健康 | 连续 3 次 healthCheck 失败 | 自动停用 + 通知；恢复需手动启用 [Data-backed] PRD 模块 4 |
| 浏览器实例池 | OOM/高水位 | 暂停新任务入队，5min 自动重启空闲实例 [Data-backed] PRD 模块 3 |
| 实例崩溃 | 执行中断 | 携幂等键 15min 内重试，不重复投递 [Data-backed] PRD 模块 3 |
| 排队任务 | 等待 >30min | 标记过期，通知用户手动重试 [Data-backed] PRD 模块 3 |
| 平台隔离 | 单平台失败 | 仅影响该平台，其余照常 [Data-backed] PRD 模块 3 |
| LLM 实例 | 超时重试 1 次/部分模型挂 | 切换可用模型，用户无感知 [Data-backed] PRD §7.3 |

### 7.4 幂等与重试矩阵

| 操作 | 幂等键归属 | 重试策略 | 防重复手段 |
|------|-----------|---------|-----------|
| 批量投递 | 前端生成 idempotencyKey | 失败任务指数退避最大 3 次 | Redis SETNX + 库唯一键 [Data-backed] PRD 模块 3 |
| 崩溃恢复 | 同一 key 查询实际状态 | 15min 窗口内重试 | 先查后做，非盲重 [Data-backed] PRD 模块 3 |
| 支付订单 | order_no 唯一 | 重复支付返回原权益 | uk(order_no)；回调以渠道为准 [Data-backed] PRD §12 |
| LLM 调用 | — | 单次超时重试 1 次 | 降级链兜底 [Data-backed] PRD §7.3 |
| 消息消费 | idempotency_key | 手动 ack + 死信 | 消费侧按业务键去重 [Expert judgment] |

### 7.5 支付与会员异常

| 场景 | 处理 |
|------|------|
| 支付中断 | 订单 24h 有效，可续付 [Data-backed] PRD §12 |
| 回调未到账 | "订单处理中" + 定时对账 15min 修正（以渠道为准）[Data-backed] PRD §12 |
| 重复支付 | 已支付订单再次发起直接返回权益 [Data-backed] PRD §12 |
| 自动续费失败 | 提前 3 天提醒；保留 7 天宽限期；过期按降级规则 [Data-backed] PRD §12/模块 8 |

---

## 8. 影响与迁移

### 8.1 现状盘点（Brownfield 起点）

本项目不是纯绿地：用户已存在 `get_jobs` 的 Java 项目（5 平台采集爬虫：BOSS/智联/51/拉勾/猎聘，Playwright+Selenium）与 Python 扫描器 `daily_job_scanner`，另有 LLM 集成（AiConfig/AiService/AiFilter）上线使用 [Data-backed] distill-002 可行性验证。

| 现有资产 | 处置 | 理由 |
|---------|------|------|
| 5 平台采集代码（Java） | 迁移为 Python 采集器适配器（CRAWLER），或短期保留复用 | 采集逻辑成熟，但按 ADR-002 归属 Python 侧，两套并存易漂移 |
| LlamaIndex/LLM 过滤（AiFilter） | 演进为匹配度服务的初版规则基线 | 已验证可过滤岗位，作为降级链"规则引擎"底座 |
| daily_job_scanner | 并入 CRAWLER 调度 | 避免重复调度源 |
| 自动投递写操作 | **尚未验证**（高风险点） | 必须先 PoC |

### 8.2 投递 PoC 前置（高风险验证门）

按 distill-002 落地保障机制第 1 条，**正式开发投递引擎前先执行 PoC**：

| 项 | 内容 |
|----|------|
| 目标 | 1-2 周内完成 BOSS 单平台投递闭环验证 |
| 验证点 | 表单自动填充成功率、验证码出现率、封号风险实测（小流量）、getDailyQuota 读取、幂等键语义可达性 |
| 判定依据 | 投递成功率 ≥80% 且无封号 → 按"自动为主+人工兜底"进入正式开发；显著低于 → 调整为"半自动模式"（自动填充表单，人工点最终提交） |
| 结果去向 | 作为 HLD §3.4/§3.6 的前提假设更新；写回 distill 记录与 ADR |
| 依据 | [Expert judgment] 衍生自 distill-002 落地保障机制 |

### 8.3 实施顺序（里程碑，对齐 PRD §9.3）

| 阶段 | 内容 | 出口标准 |
|------|------|---------|
| M0（第 0-2 周） | 投递 PoC + 技术栈初始化（双服务骨架/CI/监控底座） | PoC 通过；骨架可部署 |
| M1（数据链路） | 采集器/岗位库/简历库/账号体系 | 岗位入库可查询，简历可编辑 |
| M2（投递闭环） | 状态机/策略/适配器/实例池/幂等 | 单平台自动投递成功，状态闭环 |
| M3（AI 能力） | 匹配度/面试题/面试模拟/联动 | 投递后 5min 内生成面试题 |
| M4（商业化） | 会员支付/通知全渠道/移动端完整版 | 付费订阅闭环 |
| M5（规模化） | 高校模板/国聘/牛客适配器、适配器市场 | 平台接入 ≤2 人天验证 |

依赖顺序：M1 数据链路 → M2 投递闭环 → M3 AI 能力 → M4 联动付费，每段可独立验证 [Data-backed] PRD §9.3 / distill-002。

### 8.4 风险登记（新增/细化）

| 风险 | 概率 | 影响 | 缓解（HLD 层） |
|------|------|------|---------------|
| 反爬升级 | 高 | 高 | 适配器隔离 + 人机兜底 + 三阶段反风控 [Data-backed] PRD §9.2 |
| 投递写操作不可行 | 中 | 高 | PoC 先行验证门（§8.2） |
| 高校平台异构 | 中 | 中 | 通用模板 80% + 自定义适配器 [Data-backed] PRD §9.2 |
| 双服务契约漂移 | 中 | 中 | 契约单一定义源（共享 JSON Schema + 契约测试）[Expert judgment] |
| 浏览器资源耗尽 | 中 | 中 | 实例池 3 上限 + OOM 自愈 + 队列过期 [Data-backed] PRD §9.2 |

---

## 9. 已识别实现约束与待决项（进入 LLD 前闭环）

以下 3 项为 PRD 评审阶段识别的逻辑缺口（distill-002 "衍生决策"），本设计给出**处理决策**，LLD 按此落地：

### 9.1 滑块上限与角色限额冲突 → 动态上限

| 项 | 内容 |
|----|------|
| 问题 | 策略面板滑块 20-150（PRD 模块 3），但免费版日上限 30（PRD 模块 8）— 免费用户可滑到 150 却无效 |
| 决策 | 滑块最大值 = `min(150, 角色上限)`：免费 30 / 专业 100 / 高级 150；滑到超限值保存时提示并截断 |
| 落地 | 策略配置接口 A12/A13 返回 `limits: {max, current, roleCap}`，前端渲染动态区间 [Expert judgment] |
| 影响 | 无需改 PRD（模块 8 已是权威约束），仅产品交互微调 |

### 9.2 语音练习权限归属 → 归专业版

| 项 | 内容 |
|----|------|
| 问题 | PRD 模块 5 移动端有"语音练习"，但权限矩阵"面试备战内容"免费版仅"查看" — 语音练习是否免费存疑 |
| 决策 | 语音练习（含麦克风权限）归属专业版+；免费版可查看题目与参考答案文本，语音识别为专业版能力 |
| 落地 | 权限矩阵映射到接口 A16/A17：免费返回 `textOnly: true`，前端隐藏语音按钮；麦克风拒绝时降级文本输入（PRD 模块 5 边界既有） [Expert judgment] |
| 影响 | 与定价表（专业版含 AI 面试模拟）语义一致，无需改 PRD 文本 |

### 9.3 策略配置面板与权限缺口 → 字段级控制

| 项 | 内容 |
|----|------|
| 问题 | 策略面板含"平台扩展"管理入口（PRD 模块 3），但模块 8 矩阵中免费用户适配器"仅查看状态"、专业版"安装+配置" — 面板入口权限未声明 |
| 决策 | 面板内各项按权限矩阵逐行控制：免费仅看（daily_limit/match_threshold 只读），专业版可改全部策略项 + 平台开关，适配器安装/配置入口仅专业版+ 可见；管理后台独立 |
| 落地 | 前端按 `permissions` 字段（A03 返回）渲染；服务端 A12/A13/A15 逐字段校验 [Expert judgment] |
| 影响 | 与模块 8 矩阵完全对齐，无 PRD 冲突 |

### 9.4 其他待决项（不阻塞 LLD 主线）

| 项 | 状态 |
|----|------|
| 精确框架小版本号 | LLD 依赖锁定阶段确认 [Unverified — requires human review] |
| 代理 IP 池/风控参数具体值 | 随 PoC 结果调整 [Expert judgment] |
| 高校模板 80% 覆盖率 | 标注估算值，接入时逐平台验证 [Hypothesis] |
| R1 幂等键前端 UUID 反模式 | 已登记追踪（源自 distill-004）：LLD 阶段改由服务端生成 `idempotency_key` 或前端生成但服务端校验去重，消除"前端 UUID 必填"隐含假设；不阻塞本版 |
| R5 "事件溯源"措辞 | 已登记追踪（源自 distill-004）：LLD/术语统一阶段将 `application_event` 表述统一为"事件流水 / 审计日志"，避免与事件溯源（event sourcing）架构模式混淆；不阻塞本版 |

### 9.5 本版评审修订记录（v1.0 → v1.1，源自架构评审 distill-004）

| 项 | 原问题 | 修订内容 | 位置 |
|----|--------|---------|------|
| H1 数据库矛盾 | C2 容器图写 PostgreSQL，正文全程 MySQL | C2 图 PostgreSQL→MySQL 8.0；同步改 JDBC 端口 5432→3306；正文 C2 说明对齐 | §2.2、fig-c2-container.svg、fig-2-3-deployment.svg |
| H2 共享库冲突 | §5.3/ADR-002 说"不共享库"，§2.6 写"Java/Python 共享" | 统一为：**仅 Java 直连 MySQL**；Python 经 REST `/internal/*` 或订阅 MQ 访问业务数据，不直连业务库 | §2.6 ④、§5.3 |
| H3 容量算不平 | 500 DAU 起步基线 vs 浏览器池上限 3 | 定位修订为"单用户自用/极早期小规模"；500 DAU 仅作演进触发线；实例池 ≤3 为单 Agent 进程约束 | §1.3 容量基线、§2.6 ⑤ 后新增容量口径说明 |
| R4 Redis 队列口径 | C2 图标 Redis "任务队列后端"，全文队列为 RabbitMQ | Redis 描述改为"缓存/分布式锁/幂等令牌"；任务队列明确归 RabbitMQ | §2.2 C2 说明、fig-c2-container.svg |
| R2 孤儿任务清扫 | 链路在途任务崩溃会卡死 application | 新增定时清扫机制（5min 扫 stale + 重查/关单/通知），仅 Java 侧执行 | §3.4 关键点（新增段） |
| R3 状态机转移矩阵 | 仅列状态、标"单向不可逆"，缺转移边 | 补 10 状态允许转移矩阵；"无回退边、有跨阶段直达终态边"；offer 必到 closed | §3.4 关键点（新增段） |

> 说明：R1（幂等键前端 UUID 反模式）、R5（"事件溯源"措辞）留待 LLD/术语统一阶段处理，不阻塞本版；详见 distill-004。

### 9.6 本版架构对齐修订记录（v1.1 → v2.0，对齐 PRD §15 / §C）

v2.0 解决 HLD v1.1 与 PRD §15（本机 Agent 执行模型）之间的**唯一跨文档矛盾**，记为 C1（执行模型）/ C2（Cookie 存储）。修订后 HLD 与 PRD 在"客户端执行 + Cookie 本地化"上完全对齐。

| 项 | 原 HLD v1.1 表述（矛盾点） | 修订后（v2.0） | 位置 |
|----|--------|---------|------|
| **C1 执行模型** | 浏览器自动化归属服务端 Python 引擎（§2.1「AI/自动化…Playwright 投递独立为 Python 服务」、§2.2 C2「Python 自动化引擎承载浏览器自动化」、§2.2 时序 2-2「Python 调度中心从队列消费并执行」、§2.6「Python 服务（AI/Playwright 自动化）同机双进程 + 浏览器沙箱 Docker」、§3.6/§3.7「Python 引擎侧」） | 浏览器自动化下沉**用户本机 Agent**（桌面守护进程）：服务端仅保留 Java 业务 + Python(LLM 网关)；投递任务经任务通道下发本机 Agent，本地实例池 + 本地 Cookie 执行后回写 | §2.1、§2.2 ③、§2.2 时序 2-2、§2.5、§2.6 ②/⑤、§3.6、§3.7、§4.5(B06–B09) |
| **C2 Cookie 存储** | Cookie 密文存服务端（`PLATFORM_ACCOUNT.cookie_ciphertext`、§5.2「AES-256-GCM 密文，密钥独立」、§6.2「Cookie AES-256-GCM…服务端加密」） | Cookie **仅本机 Agent 本地加密（信封加密），不上传、不备份云端**；服务端 `platform_account` 仅存账号元信息与登录态（ok/need_login/disabled） | §5.1 ④、§5.2、§5.3、§6.2、§4.5 B06（去除 credentialRef） |
| 图一致性 | fig-c2-container / fig-2-3-deployment / fig-2-2-apply-flow 绘有服务端浏览器沙箱 | 已在本版正文标注 `⚠ 图待重绘`；三图需按新文本重绘为「本机 Agent 层承载浏览器实例池」 | §2.2、§2.6、§2.2 时序 2-2 |
| 上游文档引用 | 头部/§10 引用「PRD v3.0」 | 更新为「PRD v4.5 最终版」 | 头部、§10 |
| 容量口径（已部分一致，本版固化） | 原 §2.6 容量说明已用「单用户本机/单节点」表述，但主架构仍服务端，二者漂移 | 本版将「单用户本机 Agent + 自有账号 + 住宅/移动代理 IP」固化为唯一执行形态，与服务端无浏览器算力瓶颈自洽 | §1.3、§2.6 ⑤、§15（PRD） |

> 对齐结论：HLD v2.0 与 PRD v4.5 §15 / §C.1 / §C.5 在「本机执行 + Cookie 不上云」上已无矛盾。**剩余未决项（法务三块 PIPL 第24/DSAR/威胁模型、无障碍、精确小版本号）与本次对齐无关，仍按 PRD §19 登记延后。**

### 9.7 本版重导出修订记录（v2.0 → v3.0，基于 PRD v4.5 全文重导）

v3.0 解决 v2.0「仅打 C1/C2 补丁、未基于 PRD 重导出」的方法论缺陷：PRD v4.x 新增的十几章事故预防/可靠性内容在 v2.0 HLD 中整体缺席。本版将 PRD §17–§35 全部落成 HLD 设计决策。

| 项 | v2.0 状态 | 修订后（v3.0） | 位置 |
|----|-----------|--------------|------|
| 事故预防/可靠性覆盖 | §6 仅 46 行（性能/安全/可用性/可观测性），PRD §17–§35 几乎全缺 | 新增 §6.5–§6.10，覆盖 PRD §17/§18.4/§21.3/§22/§23/§24/§26/§27/§28/§29/§30/§31/§34/§35.1/§35.2 的设计决策 | §6.5 韧性兼容安全 / §6.6 事件响应 / §6.7 本机安全资源分发 / §6.8 密钥凭证 / §6.9 测试质量门禁 / §6.10 发布治理 |
| 本机 Agent 安全与自愈 | 仅"崩溃重试" | 看门狗/强杀级联/OS 看门狗、自更新回滚+CRL、本地留痕、睡眠唤醒、不确定就停、本地库 corruption 恢复、EV 签名、功耗硬预算、OS 兼容矩阵 | §6.5 M/N、§6.7 |
| 密钥与凭证工程 | 仅一句 KMS | KMS 信封加密+自动轮换+泄露吊销、Agent 签名密钥 CRL、API token 短期化+吊销 | §6.8 |
| 可观测性深化 | 仅常规告警 | deadman 告警、SLI/SLO+合成监控、桌面 E2E+平台 Mock、代码质量门禁 CI、Prompt 回归 | §6.9 |
| 发布治理 | 无 | OSS 许可证合规（🔴 分发 blocker）、正式 Beta/v0.9 验证计划 | §6.10 |
| §1.2 追溯矩阵 | 仅 15 行，停在 PRD v3.0 章节集 | 补全 §17–§35 每行追溯 + 显式登记 out-of-scope（§1/§2/§3/§4/§13/§14/§32/§33） | §1.2 |
| 防漂移机制 | 无 | 新增 `PRD-HLD-对齐规范.md` + `check_prd_hld_traceability.py` 门禁，PRD minor/major 必触发重导出复核 | 独立文件 |

### 9.8 图文字描述对齐修订记录（v3.0 → v3.1，仅改图注文字，不动 SVG）

v3.1 不改动架构与 SVG，仅将 C1/C2 的**文字说明**对齐 PRD v4.5（此前图注未经 PRD 回溯核验）。

| 项 | v3.0 图注 | 修订后（v3.1，对齐 PRD） | 位置 |
|----|-----------|--------------------------|------|
| C1 用户画像引用 | "用户画像详见 PRD §4.1"（§4.1 实为竞品概况） | 改为"用户画像见 PRD §5.1"；日投递量口径补全"专业版及以上 80–100 份 / 免费版 30 份，需 v0.9 验证，见 §3/§6.2/§12" | §2.2 C1 说明① |
| C1 招聘平台列表 | 仅 BOSS/猎聘/智联 | 补全首期 5 平台（BOSS/猎聘/智联招聘/前程无忧/拉勾，见 §6.2），并标注后续扩展高校/国聘（§4.2） | §2.2 C1 说明③ |
| C1 HR→系统 调用 | 误列"HR→系统"为 5 条同步调用之一 | 按 PRD §7.3 删除该箭头（HR 状态为系统→招聘平台 轮询的尽力感知，非 HR 主动回推）；同步调用改为 4 条 | §2.2 C1 说明④ |
| C2 编号碰撞 | "基础设施层"与"配色说明"同号 4 | 配色说明改为 5，消除重号 | §2.2 C2 说明⑤ |
| 图待重绘登记 | 仅 c2/2-3/2-2 三张 | 新增 `fig-c1-system-context.svg`（HR→系统 箭头 + 平台列）入待重绘清单 | §2.2 头部、C1 说明④下方 ⚠ 注 |

> 说明：本版仅修订图注文字。所有 SVG 仍按用户决策暂不动；`fig-c1/fig-c2/fig-2-3/fig-2-2` 四张图的视觉内容需在后续按本版文字重绘（已全程标注 `⚠ 图待重绘`）。

### 9.9 图文字描述对齐修订记录（v3.1 → v3.2，仅改图注文字，不动 SVG）

v3.2 承接 v3.1 的「图注对齐 PRD」工作，将其余时序图/流程图文字说明回溯核验，纠正两处架构错位（均源于 v3.0 前未基于 PRD 重导出）。

| 项 | v3.1 图注 | 修订后（v3.2，对齐 PRD） | 位置 |
|----|-----------|--------------------------|------|
| 2-4 HR 感知执行归属 | "Java 状态机…调用 Python 适配器 `getApplicationStatus`" 隐含服务端执行 | 改为"经内部契约下发至本机 Agent，由本机 Agent 适配器加载本地 Cookie 查询平台页面"；明确规避"HR→系统"反模式（PRD §7.3 / C1） | 图 2-4 说明①–②、④ |
| 2-4 轮询触发频率 | "默认 6h/次" 未提高频平台 | 补"高频平台可配置 2–4h，见 §4.5 B08" | 图 2-4 说明① |
| 2-5 LLM 可用性 failover | 仅"主 LLM → 规则引擎"两级降级，缺主备切换 | 新增"主不可达自动切备用 LLM（1 主 + 1–2 备用）+ golden set 质量回归（κ 容差）"一级（PRD §34.2）；`model` 枚举扩为 deepseek / backup / rule | 图 2-5 说明③–④、⑥、⑧ |
| 图待重绘登记 | 四张（c1/c2/2-3/2-2） | 新增 `fig-2-4-hr-status.svg`、`fig-2-5-ai-match.svg` 入待重绘清单 | §2.2 头部、图 2-4/2-5 ⚠ 注 |

> 说明：图 2-2 / 2-3 / 5-1 的图注已在 v2.0/v3.0 对齐（本机 Agent 执行、Cookie 本地化、实体④服务端不存 Cookie 密文），本次回溯核验确认无错位，未改动。所有 SVG 仍按用户决策暂不动。

> 本版对齐经 `check_prd_hld_traceability.py` 校验：全部 MUST_TRACE 章节已追溯、版本一致（绿灯）。SVG 架构图按用户决策暂不动，图待重绘见 §2.2/§2.6。

### 9.10 设计深度补强修订记录（v3.2 → v3.3，基于 PRD 缺口审计 B1–B7 + D 类卫生）

v3.2 完成「图文字对齐 PRD」后，对 PRD × HLD 做逐章设计深度审计，识别出 7 项「仅引用未设计」的 HLD 级缺口（B1–B7）与若干文档卫生问题（D 类）。本版于进 LLD 前拍板这些架构决策，避免下游模块缺乏统一约束。

| 项 | 类别 | v3.2 状态 | 修订后（v3.3） | 位置 |
|----|------|-----------|----------------|------|
| B1 语义检索 / embedding | HLD 缺口 | §2.5 技术选型无向量库，匹配仅 LLM+规则 | v1.0 不引入独立向量服务；LLM 语义+规则为主，预留本地向量扩展接口位；给出检索预算/成本/增量更新决策 | §6.11 B1、§2.5（预留位） |
| B2 埋点事件 schema | HLD 缺口 | §6.4 仅"保持两端一致" | 落成 8 类事件名+关键字段+口径（对齐 §10.2/§10.3），管道 ODS→DWD→DWS | §6.11 B2、§6.4（交叉引用） |
| B3 多环境隔离 | HLD 缺口 | 全程"单机起步"，凭证隔离只字未提 | 三环境隔离+Agent 环境 tag+防误投硬约束+灰度租户隔离 | §6.11 B3 |
| B4 订阅权益矩阵 | HLD 缺口 | 仅 §1.2 引用"模块 8 权限矩阵"无制品 | 落成「功能×套餐」完整矩阵（含管理员角色），定为权限系统权威来源 | §3.1（矩阵）、§6.11 B4 |
| B5 匹配度模型 | HLD 缺口 | 只有降级链无打分设计 | 落成 0–100 输出+规则层权重(技能40/行业20/城市20/经验20)+冷启动+κ≥0.6 验收 | §6.11 B5、§7.2（交叉引用） |
| B6 LLM 内容安全 | HLD 缺口 | 完全未提 | 过滤层+价值观可测口径(golden set 歧视命中=0)+审核失败处理 | §6.11 B6 |
| B7 离线同步引擎 | HLD 缺口 | 仅 LWW 简述 | 落成同步模型+通道+冲突可视化，v1.0 仅设置/收藏双向同步，简历强制单设备 | §6.11 B7、§5.3（交叉引用） |
| D1 关联文档表版本 | 文档卫生 | §10 写"本文档 HLD v2.0" | 改为"本文档 HLD v3.3" | §10 |
| D2 头部/页脚版本戳 | 文档卫生 | v3.2 / 2026-08-14 | v3.3 / 2026-08-15 | 头部、页脚 |
| D3 R1/R5 未登记追踪 | 文档卫生 | §9.5 留"待 LLD"，未入追踪 | 登记进 §9.4 待决项（含处理方向），明确不阻塞本版 | §9.4 |
| D4 标题术语残留 | 文档卫生 | §3.8/§3.9 标题"Python 引擎侧" | 改为"服务端 Python LLM 网关"/"服务端 Python"（浏览器自动化已移出 Python，见 v2.0） | §3.8、§3.9 |
| D5 §1.2 权限矩阵引用 | 文档卫生 | 写"§3.2 鉴权设计"（实际 §3.1 为用户与权限） | 修正为"§3.1 / §4.3 鉴权设计" | §1.2 |
| 防漂移机制 | 持续 | 已落地（校验器+pre-commit+CI） | v3.3 改动经校验器复验仍全绿；§1.2 新增补强追溯行 | 独立文件 |

> 对齐结论：HLD v3.3 与 PRD v4.5 在章节追溯与版本耦合上仍一致（校验器绿灯）。剩余未决项（法务三块 PIPL 第24/DSAR/威胁模型、无障碍、精确小版本号、6 张 SVG 重绘）与本次补强无关，仍按 PRD §19 登记延后。

---

## 10. 关联文档与后续交付

| 文档 | 状态 |
|------|------|
| PRD v4.5 最终版 | 已完成（上游，本版重导出依据） |
| ADR-001 ~ 023 | 已完成（决策依据） |
| **本文档 HLD v3.3** | **本次交付（设计深度补强 B1–B7 + 修 D 类文档卫生）** |
| 数据库设计（ER + 表结构 + 索引） | 下一步 |
| API 契约文档（含 Mock） | 下一步 |
| LLD 详细设计（类图/时序/算法） | 待排期 |
| 测试计划 / 部署运维手册 | P2 后续 |

> 文档版本：2026-08-15 · v3.3（设计深度补强 B1–B7 + 修 D 类文档卫生）· 编写依据 software-design-document 规范（设计评审导向）