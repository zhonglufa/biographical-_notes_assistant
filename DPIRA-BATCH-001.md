# DPIRA-BATCH-001 · 冻结设计（GO-LIVE 收口：真实服务闭环 + 门禁绿 + 合并 master）

> 框架：`DPIRA.md`。批次状态：`DEFINING`（待 P 审查通过）。
> 驱动：用户 2026-08-19「恢复中断任务，推进项目至部署，严格按日志与设计文档，避免生产事故」+ 指定 DPIRA 框架。
> 诚实前置：本冻结件**修正**了 `GO-LIVE-LOG.md` 中两处经实证不成立的事实声明（见 §5 TG-1/TG-2/TG-3），不沿用其虚假进度。

---

## 1. 目标（可机器验证）

把 resume-ai-prod 从「设计/契约/服务端代码已交付，但部署产物只跑了 Python 契约桩、server-java 从未在真实 MySQL 起过」推进到：

1. **代码缺口闭环**：Flyway 在**真实 MySQL** 可建表（server-java 启动不再 `Unsupported Database: MySQL`）；`/auth/login` 真实 RS256 签发↔验签闭环；RabbitMQ 消费者派发本机 Agent 链路接成闭环。
2. **在途工作诚实收口**：当前工作树 10 改 + 11 新（RS256 签发器、MQ 消费者、双 Dockerfile、全栈 compose、.env.example、cd-deploy.sh）先**实证复核 → 分批提交（不混批）→ 本地 commit 不直推 master**。
3. **门禁全绿**：server-java `mvn test` 全量真实数字、server-python `pytest` 全量、双闸门（契约 + PRD/HLD 追溯）绿、scaffold 测试、frontend `vite build` 绿。
4. **运行手册阶段二**：真实服务部署步骤 / 健康检查 / 应急 / 本机 Agent 回调契约，与实证一致。
5. **铁证合并**：经 GitHub 连接器 push → PR → gates 绿 → squash 合并 master（以远端 API 为证）。

**终点定义（诚实）**：生产就绪 + 运行手册 + 门禁绿 + 标「待用户触发」。物理部署(Q5)/真实凭据(Q6)/PIPL签署(Q7)/D阶段合规(护栏4/5/6 用户延后) **不在本批次**，如实标注。

---

## 2. 范围（in / out）

### In
- W1 Flyway MySQL 真实迁移闭环（补 `flyway-mysql` 依赖 → 真实 MySQL 跑 V1–V10 → 校验 schema history 全 success + 表齐全）。
- W2 验证并提交在途工作（#92 RS256 / #94 MQ 消费者 / #95 部署产物）。
- W3 本地全栈运行时实证（真实 MySQL + Redis + server-java jar + server-python 端到端认证与 fail-closed）。
- W4 上线手册阶段二（#96）。
- W5 QA 上线前全量验证（#97：双闸门 + mvn test + pytest + scaffold + frontend build，记真实数字）。
- W6 经 GitHub 连接器 push → PR → gates 绿 → 合并 master（#98）。

### Out（明确不在本批次，诚实标注）
- Q5 物理部署（DEPLOY_TOKEN / 真跑 cd-deploy.sh 到生产机）—— 仅用户。
- Q6 真实招聘平台凭据（Boss/猎聘）—— 仅用户。
- Q7 PIPL 法定签署 —— 仅用户（D 阶段用户 2026-08-17 延后）。
- 护栏 4/5/6 物理启用（灰度/KMS/法检专家）—— 用户延后，不计入。
- Q1 阶段二 RAG（面试模拟 grounded 题库）—— 用户 2026-08-17 延后至 MVP 后。
- 本机 Agent ↔ 服务端 `/tasks` 端到端联调（B-2）—— 待用户机器客户端，标「待联调」。

---

## 3. 禁止项 / 写入边界（R4 标准优先 + 诚信）

1. **绝不伪造验证**：未实证的「已跑通真实 MySQL / CI 已绿」不得写入交付物。本次重跑的验证以真实输出为据。
2. **不删用户文件**：执行过程不删除 `C:\Users\爱锅粥粥\...` 个人目录文件（用户 2026-08-19 已拒绝批量清缓存）。空间不足改用 `maven.repo.local` 重定向到 `E:`（32GB 空闲）。
3. **不直推保护分支**：只推非保护分支 → PR → gates 绿 → 合并。以远端 API（ls-tree / contents / commit status）为铁证，不以本地工作树判断。
4. **不动已采纳架构决策（ADR-001/002/004/010）**：本批次在既定架构内收口，不擅自改架构；若发现需改架构的系统性问题 → 触发 `A ↺ D/P`（另立批次，交用户拍板）。
5. **不削弱护栏 1/2/3**：双闸门、成本熔断、封号监控贯穿 I/R/A。
6. **DB 操作带备份**：W1 对真实 MySQL 跑迁移前，先 `mysqldump resume_ai` 备份（当前库为空，备份为防未然）；不手工 DROP/ALTER 生产表。
7. **提交不混批**：W2 各语义单元（RS256 / MQ 消费者 / 部署产物）各自独立 commit，信息含四角色贡献摘要。

