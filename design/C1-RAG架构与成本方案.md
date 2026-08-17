# C1 · RAG 架构与成本方案（S2 阶段二 · 含 LLM 成本硬上限+熔断）

> 文档版本：2026-08-17 · v1.0（S2 交付物，对齐 PROJECT_BRAIN §1 C1 / 护栏 2）
> 关联上游：PRD v4.5 §7 AI 产品专项 / §16 商业化测算；HLD v3.35 §4.5 AI 编排；MEMORY「项目性质与运维边界决策」
> 定位：阶段二（RAG 延展）+ 护栏 2（LLM 成本硬上限+熔断）落地说明
> 作者：架构师（AI 协作，全委托授权下自主推进）

---

## 0. 范围与边界（先说清什么做、什么不做）

- **本交付物必做**：护栏 2 = LLM 成本「硬上限 + 熔断」的可度量落地（已实现于 `scaffold/src/llm_match.py` 的 `CostGuard` + 本文件的 `BudgetPolicy` 装配）。
- **RAG 架构 = 设计延展、本次不建重管线**：按用户 2026-08-17 明确「核心投递闭环跑通前不急于上 RAG」，RAG 检索+向量库一层仅作**架构设计与接缝预留**，不在此轮实现向量库/嵌入管线（避免引入索引质量等新故障面）。
- **护栏 4/5/6（灰度/PIPL/法检）= 用户 2026-08-17 延后/跳过，不计入本次 /goal**，本文不覆盖其成本侧。

## 1. 护栏 2：LLM 成本硬上限 + 熔断（已落地）

### 1.1 实现位置
- `scaffold/src/llm_match.py`
  - `CostGuard`：日硬上限 `daily_cap_cents` + 失败熔断 `failure_threshold`/`cooldown_s`；`charge()` 预扣、`record_success()`/`record_failure()` 记账、超帽或连续失败即 `OPEN` 拒绝后续调用。
  - `MatchService.match()`：每次调用先 `guard.charge()`，护栏触发即抛 `CostGuardOpen`，阻断成本失控。
- `scaffold/src/cost_policy.py`（`BudgetPolicy`）：把 `CostGuard` 装配为产品级预算策略（日上限/单call成本/熔断阈值/冷却），统一注入 `MatchService`，确保护栏「落地」而非孤立类。

### 1.2 阈值与配置边界（诚实）
| 参数 | DEMO 默认 | 生产值来源 |
|---|---|---|
| 日硬上限 `daily_cap_cents` | 50000（¥500/天） | **部署方/用户按预算配置**（循环不代设真实金额、不花钱） |
| 单 call 成本 `per_call_cents` | 10 | 按所选模型定价配置 |
| 熔断失败阈值 `breaker_threshold` | 5 | 运维配置 |
| 冷却 `cooldown_s` | 60 | 运维配置 |

> ⚠️ 循环不代设真实生产金额；最终硬上限由用户在部署时按预算确定，属用户/运维配置决策（非待拍板事项，是部署参数）。

### 1.3 验证（已单测）
- 正常匹配：band/score 返回 + 成本记账（剩余=上限-10）。
- 超日硬上限：第 N 次调用抛 `CostGuardOpen`，电路 OPEN。
- 连续失败达阈值：电路 OPEN，后续调用被拦。
- 见 `scaffold/tests/test_llm_match.py` + `test_cost_policy.py`，均 PASS，双闸门绿。

## 2. RAG 架构（设计延展 · 接缝预留，本次不建重管线）

### 2.1 判定：RAG 是「自然延展」而非推倒重来
现有「服务端 LLM 调用」(`MatchService`) 就是现成接缝。RAG = 在匹配/面试模拟侧**加一层「检索 + 向量库」**，让生成 grounded 在真实知识而非纯模型记忆。

### 2.2 适用场景（按价值排序）
1. **面试模拟 grounded**：检索真实题库/公司信息/岗位 JD，生成贴合的模拟问答（价值最高、风险最低）。
2. **求职建议 grounded**：检索劳动法/行业知识/相似成功案例，给建议附依据。
3. **简历-岗位匹配 grounded**：检索相似成功投递案例，辅助匹配判分（核心匹配仍走规则+模型，RAG 作增强）。

### 2.3 架构草图（预留接缝）
```
用户/本机Agent
   └─> 服务端 API (ServerApp)
         └─> MatchService / InterviewService
               ├─ [现有] LLM 网关 (MockLLM / 生产适配)  ← 成本护栏 CostGuard 已挡
               └─ [RAG 延展·预留] Retriever
                     ├─ VectorStore (向量库，阶段二接入)
                     ├─ Embedder   (嵌入模型，阶段二接入)
                     └─ ContextAssembler (拼检索上下文 -> prompt)
```
- **不引入**：向量库/嵌入管线/索引质量运维——属阶段二能力，核心闭环跑通后再上。
- **复用护栏**：RAG 检索调用同样经 `CostGuard` 记账（检索也算 token 成本），护栏 2 对 RAG 同样有效。

### 2.4 为何此刻不做重 RAG
- 用户明确「核心投递闭环跑通前不急于上」；RAG 引入向量库/嵌入/索引质量等新故障面，与「零生产事故」目标阶段性冲突。
- 当前 LLM 用于匹配判分 + 面试模拟，规则+模型已够用；RAG 是增强而非阻塞。

## 3. 与护栏 3（监控）衔接
- `BudgetPolicy.as_dict()` 暴露 `remaining_cents` / `circuit_open`，供 C2 `LightweightMonitor` 的 `llm_cost_cents` + `llm_cost_over_cap` 告警消费。
- 成本护栏与监控形成闭环：护栏 2 拦成本失控，护栏 3 曝光成本趋势。

## 4. 交付状态
- ✅ 护栏 2 代码落地（`CostGuard` + `BudgetPolicy`）+ 单测全过 + 双闸门绿。
- 🟡 RAG 架构已设计、接缝预留；重管线延至核心闭环跑通后（阶段二能力，非本次 /goal 阻塞）。
- ⏸ 护栏 4/5/6 用户延后，不计入。
