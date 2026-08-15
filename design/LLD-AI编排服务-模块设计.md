# LLD 详细设计：AI 编排服务（服务端 Python LLM 网关）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合 HLD §9.4 接口完整性残余「B01–B05 机器可读契约」+ 异步 AI 结果回写事件缺口）
> 编写依据：LLD 交付标准（IEEE 1016-2009 设计视图 / GB-T 8567—2006 详细设计 / Amazon LLD 模板）
> 关联上游：HLD v3.16（§3.8 / §3.9 / §2.3 / §4.5 B01–B05 / §4.7 / §6.11 B1·B5·B6 / §34.2）× PRD v4.5 模块 5·6 / §7.2·§7.3·§7.4·§26.2·§26.4
> 定位：LLD 序列之**AI 编排服务模块**（服务端 Python FastAPI，ADR-002 双语言异构中的 LLM 网关）；与「本机 Agent 与投递执行」(v1.2)、「平台适配器系统」(v1.0) 协同
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

AI 编排服务是系统 AI 能力的**唯一承载点**（ADR-002：与 Java 业务服务双语言异构，不共享库），统一承接所有 LLM 调用：模型路由、三级降级链、配额与超时、内容安全。核心约束（来自 HLD §3.8 / ADR-002）：

- **执行侧 = 服务端 Python（FastAPI）**：调用外部大模型 API（境内合规，主 DeepSeek）；**不承载浏览器自动化**（已下沉本机 Agent，ADR-003）。
- **不落业务数据**：AI 结果一律经 MQ（RabbitMQ）回写由 Java 侧负责落库（跨服务最终一致，ADR-002）。本模块只产出统一结构 AI 结果。
- **仅内网可达**：B01–B05 仅 Java→Python 服务间调用，Nginx 不暴露；鉴权用 `X-Internal-Token`（HLD §4.5 / §939）。
- **故障隔离**：全实例不可用 → AI 功能降级，非 AI 功能（简历编辑/浏览/投递）照常，顶栏「AI 服务维护中」横幅（HLD §3.8 关键点）。

调用边界总览：

```
Java 业务服务 ──(B01–B05, 内网 REST, X-Internal-Token)──> AI 编排服务(Python)
   ^                                                          │
   └──────(MQ: ai.task.result 事件, B02/B04/B05 异步回写)──────┘
                                    │
                                    ▼
                           外部 LLM API(主 DeepSeek + 备用) + 规则引擎(降级)
```

---

## 1. 统一 AI 网关门面（AIOrchestrator）

门面接口为机器可读注册表：`design/contracts/ai-orchestrator.methods.json`（schema：`ai-orchestrator.registry.schema.json`，contractVersion 1.0.0）。五个方法按 HLD §4.5 B01–B05：

| 方法 | 端点 | sync | timeoutMs | degradeTo | 请求 → 响应（机器可读 schema） |
|------|------|------|-----------|-----------|------|
| `b01` match | `/internal/v1/ai/match` | true | 5000 | rule_engine | `b01-match.request` → `b01-match.response` |
| `b02` questions | `/internal/v1/ai/questions` | false | 30000 | question_bank | `b02-questions.request` → `b02-questions.response` |
| `b03` evaluate | `/internal/v1/ai/evaluate` | true | 3000 | advise | `b03-evaluate.request` → `b03-evaluate.response` |
| `b04` resumeOptimize | `/internal/v1/ai/resume/optimize` | false | 10000 | template | `b04-optimize.request` → `b04-optimize.response` |
| `b05` atsScore | `/internal/v1/ai/ats` | false | 10000 | score_skip | `b05-ats.request` → `b05-ats.response` |

- **同步方法**（b01/b03）：含超时熔断（§6 超时）；失败直接返回 `LLM_DEGRADED` 信封（`retryable=true`，调用方走降级路径）。
- **异步方法**（b02/b04/b05）：立即返回 `taskId`，结果经 MQ `ai.task.result` 事件回写（§7），Java 侧按 `taskId` 落库。

---