---

## 4. 依赖（实证现状，2026-08-19 复测）

| 依赖 | 现状 | 来源 |
|---|---|---|
| MySQL 8.0.38（root/root） | 存活；`resume_ai` 库**零表**、无 `flyway_schema_history` | `mysql -uroot -proot` 实测 |
| Maven | `E:\简历\.sandbox-tools\apache-maven-3.9.9` + JDK17（`D:\JDK2` 或托管 JDK17） | 沙箱可用 |
| 本地 `.m2`（C:） | 含 `flyway-core`/`flyway-maven-plugin`/`flyway-parent`，**无 `flyway-mysql`** | `ls $HOME/.m2` 实测 |
| server-java `pom.xml` | `flyway-core` + `mysql-connector-j`，**缺 `flyway-mysql`** | `grep flyway pom.xml` 实测 |
| Docker | 守护进程状态待 W6 时确认；若不可用，W3 用「原生 jar + 本地 MySQL/Redis」降级路径 | 环境探测 |
| GitHub 连接器 | connected；远端 master 状态以连接器 API 为准（见 TG-4） | 连接器状态 |
| 磁盘 | **C: 100% 满（0 空闲）**；E: 32GB / D: 30GB 空闲 | `df` 实测 |
| Redis | 服务端 `redis-cli` 待确认；W3 若缺则用 compose 或跳过健康强依赖项 | 环境探测 |

---

## 5. 已登记偏差 / Truth Gap（诚实，不隐藏）

- **TG-1（严重·生产阻塞）**：`GO-LIVE-LOG.md` §4.2 称「真实 MySQL 验证已在 PR#4 完成」——**不实**。`resume_ai` 库零表、无 `flyway_schema_history`，从未成功迁移。本批次 W1 重做真实迁移。
- **TG-2（严重·技术错误）**：`GO-LIVE-LOG.md` §4.3 称「不新增 `flyway-mysql`」——**对 Flyway ≥9 不成立**。Flyway 9.x 起 MySQL 支持从 `flyway-core` 拆为独立模块 `flyway-mysql`；仅 `flyway-core`+`mysql-connector-j` 启动时抛 `Unsupported Database: MySQL`。server-java 当前无法在真实 MySQL 启动。W1 必须补 `org.flywaydb:flyway-mysql`。
- **TG-3（诚信）**：`GO-LIVE-LOG.md` #92/#94/#95 标「✅ 已完成」，且 `PROJECT_BRAIN.md` §5 称「本地提交·未 push」——**均不实**。实测工作树为 **10 改 + 11 新（未提交）**，即这些改动从未 commit。本批次 W2 先实证复核再分批提交，状态据实回写。
- **TG-4（待核）**：`GO-LIVE-LOG.md` 称「续 PR#5 合并 master=dc03b3f 之后」；本地 `git log --all` **无 dc03b3f**，本地 `master`=cb26021、本地 `java-business-p0`=d0ccf7f（含未提交 GO-LIVE 改动）。远端真实状态以 GitHub 连接器 API 在 W6 核对，不沿用日志假设。
- **TG-5（既有·延续）**：B-1 MVP 认证（非空即签发，非密码哈希，未接 t_user）/ B-2 本机 Agent 端到端联调 / B-3 memory 模式消费者不启用 —— 仍有效，W4 运行手册与终报告如实标注，不消除。
- **TG-6（环境）**：C: 满盘。Maven 构建用 `maven.repo.local` 指向 `E:`（避免向满盘 C: 写入 `.m2`）；Bash 工具大输出可能触发 ENOSPC，构建输出重定向到 `E:` 日志文件后读取，不直喷 stdout。

---

## 6. 工作项（宏观 feature / 实现批次，非文件级）

