# GO-LIVE-LOG · 从「GOAL REACHED 文档」到「产品可上线」

> 多角色署名工程日志（SoftwareCompany：PM / Arch / Eng / QA）
> 起始：2026-08-19 晚（续 B 路线 PR#5 合并 master=dc03b3f 之后）
> 驱动方式：用户全权委托（R1 自驱；「直接用 github 连接器不提醒」；「继续推进直到产品上线」）
> 目标：把产品从「设计/契约/服务端代码已交付、但部署产物只跑了 Python 契约桩」推进到**真正可部署、可运维、代码缺口闭环**的生产就绪状态，并持续记录每一步的「做了什么 / 怎么做 / 思路 / 为什么」。

---

## 0. 前言：本日志写给谁、要解决什么

用户原话：「继续推进直到，产品上线，过程中落地文档日志（说明并是怎么做的？你的思路方式，为什么这样做）」。

所以本日志不是流水账，而是**工程决策的透明记录**：每一个动作都回答四问——**做了什么（What）、怎么做（How）、思路/方法（Thinking）、为什么这样做（Why）**。它同时是给用户的「可审计交付物」：用户是 Java 工程师，会逐行质疑架构与安全，因此所有高风险决策都显式登记，不隐藏。

---

## 1. PM（产品/范围）：「上线」到底指什么、验收标准、路线图

### 1.1 What —— 重新定义「上线」
本项目 `PROJECT_BRAIN.md` 的 `/goal` 早已声明：「做出来 = 交付**生产就绪**的设计文档 + 可构建/过门禁/带测试的系统代码（**非**『已在跑真人数据的线上系统』）」。也就是说，项目的成功定义本身就是「生产就绪（production-ready）」，而不是「已经用真实用户数据跑起来」。

但此前的交付有一个**真实断层**：`Dockerfile` / `docker-compose.yml` / `cd-deploy.sh` 只把 **Python 契约桩（scaffold/src/server_main.py）** 打成了容器，真正的业务后端 `server-java`（Spring Boot）和 `server-python`（FastAPI）**完全没有进镜像、没有进编排**。换言之，文档说「GOAL REACHED」，但「上线」这一步实际只完成了 10%。

因此本次「产品上线」= **把真实业务服务做成可部署、可运维、门禁全绿的生产就绪交付**，而不是去按生产环境的「上线开关」（那是用户的物理动作，见 1.3 硬边界）。

### 1.2 How —— 验收标准（可机器验证）
1. **代码缺口闭环**：
   - C 阶段：`/auth/login` 的 **mock token** 替换为 **真实 RS256 签发**（验签器 JwtVerifier 早已就绪，只差签发侧）。
   - A 阶段：Flyway **MySQL 迁移**在真实 MySQL 可落地（依赖已具备，需验证脚本 + 文档）。
   - Task #65 余下：RabbitMQ **消费者侧**（rabbit 模式监听 `apply.task.queue` 并派发本机 Agent）。
2. **真实服务可部署**：新增 `server-java` / `server-python` 的 Dockerfile（多阶段、非 root），扩展 `docker-compose.yml` 编排全栈（java + python + mysql + redis + rabbitmq + 前端静态），`.env.example` 覆盖全部配置，`cd-deploy.sh` 增加真实服务打包且保持 `DEPLOY_TOKEN` 门控。
3. **门禁全绿**：server-java `mvn test` 全绿（≥80）、server-python `pytest` 全绿、双闸门（pre-commit 契约 + PRD/HLD 追溯）绿。
4. **运行手册**：`docs/上线手册.md` 阶段二覆盖真实服务部署步骤、健康检查、监控、红线、应急、本机 Agent 接入。
5. **铁证合并**：经 GitHub 连接器 push → PR → gates 绿 → squash 合并 master（以 `git ls-tree`/contents API 为证，不看本地工作树）。

### 1.3 Why —— 边界（诚实，不伪造）
- **硬边界（用户独有动作，循环不代做、不伪造）**：提供真实凭据 / 真实部署 / 点击生产上线开关 / 处理真实用户 PII；上线前 PIPL 法定签署（D 阶段被用户 2026-08-17 拍板跳过）。这些在最终报告标「**待用户触发**」。
- **为什么这样定义**：项目自身 `/goal` 把成功定为「生产就绪代码」，且记忆中的硬边界明确「物理动作/PIPL 签署仅用户可做」。我若去「真部署生产」既越权又有事故风险（真实凭据、平台账号封禁）。因此「上线」的终点 = 生产就绪 + 运行手册 + 门禁绿 + 标待用户触发，这是**在不越权前提下能交付的最大价值**。