## 2. 三级降级链（逐方法）

降级按场景逐级回退（HLD §3.8 关键点 / §2.3 流程三），保证「调用方不感知降级路径」：

| 方法 | 主链路 | 降级 1 | 降级 2（最终） | 兜底 |
|------|--------|--------|--------|------|
| b01 match | 主 LLM（DeepSeek） | 备用 LLM（golden set κ 回归通过） | 规则引擎（关键词匹配，B5） | 返回 `LLM_DEGRADED` |
| b02 questions | 主 LLM 生成 | 备用 LLM | 题库模板（命中 JD 关键词固定题） | 返回 `LLM_DEGRADED` |
| b03 evaluate | 主 LLM 评估 | 备用 LLM | 给建议不评分（`advise`） | 返回 `LLM_DEGRADED` |
| b04 resumeOptimize | 主 LLM 优化 | 备用 LLM | 模板化改写 | 返回 `LLM_DEGRADED` |
| b05 atsScore | 主 LLM 评分 | 备用 LLM | 不评分（`score_skip`，仅给结构建议） | 返回 `LLM_DEGRADED` |

响应 `model` 字段（`deepseek`/`backup`/`rule`）记录实际来源，供归因与质量监控；降级事件记 `traceId`。

---

## 3. 模型路由与 golden set 质量回归

- **主 + 备用**：1 主（DeepSeek V4-Flash 档，ADR-009）+ 1–2 备用 LLM（HLD §34.2）。主模型不可达（超时 / 5xx 比例超阈值）→ 自动切备用。
- **prompt 适配层**：切换时做供应商差异归一（HLD §26.1），屏蔽模型间接口差异。
- **质量回归闸门**：切换至备用后，跑 golden set 质量回归，评分一致性需在 **κ 容差内**（HLD §2.3 / §6.11 B5）；偏差超 κ 容差 → 跳至降级 2（规则引擎/模板），不污染结果。
- **单次调用超时重试 1 次**：仍失败 → 进入降级链；面试对话保留上下文可断点续聊（HLD §3.8 关键点）。

---

## 4. 内容安全层（HLD §6.11 B6）

所有 AI 输出（面试题 / 评估 / 话术 / 优化文案）经内容安全审核（HLD §26.4 / §17.4）：

- **过滤层**：拦截政治敏感 / 违法 / 歧视 / 骚扰；不鼓励造假夸大（呼应伦理约束）。
- **可测口径**：golden set 歧视命中 = 0（硬指标）；审核失败 → 该条输出降级/拒答（不走正常链路，见 §9 R-10 第 4 类）。
- **ASR 文本同等过审**：语音转写文本同样过内容安全层（HLD §6.16 G7-3 对齐）。

---

## 5. 匹配度模型（HLD §6.11 B5）

- **LLM 语义匹配为主**：JD×简历语义匹配，输出 `score(0..1)` + `matchedSkills` + `explanation`。
- **规则层兜底（降级用）**：当主/备 LLM 不可达时，规则引擎按维度加权，`score` 归一化到 0–100 再映射 0..1：
  - 技能匹配 40% / 行业匹配 20% / 城市匹配 20% / 经验匹配 20%（HLD §6.11 B5 已锚定）。
- **冷启动**：无历史行为时退化为纯 JD×简历匹配，不引入伪权重。
- **验收**：规则层与 LLM 层在 golden set 上 Cohen's κ ≥ 0.6（HLD §6.11 B5）。
- **语义检索（B1）**：v1.0 不引入独立向量服务（HLD §2.5 无向量库）；LLM 语义 + 规则为主，预留本地向量扩展接口位（不影响本版契约）。

---

## 6. 配额与超时（SLA）

- **配额计数**：Redis 计数（HLD §3.8 依赖）。配额耗尽：紧急任务（投递联动 b01）优先配额，非紧急（b02/b04/b05 生成/优化）降级规则引擎/模板（HLD §3.8 关键点）。
- **超时预算（SLA，HLD §4.5 / §941）**：b01 ≤5s、b02 ≤30s、b03 ≤3s、b04 ≤10s、b05 ≤10s。超预算 → 直接走降级链（§2）。
- **可重试窗口**：同步方法单次超时重试 1 次（§3），仍失败降级。

