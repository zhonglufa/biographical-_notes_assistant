# LLD 详细设计：岗位浏览模块（服务端 Java）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合审查报告 P2「岗位浏览」业务子域真缺失项）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD v3.25（§3.3 岗位浏览模块 / §4.1 A 层 / §6.11 B1 匹配度模型 / B2 埋点）× PRD v4.5 模块 2（岗位浏览·搜索·收藏）/ 模块 8（离线缓存）/ 模块 9（日报无关）/ §20
> 定位：LLD 序列之**岗位浏览模块**（服务端 Java）；岗位聚合展示 + 匹配度获取 + 收藏/忽略/浏览记录；**只读**岗位数据，不抓取、不投递
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

- **职责**（HLD §3.3）：岗位聚合展示、匹配度获取、收藏/忽略/浏览记录。
- **边界**：不抓取岗位（Python 采集器经 B10/B11 入库，本模块只读 `job` 表）；不执行投递（投递由状态机模块 §3.4 经 C1/C2 承接）。本模块对岗位数据**只读**。
- **依赖**：MySQL（岗位域表：`job` / `job_match` / `job_favorite` / `job_view`）、AI 匹配服务（B01，同步 ≤5s，仅单岗按需）、Redis（离线缓存/热门岗位热键）。
- **职责补充（显式登记）**：HLD §3.3.1 提及 `GET /jobs/{id}`（详情）与 `GET /jobs/{id}/match`（按需匹配），但外部 API 注册表（A 层）仅登记 A07（列表）与 A08（收藏/忽略）。本 LLD 将二者作为 A07 资源集合下的标准 REST 子资源处理，并登记 T-JB-1 在编码期显式拆分为 A26/A27 入注册表（非静默）。

## 1. 岗位聚合查询（A07 GET /jobs）

- **入参**（查询串，schema：`jobs-search.request.schema.json`）：`keyword?` / `location?` / `platform?` / `salaryMin?` / `page`(≥1) / `pageSize`(1..100)。
- **出参**（schema：`jobs-list.response.schema.json`）：`items[]` + `total` + `page` + `pageSize`；每条 `jobStub` 含 `jobId/title/company/platformId/salaryMin?/salaryMax?/location?/source/matchScore?/matchBand?/matchReason?/favorited?/collectedAt`。
- **来源聚合**：所有已接入平台采集入库的岗位统一聚合，每条标注 `platformId`（来源，[Data-backed] PRD 模块 2）。
- **匹配度读取（反范式缓存，关键设计）**：列表**不**逐条同步调用 B01（否则 N×≤5s 不可接受）。列表读 `job_match` 表（按当前用户 `preferred_version` 预先异步算好的 `score/band/reason`，见 §2），O(1)/行；缺失或过期（TTL，见 T-JB-2）的岗，列表返回 `matchScore=null` 并在前端标「匹配度待计算」，由 `/jobs/{id}/match` 按需补算。
- **离线缓存**：移动端缓存最近 50 条岗位（[Data-backed] PRD 模块 8）；服务端对列表响应附 `ETag`（基于 `(query, max(collected_at))` 派生），客户端据此校验缓存有效性，避免无网重拉全量。
- **分页与排序**：默认按 `collected_at DESC`；`salaryMin` 过滤为服务端数值区间；`platform` 等值过滤；结果超 `pageSize` 走游标式 `page/pageSize`（不跳页深分页，防大 offset 慢查询）。

## 2. 匹配度获取（B01 同步 ≤5s + 异步反范式填充）

- **按需单岗匹配**（`GET /jobs/{id}/match`，T-JB-1）：同步调用 B01（JD + 用户首选简历版本文本 → `score(0..1)` + `matchedSkills` + `explanation`），**≤5s** SLA（HLD §3.3.1）；超时/LLM 降级返回规则分并标 `degradeFlag`（复用 `b01-match.response.schema.json` 语义）。
- **列表预计算管道（异步）**：用户 `preferred_version` 变更（C5 `member.plan.changed` 不触发，但 `resume.preferred.changed` 事件触发）后，异步作业对该用户全量/增量岗位跑 B01，写 `job_match(score,band,reason,computed_at)`；`band` 由 `score` 映射：绿 ≥80 / 蓝 60–79 / 灰 <60（[Data-backed] PRD 模块 2 色彩规则）。
- **色彩档契约**：`matchBand ∈ {green, blue, gray}`，与 HLD §3.3 关键点一致；前端按档着色，不暴露原始分亦可。
- **幂等与成本**：单岗按需匹配按 `(user_id, job_id, resume_version_id)` 去重；异步管道按 `computed_at` + 版本号增量，避免全量重算。