### 1.4 路线图（任务 #90–#98）
| # | 角色 | 内容 | 状态 |
|---|------|------|------|
| 90 | PM | 上线验收标准与路线图（本節） | ✅ 已完成 |
| 91 | Arch | 上线架构与部署拓扑 + 偏差登记 | ✅ 已完成 |
| 92 | Eng | RS256 真实签发替换 mock | ✅ 已完成 |
| 93 | Eng | Flyway MySQL 生产迁移可用性验证 | ✅ 已完成 |
| 94 | Eng | RabbitMQ 消费者派发本机 Agent | ✅ 已完成 |
| 95 | Ops/Eng | 真实服务部署产物（Docker/compose/.env/cd） | ✅ 已完成 |
| 96 | Docs | 上线运行手册阶段二 | 待做 |
| 97 | QA | 上线前全量验证 | 待做 |
| 98 | 收尾 | 合并 master + 日志终稿 + 标待用户触发 | 待做 |

---

## 2. Arch（架构师）：上线部署拓扑与关键决策

### 2.1 What —— 目标拓扑
```
[浏览器/前端静态] ──HTTPS──> [server-java :8080]  (Spring Boot 业务后端: 用户/投递/简历/面试/支付/通知/状态机)
                              │  REST (AI 匹配/面试模拟)
                              ▼
                         [server-python :8xxx] (FastAPI: LLM 编排 + 护栏1/2/3)
                              │  AMQP
                              ▼
                    [RabbitMQ] ──apply.task.queue──> [消费者] ──HTTP──> [本机 Agent](用户机器·浏览器自动化·持 Cookie)
                              │
        [MySQL] (业务库, Flyway 建表)   [Redis] (幂等/缓存/session)
```
- 前端：Vite 构建后由 nginx 或静态服务托管（compose 中可作独立 service 或挂 volume）。
- 本机 Agent：**不在服务端容器里**。它是用户机器上的独立客户端，服务端只通过 HTTP 回调派发任务；Cookie/平台账号凭据**始终在用户本机**，服务端不持有（对齐 HLD §3.4.1 C2 任务通道红线）。

### 2.2 How & Why —— 关键决策与理由
- **决策 D-1：多容器 docker-compose，不用 K8s。**
  - Why：PROJECT_BRAIN §4 运维取舍已定「K8s 现阶段不要——扩缩容难点在本地客户端不在服务器；K8s 误配是头号宕机源，对非专家是事故风险」。我作为架构师**沿用该已拍板决策**（R4 行业标准/已采纳决策优先），不擅自升级编排复杂度。
  - How：单个 `docker-compose.yml` 编排 java/python/mysql/redis/rabbitmq，依赖顺序 + 健康检查 + `restart: unless-stopped`。
- **决策 D-2：server-java 多阶段 Dockerfile（Maven 构建 → 运行 jar，非 root）。**
  - Why：CI 里已验证 `mvn test` 可离线跑通；镜像应只包含运行时（JRE + jar），减小攻击面、符合最小权限。
  - How：build 阶段用 `maven:3.9-eclipse-temurin-17` 构建 jar；runtime 阶段用 `eclipse-temurin:17-jre` + `useradd` 非 root 运行。
- **决策 D-3：RS256 密钥「缺省生成临时密钥对、生产注入 PEM」。**
  - Why：开发/测试零配置可起（生成临时 RSA-2048）；生产经 `.env` 挂载私钥/公钥 PEM，私钥**不入库、不进镜像**（红线）。验签器 JwtVerifier 已有 fail-closed（无公钥即拒绝一切），本决策与之对齐。
  - How：新增 `RsaKeyProvider`（`@Component`）：若 `resumeai.jwt.private-key`/`public-key`（PEM）均配置→加载；均缺→生成临时密钥对并**明确 WARN 日志**（dev 模式，不安全）。签发器与验签器共用同一 Provider 的密钥。
