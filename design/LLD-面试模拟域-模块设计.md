# LLD：面试模拟域模块设计（v1.0）

> 上游：HLD §6.16（G7-1 会话状态机 / G7-2 rubric 透明可申诉 / G7-3 ASR 降级）、§3.9 面试题生成/AI 面试、§4.5 B02/B03、§5.2 实体 `INTERVIEW_SESSION`。
> 机器可读契约：`design/contracts/interview-*`（见 §9，已纳入零依赖校验器 + CI/pre-commit 双闸门）。
> 关联模块：[LLD-AI编排服务-模块设计.md](./LLD-AI编排服务-模块设计.md)（B01–B05 复用）；[LLD-平台适配器系统-模块设计.md](./LLD-平台适配器系统-模块设计.md)。

---

## 1. 模块边界与职责

面试模拟域由**两层**协作：

| 层 | 技术 | 职责 |
|----|------|------|
| 会话编排层 | 服务端 Java | 持有 `INTERVIEW_SESSION` 状态机、写 `interview_session_event` 审计、触发题目/评估、生成报告、重跑/申诉 |
| 智能层 | 服务端 Python LLM 编排 | 复用 B01–B05 内部契约：B02 生成面试题、B03 逐轮评估；降级时回退题库/模板/建议 |

**不负责**：真实浏览器动作（下沉本机 Agent）、简历解析（LLD 解析模块）、支付/通知（各自模块）。

**核心实体**：`INTERVIEW_SESSION`（⑭，§5.2）、`INTERVIEW_QUESTION_SET`（⑫，由 A17 前序联动生成）、`INTERVIEW_QUESTION`（面试题，本 LLD §4 定义）。

---

## 2. 统一门面 InterviewSessionFacade

对外（Java→Python 内部）暴露 6 个门面方法，字段大纲详见 `design/contracts/interview-domain.methods.json`（机器可读权威）：

| 方法 | 同步 | 超时 | 降级目标 | 说明 |
|------|------|------|----------|------|
| `createSession` | 是 | 2000ms | — | 创建会话，返回 sessionId（state=created） |
| `getNextQuestion` | 否 | 30000ms | question_bank | 驱动 B02 生成/取下一题（异步 ≤30s） |
| `submitAnswer` | 否 | 3000ms | advise | 驱动 B03 逐轮评估 |
| `evaluateSession` | 是 | 5000ms | advise | 综合评分（G7-2 rubric 聚合） |
| `endSession` | 是 | 2000ms | — | 终态（completed/abandoned） |
| `getReport` | 是 | 2000ms | — | 取评估报告 + 重跑/申诉入口 |

---

## 3. 会话状态机（G7-1）

状态集合（机器可读见 `interview-session.schema.json`）：
`created → active → in_progress ⇄ paused → completed → scored → archived`，`abandoned` 为终态（从 `in_progress`/`completed` 可达）。

| 当前态 | 允许转移到 | 触发 |
|--------|-----------|------|
| `created` | `active` | 用户点击开始（A17 返回 sessionId 后首个动作） |
| `active` | `in_progress` | 首题下发、用户首次作答 |
| `in_progress` | `paused` / `completed` / `abandoned` | 用户暂停（断点续聊）/ 轮次结束或主动结束 / 超时未应答（单轮 30min 静默关） |
| `paused` | `in_progress` | 用户恢复续聊（上下文保留，非状态回退） |
| `completed` | `scored` / `abandoned` | 评估完成生成报告（A19）/ 用户放弃评分 |
| `scored` | `archived` | 超过保留期归档（§5.3） |
| `abandoned` | （无） | 终态 |

**不变式**：
- 无回退边；`in_progress ⇄ paused` 仅断点续聊，保留上下文（§7.3）。
- 单轮调用受 §28.1 LLM 成本双闸「单会话最大调用轮次」约束。
- 摄像头仅本地画中画、不进会话状态（PRD §683）。
- 语音作答经 ASR 转写为文本入轮次（G7-3）。
- **每态变更写 `interview_session_event`**（事件见 §9），供审计与「重跑/申诉」溯源——这是状态机可信性的硬要求，不得跳过。

---

## 4. 面试题（INTERVIEW_QUESTION）

`getNextQuestion` 内部调用 B02（异步），字段大纲：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 题目唯一 id |
| `text` | string | 题干 |
| `type` | enum(behavior\|tech\|case) | 行为/技术/案例 |
| `expectedPoints` | string[]? | 期望要点（评分参考） |
| `jdKeywordsCoverage` | float(0..1) | 本题覆盖 JD 技术关键词比例 |

**成功标准**：整场 `jdKeywordsCoverage` 均值 ≥ 0.8（PRD §7.2）。降级链：LLM 生成 → 题库（question_bank）→ 预设模板题。

---

## 5. 逐轮评估（驱动 B03）