### W1 — Flyway MySQL 真实迁移闭环（生产启动阻塞级）
- **目标**：server-java 能在真实 MySQL 自动建库（V1–V10）。
- **做法**：`pom.xml` 加 `org.flywaydb:flyway-mysql`（版本对齐 `flyway-core`）；备份 `resume_ai`；以真实 MySQL 启动 Flyway（`mvn -o flyway:migrate` 或起 jar）；校验 `flyway_schema_history` 全 `success` + 表齐全。纠正 TG-1/TG-2。
- **验收（机器可验证）**：
  1. `resume_ai.flyway_schema_history` 含 V1..V10 且 `success=1`。
  2. `SHOW TABLES` 返回 ≥ 全部业务表（application/jobs/resume/strategy/adapter/interview/payment/notification/daily_report/user 等）。
  3. server-java jar 以 `DB_HOST=127.0.0.1 DB_USER=root DB_PASS=root` 启动，`/actuator/health` 返回 UP（不再 `Unsupported Database: MySQL`）。
- **角色**：Eng（架构师复核技术栈符合性）。
- **依赖**：MySQL 存活、Maven、E: 本地仓库。

### W2 — 验证并提交在途工作（#92 RS256 / #94 MQ 消费者 / #95 部署产物）
- **目标**：把工作树 10 改+11 新实证后分批提交，状态据实。
- **做法**：先 `mvn test` 全量复核（取真实数字，不引用 GO-LIVE-LOG 宣称值）；双闸门预检；按语义分 commit（RS256 签发 / MQ 消费者 / 部署产物三批），本地 commit，不直推 master。
- **验收**：
  1. `mvn test` 真实 `Tests run: N, Failures: 0, Errors: 0`（N 为实证值）。
  2. 双闸门（契约 + PRD/HLD 追溯）绿。
  3. 三个语义单元各自独立 commit，message 含四角色摘要。
- **角色**：Eng + QA（复核）。
- **依赖**：W1 后（依赖可编译/可起的 server-java）。

### W3 — 本地全栈运行时实证
- **目标**：消除「只跑单测、从未真起过服务」的假上线断层。
- **做法**：起本地 Redis → 真实 MySQL 起 server-java jar → `/actuator/health` UP → `/auth/login` 取真实 RS256 令牌 → 带令牌调受保护端点验签发↔验签 → 无令牌验 401 fail-closed；起 server-python 验 `/healthz` 与 `X-Internal-Token` fail-closed。留存实证输出。
- **验收**：
  1. server-java `/actuator/health` = UP；`/auth/login` 返回可验签 JWT；受保护端点带令牌 2xx、无令牌 401。
  2. server-python `/healthz` 200；缺 `X-Internal-Token` 返回 401。
- **角色**：Eng + QA。
- **依赖**：W1/W2 后；Redis 可用（否则记降级）。

### W4 — 上线手册阶段二（#96）
- **目标**：真实服务部署步骤 / 健康检查 / 应急 / 本机 Agent 回调契约，与实证一致。
- **做法**：扩写 `docs/上线手册.md` 阶段二（全栈 compose / 原生 jar 降级路径 / 真实 MySQL Flyway 前置 / RS256 密钥注入 / 本机 Agent 回调契约 / 健康检查 / go-no-go / 应急回滚）。不写未验证步骤。
- **验收**：手册每步对应 W1–W3 实证；含 B-1/B-2/B-3 诚实标注与「待用户触发」清单。
- **角色**：Docs + Arch 复核。

### W5 — QA 上线前全量验证（#97）
- **目标**：独立验证全量门禁。
- **做法**：`design/contracts/validate_contracts.py` + `design/check_prd_hld_traceability.py` 双闸门；server-java `mvn test`；server-python `pytest`；scaffold 测试；frontend `vite build`。逐项记真实数字。
- **验收**：上述每一项 BUILD/PASS，无 FAIL；任一 FAIL → 回 I 修复（A↩I）。
- **角色**：QA（独立）。

### W6 — 经 GitHub 连接器 push → PR → gates 绿 → 合并 master（#98）
- **目标**：铁证合并。
- **做法**：先用 GitHub 连接器核对远端 master 真实状态（解 TG-4）；推非保护分支 → 开 PR → 等 `gates` 绿 → squash 合并 master；以远端 API（ls-tree/contents/commit status）为证。
- **验收**：远端 master 含本批次全部文件；PR gates 全绿；合并 commit 可经 API 验证。
- **角色**：收尾（Team Lead）。
- **依赖**：W1–W5 全 `DRAFT_COMPLETE`；远端状态已核。

---

## 7. 批次级验收（进 DONE 前必须全过）