- **决策 D-4：消费者派发本机 Agent 走「配置化 HTTP 回调」，不把浏览器自动化塞进服务端。**
  - Why：产品本质是「重客户端（本地浏览器自动化）+ 轻量服务端」。服务端持 Cookie 会同时违反平台反爬红线与 PIPL（凭据集中）。保持服务端无凭据是核心安全约束。
  - How：消费者 `@RabbitListener` 监听 `apply.task.queue`，按 `ApplyTaskMessage` 调用配置的「本机 Agent 回调 base URL」（如 `http://localhost:9xxx/task`），幂等键 `idempotencyKey+taskId` 经 Redis 去重，失败进 DLQ。该回调契约（请求/响应）写入运行手册，本机 Agent 侧联调属待办（诚实标注）。

### 2.3 登记的偏差（显式，不隐藏）
- **B-1**：用户store（`UserServiceImpl`）当前为内存 mock，未接 `t_user` 持久层。本次 #92 把令牌换成真实 RS256，但**凭据校验仍是 MVP 简化**（接受非空 account/credential 即签发；不做密码哈希/注册流程）。理由：完整用户注册+密码哈希+DB 校验是一个独立子域，且牵涉 PIPL（D 阶段已跳过）。**诚实标注为 MVP 限制，非生产级认证**，列待办。
- **B-2**：本机 Agent 回调契约已定义，但服务端→本机 Agent 的端到端联调未做（需用户机器上的客户端配合），标「待联调」。
- **B-3**：RabbitMQ 若用户选择 `memory` 模式（开发/测试），消费者不启用，任务不真正下发——这是预期行为，非缺陷。

> 下一步：以 #92 为第一刀，先把「mock token → 真实 RS256」这一最显眼的「假上线」点消除，再补部署产物。每完成一批，回到本日志追加 Eng/QA 章节。

---

## 3. Eng（工程师）· 批次一：RS256 真实签发（#92）

### 3.1 What —— 消除「mock token」
`UserServiceImpl.login` 原先返回 `"mock-" + account`，是纯占位，根本不是认证。本批次把它替换为**真实 RS256 JWT 签发**，使 `/auth/login` 产出的 access/refresh 令牌可被已有的 fail-closed `JwtVerifier` 验签——前后端才真正形成「签发↔验签」闭环。

### 3.2 How —— 改动清单
- **新增 `security/RsaKeyProvider`**：密钥源。生产经 `.env` 注入 `resumeai.jwt.private-key`/`public-key`(PEM) 加载固定密钥对；两者均缺→生成**临时 RSA-2048** 供开发零配置启动，并 WARN 日志（重启失效）。只配其一→启动即失败（避免半吊子安全）。
- **新增 `security/JwtTokenSigner`**：用私钥签 RS256，claims=`sub/iss/plan/role/type`，access/refresh 仅 TTL 与 type 不同。
- **改 `security/JwtVerifier`**：保留原 `(JwtProperties)` 构造（兼容 9 处既有单测零改动），**新增运行时构造 `(PublicKey, issuer)`**；去掉 `@Component`，改由 `SecurityConfig` 以 `@Bean` 注入（与签发器共用 `RsaKeyProvider` 的同一密钥对，保证自签自验）。
- **改 `security/SecurityConfig`**：`@Value` 读私钥 PEM；新增 `rsaKeyProvider`/`jwtVerifier`/`jwtTokenSigner` 三个 `@Bean`。
- **改 `module/user/UserServiceImpl`**：构造注入 `signer`+`verifier`；`login` 签发真实 JWT；`refresh` 先验签 refresh 令牌再重签；`me` 直接使用已由过滤器验签得到的 `sub`。
- **改 `application.yml`**：补 `private-key`/`public-key`（默认空→临时密钥）。
- **测试**：`UserServiceTest` 改为用临时密钥做「自签自验」断言（不再是 mock）；新增 `JwtTokenSignerTest`（claims/issuer 一致性）。

### 3.3 Thinking / Why —— 思路与理由
- **为什么用密钥源共用而非两处各读配置**：签发与验签必须用同一密钥对，否则自签自验必败。集中到 `RsaKeyProvider` 单一真相源，消除「配置漂移导致验签失败」这类隐蔽 bug。
- **为什么保留 `JwtVerifier(JwtProperties)` 旧构造**：9 处既有单测靠它，全部改为新构造是噪音且无收益；运行时走新构造即可。这是「不为了整洁破坏已绿测试」的取舍。
- **为什么 MVP 凭据校验仍是「非空即签发」（偏差 B-1）**：完整用户注册 + 密码哈希 + 查 `t_user` 是独立子域，且牵涉 PIPL（D 阶段被用户 2026-08-17 跳过）。若在此伪造「已做密码校验」是隐瞒风险；故显式标注为 MVP 限制，列待办。**绝不把占位当生产认证**。
- **为什么缺省生成临时密钥而非报错**：开发/测试要能零配置 `mvn test` 与本地起服务；但生产若不留 PEM，重启后所有令牌失效——用 WARN 日志把这条隐性风险**显式喊出来**，而非静默。