`submitAnswer` 内部调用 B03（异步 ≤3s），返回该轮 `turnScore`(0..1) + `rubric` 逐维分(1-5) + `feedback`。降级链：LLM 评估 → 给建议不评分（advise）→ 不评分（标注降级）。

---

## 6. rubric 综合评估模型（G7-2）

**维度集**（每维 1–5 分，PRD §691）：

| 维度 | 默认权重 | 说明 |
|------|----------|------|
| 回答完整性 | 0.25 | 是否覆盖问题要点 |
| 技术准确性 | 0.25 | 技术内容是否正确 |
| 结构化表达 | 0.25 | 条理/逻辑清晰度 |
| 与岗位匹配度 | 0.25 | 与 JD 契合度 |
| （可选第 5 维） | 待拍板 | 见 §11 待拍板项 T2 |

**聚合**：各维 `rawScore`(1–5) × 维度权重 → **加权综合分 0–100**（机器可读见 `interview-evaluation.schema.json`）。
**透明可申诉**（§26.2）：报告逐维度展示分数与理由；提供「重跑本场」（换模型/清上下文重评）与「申诉/反馈」入口，反馈回流为评分模型训练信号。降级评估（LLM 不可用→规则建议）**必须**置 `degradeFlag=true` 并在报告标注「本次为降级评估，仅供参考」。

---

## 7. ASR 降级链（G7-3）

语音作答经 ASR 转写为文本再入评估。抽象 `AsrProvider`（主+备）：

| 优先级 | 供应商 | 说明 |
|--------|--------|------|
| 1（主） | `cloud_asr` | 云端合规境内 ASR（优先） |
| 2（备） | `ondevice_asr` | 端侧/离线 ASR |
| 3（兜底） | `text_input` | 均不可用→文本输入（麦克风拒绝即文本，PRD 模块 5/6 边界） |

**约束**：ASR 文本同样过 B6 内容安全层（§6.11）；`modality=voice_asr` 时 `answerReceived` 事件记录实际 `asrProvider`，降级文本时为 `null`。

---

## 8. 降级链汇总

| 能力 | 一级（LLM） | 二级 | 三级 |
|------|------------|------|------|
| 面试题生成 | LLM 生成 | 题库 | 预设模板题 |
| 逐轮评估 | LLM 评估 | 给建议不评分 | 不评分（标注降级） |
| 语音输入 | 云端 ASR | 端侧 ASR | 文本输入 |

LLM 不可用统一返回 `LLM_DEGRADED`（错误码注册表），前端提示「降级模式」。

---

## 9. 机器可读契约映射

| 契约文件 | 承载 |
|----------|------|
| `interview-domain.methods.json` + `.registry.schema.json` | 门面 6 方法 + 状态机 + rubric + ASR 降级链（自洽注册表） |
| `interview-session.schema.json` | `INTERVIEW_SESSION` 实体（state 枚举 8 态） |
| `interview-question.schema.json` | 单道面试题 |
| `interview-evaluation.schema.json` | 评估报告（加权综合分 0–100 + 逐维理由 + degradeFlag） |
| `asr-config.schema.json` | ASR 降级配置 |
| `interview-events.event.schema.json` | 面试域事件（5 类 payload，oneOf 定型） |

校验器（`validate_contracts.py`）覆盖：schema 正向必过 / 反向必败证伪 / 注册表自洽 / 错误码唯一。CI（`.github/workflows/contract-check.yml`）+ pre-commit 双闸门。

---

## 10. 待拍板项登记（显式，非静默覆盖）

| 编号 | 项 | 现状 | 默认处置 |
|------|----|------|----------|
| T1 | ASR 供应商选型（具体云端/端侧厂商） | HLD G7-3 ⚠ 留 LLD | 本 LLD 抽象 `AsrProvider`，编码期配置中心确定具体厂商；降级链 `cloud_asr→ondevice_asr→text_input` 已固化 |
| T2 | rubric 第 5 维启用与权重 | HLD G7-2 ⚠ 不拍板 | 默认 4 维等权（各 0.25）；第 5 维是否启用及权重由产品/将军拍板，启用后 `dimensions` 扩至 5、`defaultWeights` 同步更新 |
| T3 | 加权权重最终值 | HLD 不拍板 | 默认等权；产品可配置非等权，须保证 `defaultWeights` 求和=1 |

以上三项为技术/产品侧待拍板，不构成「接口契约缺失」——接口形态已机器可读闭环，仅数值/厂商待定。

---

## 11. 与 HLD 追溯

| HLD 锚点 | 本 LLD 落点 |
|----------|------------|
| §6.16 G7-1 会话状态机 | §3 + `interview-session.schema.json` |
| §6.16 G7-2 rubric 透明可申诉 | §6 + `interview-evaluation.schema.json` |
| §6.16 G7-3 ASR 降级 | §7 + `asr-config.schema.json` |
| §3.9 面试题生成/AI 面试 | §2/§4/§5（复用 B02/B03） |
| §5.2 `INTERVIEW_SESSION` 实体 | §1/§3 |