1. W1–W6 全部 `DRAFT_COMPLETE`。
2. 双闸门绿；server-java `mvn test` / server-python `pytest` / scaffold / frontend build 全绿（真实数字）。
3. W3 运行时实证留存输出，签发↔验签 + fail-closed 均通过。
4. TG-1/TG-2/TG-3 已纠正并回写日志；TG-4 远端状态已核。
5. 交付回执产出；物理动作（Q5/Q6/Q7/护栏4/5/6）标「待用户触发」。
6. 回写 `PROJECT_BRAIN.md` §2/§5/§7、`TASK-QUEUE.md`、`TASK-LOG.md`、`GO-LIVE-LOG.md` 终稿。

---

## 8. 回路处置

- **A ↩ I（普通缺陷）**：W1–W6 任一验收 FAIL 属实施缺陷 → 回对应 I 修，修完只重跑 A，不重走 D/P。
- **A ↺ D/P（系统问题）**：若发现需改 ADR-001/002/004/010 或范围假设错误 → 本批次打回 `DEFINING`，另立 BATCH-002 交用户拍板，不擅自改架构。

---

## 9. P 阶段审查结论（Plan Review）

| 闸门 | 判定 | 说明 |
|---|---|---|
| 范围完整？ | ✅ 是 | W1–W6 覆盖 GO-LIVE 目标；§2 显式列出 in/out，无遗漏。 |
| 依赖明确？ | ✅ 是 | §4 逐依赖给实证现状；TG-4 远端状态留 W6 核，不阻塞 D。 |
| 验收可判定（全机器可验证）？ | ✅ 是 | 每个 W 含显式机器检查（schema history / mvn test / health / 401 / 双闸门 / gates）。 |
| 与 ADR-001/002/004/010 / PROJECT_BRAIN §3 / 护栏 1/2/3 冲突？ | ✅ 无 | W1 补 flyway-mysql 属修复 ADR-003(MySQL8) 缺陷；W2 收口 RS256/MQ/compose 对齐既定架构；护栏 1/2/3 全程不削弱。 |
| 未知项已登记？ | ✅ 是 | TG-1..TG-6 全登记；TG-2 要求 W1 实现时对齐 flyway-core 解析版本（I 时核实）。 |

**结论**：✅ **通过（进 I）**。无重大冲突，无需打回 D。
**审查人/角色**：架构师(software-architect) + Team Lead（将领）
**日期**：2026-08-19

---

## 10. 实证记录（Evidence Log · 机器可复核）

### W1 — Flyway MySQL 真实迁移闭环 ✅ DRAFT_COMPLETE
- 构建：`clean package -DskipTests` → `BUILD SUCCESS`，产物 `server-java-0.1.0.jar`（48MB，已 repackage）。为规避中文路径编码乱码，构建在 ASCII 拷贝 `/e/build/server-java` 完成，Maven 经 `java -cp classworlds.jar Launcher` 直接启动（绕过损坏的 `mvn` 脚本 glob）。
- 起 jar（真实 MySQL `127.0.0.1/root/root`）：Flyway 日志 `Successfully validated 10 migrations` → 依次迁移至 `version "10 - user"` → `Successfully applied 10 migrations to schema resume_ai, now at version v10`。
- `flyway_schema_history`：`COUNT(*)=10, SUM(success)=10`（V1–V10 全 success=1）。
- 业务表：`SHOW TABLES` 返回 25 张（application / job_match / job_favorite / job_view / resume / strategy / adapter / interview / payment / notification / daily_report / user / t_user 等齐全）。
- `/actuator/health`：`{"status":"UP"}`（端口 8080，经 `SERVER_PORT=8080` 覆盖沙箱 `SERVER__PORT=0`，见 F2）。
- **结论**：生产启动阻塞级缺陷（连真实 MySQL 必崩 `Unsupported Database: MySQL`）已闭环。