### 3.4 QA 结果
- 离线 `mvn test`：**84/0/0 BUILD SUCCESS**（原 80 + 新增 JwtTokenSignerTest 3 + UserServiceTest 由 3 扩到 4，并修 1 处测试断言：验签器对 issuer 不匹配抛 `AuthException` 而非裸 `JwtException`）。
- 双闸门 pre-commit：待提交时校验（见 #97）。

---

## 4. Eng（工程师）· 批次二：Flyway MySQL 生产迁移可用性（#93）

### 4.1 What
确认 server-java 在**真实 MySQL** 上能通过 Flyway 自动建库（V1–V10，含 V10 补齐的 `t_user`），使「上线」无需手工建表。

### 4.2 How / 核查结论
- `pom.xml` 已含 `mysql-connector-j` + `flyway-core`（依赖就位，无需新增）。
- 主迁移位于 `src/main/resources/db/migration/`：`V1`–`V9`（业务表）+ `V10__user.sql`（MySQL 语法 `ENGINE=InnoDB utf8mb4_0900_ai_ci`，补齐此前漏建的 `t_user`）。生产 profile 走默认 `classpath:db/migration` → 应用 V1–V10。
- 测试 profile 在 `src/test/resources/application.yml` 覆盖 `flyway.locations: classpath:db/migration-test`（仅 `V11__user.sql`/H2），供 `UserServiceTest` 真落库；其余 80 个测试 mock Mapper，不触 DB——这是既有的有效测试策略，非缺陷。
- **真实 MySQL 迁移已在 W1 批次实证（非 PR#4）**：W1 在真实 MySQL（root/root）启动 jar，Flyway 应用 V1–V10 全部 `success=1`、建成 25 张业务表、`/actuator/health` 返回 UP。旧版 GO-LIVE-LOG 称「PR#4 已验证」属不实声明，已在此纠正（详见 DPIRA-BATCH-001 / 上线手册 §11）。

### 4.3 Why
- **为什么 V10 用 MySQL 专用语法、V11 用 H2**：生产库是 MySQL，必须用 MySQL DDL；测试用 H2 `MODE=MySQL` 兼容大部分语法但仍单列 V11 以隔离。两路分离避免「一套 SQL 在两个库都勉强跑但语义漂移」。
- **为什么不新增 `flyway-mysql` 依赖**：基础 schema 迁移 `flyway-core`+`mysql-connector-j` 已足够；`flyway-mysql` 仅提供 MySQL 专属回调等高级特性，当前用不到，引入即增加攻击面与维护成本（R4 标准优先、最小必要）。

### 4.4 QA / 验证命令（交运维/用户执行）
```bash
# 在生产 MySQL 就绪后，从 application.yml 注入数据源，启动即自动迁移：
DB_HOST=127.0.0.1 DB_USER=root DB_PASS=root java -jar server-java.jar
# 或单独校验迁移（不启动业务）：
mvn -q -DskipTests flyway:migrate
# 期望：Schema history 表记录 V1..V10 全部 success。
```
- 诚实标注：本批次**已在真实 MySQL 实证（非「本次未复测」）**：V1–V10 全 `success`、`resume_ai` 库 25 表就绪、health UP。旧版「PR#4 已验证 / 本次未复测」表述已纠正为 W1 实证结论。

---

## 5. Eng（工程师）· 批次三：RabbitMQ 消费者派发本机 Agent（#94，闭环 Task #65）

### 5.1 What —— 把「只发不收」的异步链路接成闭环
B 路线（PR#5，`dc03b3f`）只落地了**发布器** `RabbitMqApplyTaskPublisher`——它负责把 `ApplyTaskMessage` 投到 `apply.task.queue`，但**队列那头没有任何消费者**。消息发出去无人处理，整个「AI 匹配 → 用户确认 → 异步派发投递任务」链路在 RabbitMQ 这一环是断的。本批次补上消费端 `ApplyTaskConsumer`，让消息被真正消费并派发到用户机器上的本机 Agent，异步投递链路才完整。

