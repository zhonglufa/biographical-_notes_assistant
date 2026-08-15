# LLD 详细设计：平台适配器系统

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合 HLD §9.4 接口完整性残余 #110 / #111）
> 编写依据：LLD 交付标准（IEEE 1016-2009 设计视图 / GB-T 8567—2006 详细设计 / Amazon LLD 模板）
> 关联上游：HLD v3.16（§3.6 / §4.5 / §4.7.1 / §6.13.3 / §6.14）× PRD v4.5 模块 4
> 定位：LLD 序列之**适配器模块**（执行侧本机 Agent；编排侧服务端）；与首选模块「本机 Agent 与投递执行」(v1.2) 协同
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

平台适配器系统负责把各招聘平台的页面差异**收敛为统一契约**，使上层（投递状态机、岗位浏览、策略引擎）不感知平台特性。核心约束（来自 HLD §3.6 / ADR-003）：

- **执行侧 = 用户本机 Agent**：所有浏览器动作（登录、投递、查询、采集）一律在用户本机执行；服务端**不直接触达招聘平台**，仅经任务通道下发指令、回收结果。
- **Cookie 不出本机**：凭证经信封加密存于本机，服务端 `platform_account` 仅存账号元信息与登录态（ok/need_login/disabled）。
- **统一门面 `PlatformAdapter`**：每个平台一个适配器代码包，实现同一接口契约（见 §2）。
- **选择器外置**：平台 DOM/XPath/CSS 选择器外置为配置中心热更的 `SelectorBundle`，禁止硬编码（HLD §6.13.3）。

数据流总览：

```
服务端(编排) ──B06/B08/B09/B10/B11──> 本机 Agent ──浏览器实例池(本地Cookie)──> 招聘平台
   ^                                  │
   └─────B07 结果回写 / crawler-result 写入 JOB 实体────┘
```

---

## 1. 统一适配器门面契约（PlatformAdapter）

门面接口为机器可读注册表：`design/contracts/adapter-facade.methods.json`（schema：`adapter-facade.registry.schema.json`，contractVersion 1.0.0）。十个方法按 `kind` 分类：

| 方法 | kind | 参数 | 返回 | 说明 |
|------|------|------|------|------|
| `login` | lifecycle | platformId, credentialRef | loginState | 加载本地 Cookie 建立会话；credentialRef 指向本机加密凭证，非明文密码 |
| `checkLoginStatus` | query | platformId | loginState | 探测 Cookie 健康；失效→置 `login_expired` |
| `logout` | lifecycle | platformId | void | 清本机会话 |
| `searchJobs` | trigger | query, filters, geo, page | jobStub[] | 采集岗位列表（入 B 系列，见 §4） |
| `getJobDetail` | trigger | externalJobId | job | 采集岗位详情（入 B 系列，见 §4） |
| `applyJob` | action | jobId, resumeVersionId, behavioralProfile | applyResult | 投递执行；behavioralProfile 控制拟人抖动 |
| `checkApplyStatus` | query | applyId | hrStatus | HR 感知通道 1：`viewed/contacting/interview_invited/unknown`（HLD §3.6.1） |
| `getDailyQuota` | query | platformId | quota | 平台每日投递上限查询 |
| `isAvailable` | query | platformId | bool | 适配器健康与启用态 |
| `healthCheck` | query | platformId | healthReport | 单平台健康探针（DOM 解析成功率等） |

**平台绑定硬约束**（注册表 `platformBinding`）：`deployedAt=local-agent`、`executedAt=local-agent`、`cookieScope=local-only`——任何平台适配器不得绕过本机执行或上传 Cookie。

**反爬拟人基线**（注册表 `antiBot`）：`humanLikeDelaySec=[3,8]`（正态分布随机延迟）、`mouseTrajectory=bezier`、`captchaPause=true`（遇验证码即暂停全平台+通知）、`cookieLocalEncrypt=true`。

---

## 2. B 系列内部契约（服务端 ↔ 本机 Agent）

B06/B08/B09 字段契约见 HLD §4.5（已落地）。本 LLD 补全 **B07 / B09 字段 schema** 并新增 **B10 / B11（采集触发）**，全部为机器可读契约，纳入 `design/contracts/` 校验器。

### 2.1 B07 投递任务结果查询响应（schema：b07-task-result.schema.json）

服务端经 `GET /internal/v1/apply/tasks/{taskId}` 查询本机 Agent 回写的结果：

| 字段 | 类型 | 说明 |
|------|------|------|
| taskId / idempotencyKey | string | 任务标识与幂等键（ADR-006 四元组之一） |
| status | enum(pending/running/done/failed) | 任务执行态 |
| outcome | enum(success/failed/captcha/risk_blocked/need_login) \| null | 终态结果；与 HLD §4.5 B06 结果事件 `outcome` 对齐 |
| platformApplyId | string \| null | 平台侧投递号 |
| failReason | string \| null | 失败原因（供 `AGENT-1xxx` 桥接，见 §5） |
| evidence | object \| null | 证据快照（截图 URL/解析痕迹），不长期留存明文凭证 |
| updatedAt | int64 | 回写时间戳 |

### 2.2 B09 适配器健康上报（schema：b09-health.schema.json）

本机 Agent 收到 `POST /internal/v1/adapters/health` 触发后，上报单平台健康：