## 3. 收藏 / 忽略 / 浏览记录（A08 POST /jobs/{id}/favorite）

- **动作**：`action ∈ {favorite, ignore}`（schema：`jobs-favorite.request.schema.json`）；幂等（重复同动作 = 无副作用）；`ignore` 用于从投递推荐中过滤（状态机模块 §3.4 读取 `job_favorite.action='ignore'` 排除）。
- **存储**：写 `job_favorite(user_id, job_id, action, created_at)`，软删（`action='removed'`）保留审计；响应 `jobs-favorite.response.schema.json` 含 `ok/status(favorited|ignored|removed)`。
- **浏览记录**：任意详情/列表曝光经 `GET /jobs/{id}` 或列表拉取时异步写 `job_view(user_id, job_id, viewed_at, source)`（不阻塞主响应，落库走本地 MQ/批写）；支撑「最近浏览」与离线缓存命中统计。
- **权限**：`job_favorite`/`job_view` 强约束 `user_id` 归属（服务端强制，跨用户访问返回 `DATA_ISOLATION_VIOLATION`/404，不复用他人收藏）。

## 4. 数据表对齐（数据库设计 LLD 收口）

- 复用 `job` 表（采集去重 `uk_platform_ext`，见数据库设计 LLD §3.1）。
- **本 LLD 发现并闭合的真实缺口**：A08 收藏/忽略与浏览记录、列表匹配度缓存在原数据库设计 LLD 中**无对应表**。已在 `LLD-数据库设计-模块设计.md` §3.1 新增三张表并登记 ER/索引：
  - `job_match(user_id, job_id, resume_version_id, score, band, reason, computed_at)` —— 匹配度反范式缓存（§1/§2）。
  - `job_favorite(user_id, job_id, action, created_at)` —— 收藏/忽略/软删（§3）。
  - `job_view(user_id, id, job_id, viewed_at, source)` —— 浏览记录，时序高增按月分区（§3）。
- 三表主键/首列均含 `user_id`（§6.15 分片预留零迁移）；`job_view` 入时间分区冷热分离；`job_favorite`/`job_match` 入用户维分片预留清单。

## 5. 事件契约

- 订阅：`resume.preferred.changed`（触发 §2 异步匹配管道重算）。
- 发布（可选，供推荐/日报消费）：`job.favorite.changed {userId, jobId, action}`，经 C 层 MQ 广播；不触发投递，仅影响推荐过滤与日报统计。
- 埋点（B2）：`job.viewed` / `job.searched` / `job.matched_shown` 事件（含 `band`/`platform`/`source`），供 §27.4 漏斗与 §33 增长复用。

## 6. 错误码映射（复用 A 命名空间，不新增）

- `RESOURCE_NOT_FOUND` / `NOT_FOUND`：岗位不存在或不可见（A08/A26/A27）。
- `INVALID_PARAM`：分页/过滤参数非法（A07）。
- `DATA_ISOLATION_VIOLATION` / `FORBIDDEN`：越权访问他人收藏/视图。
- `RATE_LIMITED`：搜索/匹配高频限流（与全局限流策略一致）。

## 7. 待决项登记（非静默）

| 项 | 说明 |
|----|------|
| T-JB-1 拆分 A26/A27 入注册表 | 单岗详情 `GET /jobs/{id}` 与按需匹配 `GET /jobs/{id}/match` 当前作为 A07 子资源；编码期显式登记为 A26/A27 并补 schema，使外部 API 契约完整 |
| T-JB-2 匹配度 TTL 与刷新策略 | `job_match.computed_at` 过期窗口（建议 24h 或简历版本变更即失效）、列表缺失匹配度的降级展示规则，由配置中心定 |
| T-JB-3 浏览记录保留期 | `job_view` 时序保留期与匿名化策略（建议 90 天），关联 §8.2 最小化与审计 |

## 8. 契约索引

| 端点/契约 | 文件 | 状态 |
|----------|------|------|
| A07 查询参数 | `contracts/jobs-search.request.schema.json` | fully-detailed |
| A07 响应 | `contracts/jobs-list.response.schema.json` | fully-detailed |
| A08 请求 | `contracts/jobs-favorite.request.schema.json` | fully-detailed |
| A08 响应 | `contracts/jobs-favorite.response.schema.json` | fully-detailed |
| B01 匹配（复用） | `contracts/b01-match.*.schema.json` | fully-detailed |