### 5.2 How —— 改动清单
- **新增 `module/application/event/ApplyTaskConsumer.java`**：
  - `@Component @ConditionalOnProperty(name="resumeai.mq.mode", havingValue="rabbit")`——**仅 rabbit 模式监听**；memory 模式不启用（对齐偏差 B-3，避免无 broker 时报错）。
  - 构造注入 `StringRedisTemplate` + `RestTemplate` + `@Value("${resumeai.agent.callback-base-url:http://localhost:9800}")`。
  - `@RabbitListener(queues = ApplyTaskPublisherConfig.QUEUE)` 监听同一队列（与发布器共用队列常量，单一真相源）。
  - **幂等去重**：键 `apply-task:idem:{idempotencyKey}:{taskId}`，命中即 `return`（跳过重复投递）；派发成功后 `redis.opsForValue().set(...,"1")` + `redis.expire(...,86400,SECONDS)`（24h TTL）。
  - **派发**：`rest.postForEntity(callbackBaseUrl + "/tasks", msg, String.class)`；非 2xx → 抛 `IllegalStateException`；任何异常 → 原样 `throw`，由 RabbitMQ 按 `apply.dlx` 路由到 DLQ 重试。
- **改 `config/ApplyTaskPublisherConfig`**：新增**无条件** `@Bean RestTemplate`（发布器与消费者共用 HTTP 客户端，避免重复定义）。
- **改 `application.yml`**：补 `resumeai.agent.callback-base-url`（默认 `http://localhost:9800`）；确认 `resumeai.mq.mode` 已存在。
- **新增 `ApplyTaskConsumerTest`**：Mockito `@ExtendWith(MockitoExtension.class)`，`@Mock redis/valueOps/rest`；3 用例：
  1. `dispatches_to_local_agent_and_records_idempotency`——派发成功并记幂等键；
  2. `skips_when_idempotency_key_present`——幂等键存在则跳过、不调 rest；
  3. `dispatch_failure_throws_to_route_dlq`——rest 抛异常时监听器抛异常（触发 DLQ）。

### 5.3 Thinking / Why —— 思路与理由
- **为什么消费者派发到「本机 Agent」而非服务端自己做浏览器自动化（决策 D-4 / 偏差 B-2）**：本产品本质是「重客户端（本地浏览器自动化）+ 轻量服务端」。Cookie / 平台账号凭据**绝不能集中在服务端**——既违反平台反爬红线，也触碰 PIPL（凭据集中）。服务端只持有「派发通道」，`callback-base-url` 指向用户机器上的客户端，凭据始终在用户本机。这是核心安全约束，不是偷懒。
- **为什么幂等键用 `idempotencyKey + taskId`**：发布器侧已按 ADR-004 在消息体写入 `idempotencyKey`（最小必要字段）。RabbitMQ 是「至少一次投递」语义，网络抖动/重投/DLQ 重试都可能让同一消息被消费多次。若不去重，重复消费 = 重复派发本机 Agent = 重复向招聘平台投递 = **封号风险**。以幂等键去重是把「不全面之处」管理起来（用户多次强调的生产事故来源），而非假装不会出现。
- **为什么派发失败抛异常而非 `try-catch` 吞掉**：RabbitMQ 的 DLQ/重试机制**靠监听器抛异常触发**——`@RabbitListener` 抛异常才会被 broker 捕获并按 DLX 路由到死信队列重试。若吞掉异常，失败任务静默丢失，既无重试也无可观测，是「假装成功」式隐瞒。这与本项目贯穿的 fail-closed 思路一致：**异常外显，不掩盖**。
- **为什么 memory 模式不启用消费者（B-3）**：memory 模式是开发/单测用的同步桩（InMemory），消息根本不进 RabbitMQ，自然无需异步消费者；强制启用会因无队列/无 broker 而启动失败。这是预期行为，已在 Arch 偏差表登记。
- **为什么 `RestTemplate` Bean 放发布器配置类**：发布器与消费者都依赖一个 HTTP 客户端，放 `ApplyTaskPublisherConfig` 共用，避免两处各 new 一个（难统一超时/拦截器）。属「共享依赖单一配置点」。

