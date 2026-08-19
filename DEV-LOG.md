# DEV-LOG · B 路线：事件发布器 RabbitMQ 化（ADR-004 发布侧）

> 多角色署名交付物（SoftwareCompany 工作流：PM / Arch / Eng / QA 各司其职）
> 日期：2026-08-19
> 分支：`java-business-p0` → 目标 `master`
> 关联：ADR-004（消息队列选型 RabbitMQ）、HLD §3.4.1 C2 任务通道、Task #65（event/ 包，部分）

---

## 一、PM（产品/范围界定）· 范围与验收
- **目标**：将 P0 骨架中的 `InMemoryApplyTaskPublisher` 桩，升级为 ADR-004 规定的 RabbitMQ 生产级发布器，同时保持开发/测试环境零 broker 依赖。
- **范围边界（显式）**：
  - ✅ 本迭代只做**发布侧**：RabbitMQ 拓扑声明（DirectExchange + DLX + 持久队列 + DLQ + 绑定）、JSON 消息体、条件化 Bean 切换、单测。
  - ⏸️ **不在本迭代**：消费端、延迟执行（TTL+DLX 实际消费者）、Redis 幂等去重——这些属 P1/event/ 包职责（Task #65），诚实标注为待补，不伪造完成。
- **验收标准**：
  1. 默认 `memory` 模式：行为与原桩一致，不依赖 broker，全量单测不破。
  2. `rabbit` 模式：经 `apply.direct` 下发 `apply.task.queue`，消息 JSON 化、带 `trace_id`、队列配死信。
  3. 新增发布器单测通过；全量 `mvn test` 绿灯。

## 二、Arch（架构师）· 设计符合性审查
- **结论：符合 ADR-004 / HLD，可进入实现。** 审查要点：
  - 消息体 `ApplyTaskMessage`（Java 17 record）仅含业务最小必要字段（taskId/applicationId/platformId/jobId/idempotencyKey/resumeVersionId/traceId），**不含 Cookie**——Cookie 由本机 Agent 本地加载，符合 HLD §3.4.1 C2 任务通道红线。✅
  - 拓扑与 ADR-004 一致：`apply.direct`(Direct) + `apply.dlx`(DLX) + `apply.task.queue`(持久, x-dead-letter-exchange=apply.dlx) + `apply.task.dlq` + 两处绑定。✅
  - 通过 `resumeai.mq.mode`（`memory`/`rabbit`）条件化装配，默认 `memory` 不创建 broker 相关 Bean，符合「开发/测试零依赖」约束。✅
  - `management.health.rabbit.enabled` 默认 `false`，避免无 broker 时 `/health` 误报 DOWN（属预期，非故障）。✅
- **登记的设计偏差（诚实标注，非遗漏）**：
  - 偏差 D1：延迟执行与消费端幂等未在本迭代落地，属 P1 职责（Task #65），需在 event/ 包补齐消费者与 TTL+DLX 实际消费逻辑。
  - 偏差 D2：发布侧 `trace_id` 取自 MDC，若上游未注入则退化为 UUID——链路追踪完整性依赖入口侧 MDC 植入，需在接入层确认。
- **偏离上报**：无。未偏离已采纳架构决策（ADR-001 双语言 / ADR-002 MyBatis-Plus / ADR-004 RabbitMQ）。

## 三、Eng（工程师）· 实现要点
新增 / 修改文件（6 个）：
1. `module/application/event/ApplyTaskMessage.java`（NEW）：消息体 record，Javadoc 标注 ADR-004 最小必要字段 + 不含 Cookie。
2. `module/application/event/RabbitMqApplyTaskPublisher.java`（NEW）：`implements ApplyTaskPublisher`；构造注入 `RabbitTemplate`+exchange+routingKey；`publish()` 生成 `taskId=UUID`、`traceId=MDC.get("traceId")` 或 UUID，组装消息并 `convertAndSend`；Javadoc 诚实标注延迟/消费幂等属 P1。
3. `config/ApplyTaskPublisherConfig.java`（NEW）：`@Configuration` 条件化 Bean——`rabbitMqApplyTaskPublisher`(mode=rabbit)、`inMemoryApplyTaskPublisher`(mode=memory, matchIfMissing=true)、JSON 转换器、交换机/队列/死信/绑定（均 `@ConditionalOnProperty mode=rabbit`）；常量集中定义。
4. `module/application/InMemoryApplyTaskPublisher.java`（EDIT）：移除 `@Component` 与 `import org.springframework.stereotype.Component`，改由 config 条件化提供，避免同类型双 Bean 冲突；保留 `implements ApplyTaskPublisher`。
5. `src/main/resources/application.yml`（EDIT）：`resumeai.mq.mode: ${MQ_MODE:memory}`；`management.health.rabbit.enabled: ${MQ_RABBIT_HEALTH:false}`。
6. `src/test/java/.../event/RabbitMqApplyTaskPublisherTest.java`（NEW）：Mockito + `@Mock RabbitTemplate`，`@BeforeEach` 中构造被测对象（修正：避免字段声明处 `new` 早于 `@Mock` 注入导致 NPE），校验 exchange/routingKey/字段/traceId。

## 四、QA（质量保证）· 验证结果与遗留项
- **验证动作**：离线 Maven 全量 `mvn test`（JAVA_HOME=/d/JDK2，classworlds launcher 直调，指定缓存仓库，清 `_remote.repositories` 标记）。
- **结果**：`Tests run: 80, Failures: 0, Errors: 0, Skipped: 0 — BUILD SUCCESS`（79 原绿 + 新发布器单测 1）。默认 `memory` 模式不破既有、不依赖 broker。✅
- **遗留项（如实登记）**：
  - L1：消费端 / 延迟执行 / Redis 幂等去重（Task #65，P1）。
  - L2：RabbitMQ 本地未起时 health DOWN 为预期（ADR-004 event/ 延后预期），生产设 `MQ_MODE=rabbit` + `MQ_RABBIT_HEALTH=true` 启用。
  - L3：Flyway MySQL 支持仍离线缺失（dev 库手动 SQL 绕开）——A 阶段补。
  - L4：`/auth/login` 仍签 mock token（非 RS256 签发）——C 阶段补。

## 五、合并信息（GitHub 连接器自动推进）
- 提交：`java-business-p0` 分支，commit 待生成（见下方合并记录）。
- 流程：push → 开 PR → 等 `gates`（契约+PRD/HLD 追溯+scaffold+mvn compile/test）+ `server-python tests` 双绿 → squash 合并 `master`。
- 铁证：`git ls-tree origin/master` 验文件进树（不以本地工作树判断）。
- 历史 merge 参照：PR#2→`99ab86a` / PR#3(d+JwtAuthFilterTest)→`cb260216` / PR#4(t_user 修复)→`a99b4da`。