---

## 7. 异步结果 MQ 回写（B02/B04/B05）

HLD §4.5 注明「B02/B04/B05 异步，结果经 MQ 回写（§4.6）」——但 §4.6 原未列该事件契约，本 LLD 补 `ai.task.result` 事件（机器可读：`ai-result.event.schema.json`）：

- **生产者**：AI 编排服务（异步方法完成/降级后）。
- **消费者**：Java 业务服务（按 `taskId` 落库 `INTERVIEW_QUESTION_SET` / 优化记录 / ATS 记录）。
- **payload**：`{ eventType:"ai.task.result", traceId, taskId, method(b02|b04|b05), status(ok|degraded), result, degradeTo?, producedAt }`。
- **去重**：Java 侧按 `taskId` 幂等（重复事件覆盖首次结果，不重复落库）。
- **失败处理**：MQ 投递失败 → 编排服务本地重试队列 + 告警；不影响同步链路。

---

## 8. 可观测性

- **traceId 贯穿**：所有 LLM 响应、`ai.task.result` 事件、降级记录均带 `traceId`（HLD §4.5 注），便于归因与质量回归。
- **指标**：LLM 调用 p99 延迟、降级率、golden set κ 偏差、配额余量、内容安全命中率。
- **SLI**：AI 功能可用性（非 AI 功能不受影响）；匹配 p99 ≤5s（HLD §1232）。

---

## 9. R-10 幻觉硬熔断默认阈值（显式登记待决项）

HLD §4.5 注「幻觉硬熔断阈值见 R-10（待 LLD 细化）」。本 LLD 给出**默认阈值方案**并显式登记为待技术侧最终拍板（fail-closed：配置中心缺失时启用最严档）：

| 检测类 | 默认阈值（LLD 默认，可配置） | 触发动作 |
|--------|------|------|
| 实体越界（编造） | 优化/ATS 文案中出现的公司名/院校名/技能证书名不在用户原始 resume 实体集合内 | 拦截 + 重生成（≤1 次）；仍失败 → 降级 template |
| 自我矛盾 | 同一次响应内结论与评分矛盾（如 explanation 称「匹配度高」但 score<0.3） | 标记 `degraded`，记 traceId 供人工审查 |
| 连续非结构化超长 | 单字段输出 > 1200 token 且无合理标点/分段暂停 | 截断 + 降级 |
| 安全词命中 | 输出命中内容安全层（§4）拦截词 | 直接降级/拒答（不走正常链路） |

> **待决登记（非静默）**：R-10 具体数值（1200 token、κ 容差具体值、实体集合匹配相似度阈值）由编码期配置中心最终确定；本 LLD 仅给默认档与 fail-closed 行为，不构成已拍板最终值。HLD §9.4 待决项同步登记。

---

## 10. 机器可读契约索引

`design/contracts/` 下本模块相关契约（均为零依赖校验器双闸门覆盖项）：

| 文件 | 用途 |
|------|------|
| `ai-orchestrator.registry.schema.json` | 注册表自洽 schema |
| `ai-orchestrator.methods.json` | 五个方法注册表数据（契约版本 1.0.0） |
| `b01-match.request/response.schema.json` | B01 请求/响应 |
| `b02-questions.request/response.schema.json` | B02 请求/响应 |
| `b03-evaluate.request/response.schema.json` | B03 请求/响应 |
| `b04-optimize.request/response.schema.json` | B04 请求/响应 |
| `b05-ats.request/response.schema.json` | B05 请求/响应 |
| `ai-result.event.schema.json` | 异步回写事件 `ai.task.result` |

契约版本协商沿用 HLD §6.13.4：服务端/调用方 `contractVersion` 不匹配返回 `426 Upgrade Required` + 最低兼容版本，消费者（Pact）驱动契约纳入 CI。