### 5.4 QA / 踩坑与结果
- **编译期坑（关键）**：初写测试 `verify(valueOps).expire(anyString(), eq(86_400L), eq(SECONDS))` 编译失败——`ValueOperations` 接口**没有** `expire(K,long,TimeUnit)` 方法；`expire` 只在 `StringRedisTemplate.expire(K,long,TimeUnit)` 上存在。主代码 `redis.expire(...)` 是对的，测试验证对象搞错了。修正为 `verify(redis).expire(...)` 后编译通过。
- **严格桩坑**：`setUp` 中 `when(redis.opsForValue()).thenReturn(valueOps)` 在 skip/failure 用例里不会被调用（提前 return / 抛异常），Mockito 严格桩报 `UnnecessaryStubbing`。用 `lenient()` 标注该 stub 解决——这是「跨用例共享 stub 但部分用例用不到」的标准处理，不是掩盖问题。
- **离线 `mvn test`：87/0/0 BUILD SUCCESS**（原 84 + 新增 `ApplyTaskConsumerTest` 3 用例）。全量绿，无失败无错误。

### 5.5 当前诚实遗留（仍有效，F1 已闭合见上）
- **B-1**：`UserServiceImpl` 凭据校验仍为 MVP 简化（非空即签发，非密码哈希/注册流程）。已真实 RS256 签发，但**认证强度未达生产级**，待独立用户子域 + PIPL 后补齐。
- **B-2**：服务端 → 本机 Agent 的端到端联调未做（需用户机器上的客户端配合定义 `/tasks` 契约）。服务端侧契约已定义，联调属待办，标「待联调」。
- **B-3**：memory 模式消费者不启用，预期行为。
- **B-4（HIGH·真实缺陷·F1）— ✅ 已闭合（2026-08-20）**：`Job` 实体 `@TableName("job")`，`job` 读表此前从未被创建（V3__jobs.sql 注释甩给 Python Alembic，但 server-python 无建表代码），致 `GET /api/v1/jobs` 必 500。**决策（R1 自主拍板）**：server-python 从未交付 Alembic 建表路径，而本仓库 25 张业务表均由 server-java Flyway 拥有，故由 server-java 新增 `V11__job.sql` 显式建 `job` 表（与 job_match/job_view/job_favorite 同库、类型对齐 BIGINT UNSIGNED；不改动已跑过的 V3 以避校验和冲突）。**实跑验证**：MySQL 灌库建表成功；重建 jar 启动后 Flyway 补登 v11(success=1)；`POST /auth/login`→200 签发 RS256；`GET /api/v1/jobs?page=1&pageSize=10`→**200** `{"items":[],"total":0}`（不再 500）。详见 `DPIRA-BATCH-001` F1 与 `上线手册.md` §11。

---

## 6. Ops/Eng（运维/工程师）· 部署产物：真实服务进镜像与编排（#95）

### 6.1 What —— 把「只跑 Python 契约桩」的部署升级为「全栈真实服务」
原部署产物（O 阶段）的 `docker-compose.yml` 只 build 根 `Dockerfile`（= `scaffold/src/server_main.py` 契约桩），`server-java` 与 `server-python` 完全不在镜像/编排里——所谓「上线」只完成了契约桩一层。本次补齐：
- 新增 `server-java/Dockerfile`（多阶段，非 root）：maven 构建 → 运行 `server-java-0.1.0.jar`。
- 确认 `server-python/Dockerfile` 已就绪（非 root，构建 `app.main:app`，且必须保留 `design/` + `server-python/` 兄弟目录布局）。
- 重写 `docker-compose.yml`：编排 `mysql + redis + rabbitmq + server-java + server-python + frontend`（6 服务 + 3 数据卷）。
- 重写 `.env.example`：覆盖全部 6 服务的配置键（DB/Redis/RabbitMQ/JWT/本机Agent回调/LLM网关/护栏阈值/前端API基址）。
- 更新 `scripts/cd-deploy.sh`：新增 server-java fat-jar 构建 + server-python 打包，保持 `DEPLOY_TOKEN` 门控（不真部署）。
- 新增 `frontend/Dockerfile` + `frontend/nginx.conf`（node 构建 → nginx 静态托管 + `/api` 反代 server-java）+ 各自 `.dockerignore`。