| 字段 | 类型 | 说明 |
|------|------|------|
| platformId / healthy / checkedAt | string/bool/int64 | 主键 + 健康布尔 + 探针时间 |
| reason | string \| null | 不健康原因（login_expired/rate_limited/version_mismatch/unreachable） |
| metrics.domParseSuccessRate | number[0,1] | **健康分核心指标**（HLD §6.13.3）：失败率>20% 持续 5min → 自动降级该平台 |
| metrics.avgLatencyMs / cookieHealthy / selectorBundleVersion | — | 延迟、Cookie 健康、选择器包版本 |

### 2.3 B10 / B11 采集触发（schema：b10-search-jobs.schema.json / b11-get-job-detail.schema.json）

服务端经任务通道下发采集指令，本机 Agent 加载本地 Cookie 查询平台页面：

- **B10** `POST /internal/v1/crawl/search`：`{ platformId, query, filters?, geo?, page? }` → 触发 `searchJobs`。
- **B11** `POST /internal/v1/crawl/detail`：`{ platformId, externalJobId }` → 触发 `getJobDetail`。

二者请求体 `additionalProperties:false`，不含任何凭证（Cookie 本机加载）。结果经 §4 采集回写路径入 B 系列。

---

## 3. 适配器生命周期与编排

状态机（与注册表 `lifecycleStates` 一致）：`installed → test_mode → enabled ⇄ disabled`，异常 `degraded`，登录失效 `login_expired`。

- **灰度**：新适配器默认 `test_mode`，验证（测试模式 + 选择器回归）通过后转 `enabled`（HLD §3.6）。
- **健康熔断**：连续 3 次 healthCheck 失败 → 自动 `disabled` + 通知用户，恢复需手动启用（HLD §7.3）。
- **登录失效**：本地 Cookie 过期 → 该平台 `login_expired` + 暂停任务 + 推送"需重新登录"（HLD §3.6）。
- **风控熔断冷却**：单平台连续验证码/风控 → 立即熔断 + 指数退避（base 15min ×2ⁿ，上限 6h）；同账号全平台 `risk_blocked` 即停（HLD §6.14.3/§6.14.4）。

---

## 4. 采集路径入 B 系列（#111 核心收口）

`searchJobs` / `getJobDetail` 的服务端触发路径此前未契约化（HLD §9.4 残余）。本 LLD 闭环如下：

1. 服务端经 **B10/B11** 下发采集指令（§2.3）。
2. 本机 Agent 加载本地 Cookie，经浏览器实例池查询平台页面，解析出岗位。
3. 结果按 **crawler-result.schema.json** 回写：
   ```
   { taskId, kind: "searchJobs"|"getJobDetail", jobs: [job...], collectedAt }
   ```
   `job` 实体（`crawler-result.$defs.job`）即 HLD §5.1 ⑦ `JOB` 实体：`externalJobId + platformId` 全局去重（§5.2）。
4. 服务端消费 `crawler-result` → 写入 `JOB` 表（采集路径入 B 层），并发布 **新事件 `crawler.job.discovered`**（C 层，事件信封，见 HLD §4.6 增补）供岗位浏览/匹配消费。
5. **节流同源**：采集频率 ≤ 平台公开页更新周期（默认 6h/平台，与 B08 HR 轮询同源节流，HLD §6.11）；避开高峰。

> 此路径与 B06 投递执行共用"本机执行 + 结果回写"骨架，差异仅在触发目的（采集 vs 投递）与结果实体（job vs applyResult）。

---

## 5. 错误码桥接（指向 HLD §4.7.1）

适配器执行期错误统一经 HLD §4.7.1 的双向桥接表映射：

- `AGENT-1001 BrowserLaunchFailed` / `AGENT-3001 SelectorMiss` / `AGENT-4001 CaptchaTimeout` → 统一码 `ADAPTER_UNAVAILABLE`（B, retryable）。
- `AGENT-1003 BrowserPoolFull` → `BROWSER_OVERLOADED`（B, retryable 排队）。
- 平台侧结果（`failed`/`captcha`/`risk_blocked`/`need_login`）经 `outcome` 枚举承载，不进入业务错误码表。
- `AGENT-5001/5002`（进程级/持久化故障）**严禁**包装进错误信封，走健康/事件通道（HLD §4.7.1 桥接纪律）。

---

## 6. 测试与可追溯性

- **选择器回归**：适配器改动先过真实 DOM fixtures 选择器回归（HLD §6.11 Playwright E2E 门禁）。
- **防误投**：非 prod 环境一律 mock 适配器或平台沙箱，CI 拦截真实域名。
- **契约门禁**：本 LLD 引用的全部 schema（b07/b09/b10/b11/crawler-result/adapter-facade/external-api）纳入 `design/contracts/validate_contracts.py`，与 PRD-HLD 防漂移校验器构成双闸门，pre-commit + CI 强制。

---

## 7. 与 HLD 残余项映射

| HLD §9.4 残余 | 本 LLD 收口动作 |
|----|----|
| B07 查询结果 / B09 健康检查 补字段 schema | §2.1 / §2.2 + `b07-task-result.schema.json` / `b09-health.schema.json` |
| 适配器 searchJobs/getJobDetail 服务端触发路径入 B 系列 | §4 + B10/B11（§2.3）+ `crawler-result.schema.json` + 事件 `crawler.job.discovered` |
| 22/25 外部 API 补详细契约 | 见 `external-api.registry.json`（25 端点全枚举，3 全详 + 其余字段大纲），本 LLD 模块不直接持有 A 层契约，登记于 HLD §4.1.1 |