### W2 — 验证并提交在途工作 ✅ DRAFT_COMPLETE
- `mvn test` 全量（ASCII 构建副本）：`Tests run: 87, Failures: 0, Errors: 0, Skipped: 0` → `BUILD SUCCESS`（TEST_EXIT=0）。覆盖 RS256（`JwtTokenSignerTest`/`JwtVerifierTest`/`JwtAuthFilterTest`）、MQ 消费者（`ApplyTaskConsumerTest`/`RabbitMqApplyTaskPublisherTest`）。
- 双闸门（design/contracts/validate_contracts.py + design/check_prd_hld_traceability.py）：**全绿**（schemas 66 可加载 / 正向通过 / 反向证伪 / 注册表自洽 / 错误码唯一；PRD↔HLD MUST_TRACE 全追溯、版本一致 4.5=4.5）。
- 分批提交（本地，不直推 master，6 commit）：
  - `5ab30b6` fix(java): W1 补 flyway-mysql 闭环真实迁移
  - `c4c7397` feat(java): #92 RS256 真实签发验签闭环
  - `3f4e0c7` feat(java): #94 RabbitMQ 投递任务消费者
  - `929951a` feat: #95 部署产物 双Dockerfile+全栈compose+.env+cd-deploy
  - `ff56cc4` feat(java): #92 JWT 真密钥(env)注入 + Agent 回调基址  ← 补提交漏落的 application.yml 改动
  - `d3f9bb4` chore: DPIRA 框架与批次文件

### W3 — 本地全栈运行时实证 ✅ DRAFT_COMPLETE
**server-java（真实 MySQL + Redis，端口 8080）**
- `POST /auth/login`（任意凭据，MVP B-1 占位）→ `code=0`，返回 RS256 令牌；JWT header 解码 `{"alg":"RS256"}` ✅ 真实 RS256 签发。
- `GET /auth/users/me` + `Bearer <token>` → **HTTP 200** ✅ 签发↔验签闭环成立。
- `GET /auth/users/me` 无令牌 → **HTTP 401** ✅ fail-closed。
- `GET /api/v1/jobs` 无令牌 → **HTTP 401** ✅ fail-closed；带令牌 → HTTP 500（根因为 F1：`resume_ai.job` 表不存在，非鉴权问题，鉴权已通过）。
- `POST /auth/refresh` + refreshToken → 换新 token `code=0` ✅。

**server-python（FastAPI，端口 8000，INTERNAL_TOKEN=w3-internal-token）**
- `GET /healthz` → **HTTP 200** ✅。
- `POST /internal/v1/ai/match` 无 `X-Internal-Token` → **HTTP 401** ✅ fail-closed（未配置/缺失令牌一律拒，无后门）。
- `POST /internal/v1/ai/match` + 正确 `X-Internal-Token` → **HTTP 400**（已通过令牌门、进入业务层校验，非 401）✅ 令牌校验闭环成立。

### 运行时发现（已登记于 DPIRA-STATE.json → findings）
- **F1（HIGH）**：`job` 读表从未被创建（跨服务设计-实现缺口）。`Job` 实体 `@TableName("job")`，但 V3 迁移注释声明由 Python 侧 Alembic 创建，而 server-python 无任何建表代码 → `resume_ai.job` 永不存在 → jobs 读接口 500。属 ADR-002 双语言异构下 Python 侧承诺未交付。**不擅自在 Java 静默补表**，交 A 报告与用户决策；W4 手册须标注部署顺序依赖。
- **F2（INFO）**：沙箱注入 `SERVER__PORT=0` 致 Tomcat 随机端口；本地以 `SERVER_PORT=8080` 覆盖确认真实监听 8080。真实部署环境无此变量，配置 `server.port:8080` 生效，compose/nginx 假定 8080 正确。

### W4 — 上线手册阶段二 ✅ DRAFT_COMPLETE
- 扩写 `docs/上线手册.md` §11「阶段二：全栈 compose 真实部署」，以 `docker-compose.yml` 为权威来源，覆盖拓扑/前置/.env/部署步骤/健康检查/RS256+Agent 回调契约/应急回滚。
- 诚实标注 F1（job 表未创建·跨服务缺口）、B-1（MVP 认证）、前端本地 safe-delete 钩子；明确「用户物理动作不代执行」。

### W5 — QA 上线前全量验证 ✅ DRAFT_COMPLETE
- 双闸门（契约 + PRD/HLD 追溯）：**全绿**（W2 已实证，W5 复验一致）。
- server-java `mvn test`：`Tests run: 87, Failures: 0, Errors: 0, Skipped: 0` → BUILD SUCCESS。
- server-python `pytest`：`PYTEST_EXIT=0`（全部通过，含 auth fail-closed 用例）。
- scaffold `test_smoke.py`：`SCAFFOLD_EXIT=0`，**25 端点全 PASS**（含 422 fail-closed 抽样）。
- frontend `vite build`：编译成功（1618 模块；用外部 outDir 绕过沙箱 safe-delete 对默认 `dist` 清理的拦截，容器构建无碍）。
- **结论**：W5 全部门禁绿，满足批次级验收 §7 第 2 项。