### 6.2 How —— 关键设计
- **拓扑**：`前端(nginx:5173) --/api--> server-java(:8080) --REST--> server-python(:8000) ↘ MySQL/Redis/RabbitMQ`。对齐 Arch §2.1 目标拓扑（决策 D-1：多容器 compose，不用 K8s）。
- **依赖顺序 + 健康门控**：`server-java` `depends_on` mysql/redis/rabbitmq 的 `service_healthy`（杜绝「库没起就连接」的启动竞态）；各服务均配 `healthcheck`（`/actuator/health`、`/healthz`、mysqladmin ping、redis-cli ping、rabbitmq-diagnostics）。
- **最小权限**：server-java runtime 用 `eclipse-temurin:17-jre` + `useradd -u 10001 appuser`；server-python 已有 `appuser`；frontend 用 nginx 默认非 root。无服务以 root 运行。
- **密钥红线**：`RESIMEAI_JWT_PRIVATE_KEY/PUBLIC_KEY`、`INTERNAL_TOKEN`、`LLM_API_KEY` 仅经 `.env` 注入，**不进镜像、不入库**（`.dockerignore` 已排除 `.env`；compose 用 `${VAR}` 引用）。私钥缺失 → server-java 启动生成临时 RSA-2048 并 WARN（开发态），生产必须注入 PEM。
- **本机 Agent 回调**：`AGENT_CALLBACK_BASE_URL` 默认 `http://host.docker.internal:9800`；server-java 容器加 `extra_hosts: host.docker.internal:host-gateway`（Linux Docker Engine 解析宿主），使服务端能回调用户机器的本机 Agent。服务端始终不持 Cookie/凭据（对齐 D-4/B-2）。
- **RabbitMQ 模式**：`MQ_MODE=rabbit` + `MQ_RABBIT_HEALTH=true`（compose 默认）。开启后消费者启用、broker 探活生效；`memory` 模式则为开发同步桩（消费者不启用，预期）。

### 6.3 Thinking / Why
- **为什么重写而非新增 compose**：原 compose 只描述「契约桩单容器」，与「真实服务」目标自相矛盾；保留它会让部署产物继续「假装上线」。重写为全栈编排，是消除「假上线」的必须一步（与 #92 消除 mock token 同一思路：把占位换成真实）。
- **为什么 server-java 镜像构建跳过测试（`-DskipTests`）**：单测/集成测试已在 CI gates 全绿验证（本次 87/0/0）。镜像只负责「可运行产物」；在镜像内重跑测试既慢，又易因构建环境缺 DB 而失败。测试职责在 CI，不在镜像——这是关注点分离：CI 验正确性，镜像验可运行。
- **为什么 healthcheck 各取所需**：java 的 `eclipse-temurin:17-jre` 默认无 curl/wget → 显式 `apt-get install curl`（构建后清 apt 缓存，不增常驻体积）；python slim 自带 python → `urllib` 一行探针；nginx-alpine 自带 busybox `wget`。按「最小必要安装」原则，不统一装重。
- **为什么前端用 nginx 反代 `/api` 而非 CORS**：同源部署（前端 5173 经 nginx 同一入口对外）避免浏览器跨域与令牌暴露面；前端只调相对 `/api`，nginx 转发到 server-java，后端地址不暴露给客户端。
- **为什么 `host.docker.internal` + `host-gateway`**：服务端在容器内、本机 Agent 在用户宿主机器，跨网络回调用宿主网关地址；Linux Docker 默认不解析 `host.docker.internal`，需 `extra_hosts` 显式映射。这是「服务端不持凭据、只回调用户机器」架构的部署落地细节。

### 6.4 QA / 诚实声明
- **compose YAML 已通过 Python yaml 解析校验**（6 服务 + 3 卷，结构合法）。
- **未执行 `docker compose build` / `docker compose up`**：沙箱无 docker daemon，且镜像构建需拉取 `maven:3.9`/`node:20`/`mysql` 等基础镜像（离线不可达）。故「镜像能否成功构建、compose 能否拉起全栈」**未在本环境实证**——列为「待用户在具备 Docker 的环境验证」。这是诚实边界，不伪造「已部署」。
- 各服务 env 键已与源码逐一核对一致（server-java `application.yml` / server-python `config.py`），避免「compose 注入变量名与代码读取不一致」这类隐蔽错位。
- 偏差延续：B-1（MVP 认证）、B-2（本机 Agent 端到端联调）仍有效，不因部署产物而消除。
