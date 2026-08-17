<!-- TRACE
role: PM | software-product-manager
package: U6 面试模拟 UI (A16/A17/A18/A19)
agent_run: 2026-08-17T21:42
author_of_record: software-product-manager（本轮子 agent 调度瞬断，由 Team Lead 代笔，见 ROLE-DELIVERABLES.md 注）
upstream_read: [prd/PRD-简历自动投递与面试模拟-最终版.md §595-720(模块5 面试模拟备战/模块6 AI面试模拟/模块7 联动), design/contracts/external-api.registry.json(A16-A19), design/contracts/interview-questions.response.schema.json, design/contracts/interview-session-create.response.schema.json, design/contracts/interview-session-answer.response.schema.json, design/contracts/interview-session-report.response.schema.json, design/ui/00-design-system.html, design/ui/ROLE-WORKBOOK.md §2]
downstream_write: [design/ui/roles/U6-arch.md, design/ui/screens/U6-interview.html, design/ui/interaction-U6.md]
decisions: 本包覆盖"面试备战(A16)+AI面试模拟(A17/A18/A19)"两大模块；不实现真实 LLM 对话/语音识别/摄像头采集（仅本地预览占位，不参与评估不上传），属红线约束；每日次数上限按套餐(专业版每日10次)展示剩余并超限引导升级；评估报告 4 维度(1-5)对齐 PRD §693 + A19 dimensions。
status: DONE
-->

# U6 面试模拟 UI · 产品经理需求规格（A16 / A17 / A18 / A19）

> 角色：PM（software-product-manager）｜包：U6 面试模拟 UI｜对应契约：A16 面试题列表(备战) / A17 创建会话 / A18 提交作答 / A19 评估报告
> 配套：架构师产物 `U6-arch.md` ← 本文件被其引用；工程师产物 `U6-interview.html` + `interaction-U6.md` ← 本文件被其引用

## 1. 目标与范围
**目标**：在 PC 端提供"投递 → 备战 → 复盘"闭环中的面试准备与模拟能力——用户既能浏览 AI 生成的备战题集（自我介绍/项目/技术/行为），也能进行一场完整的 AI 模拟面试并在结束后拿到结构化评估报告。
**范围（做）**：
- 面试备战（A16）：题集列表（accordion 手风琴，单卡展开）、题集元信息（题量/难度/标签）、"模拟作答"入口。
- AI 面试模拟（A17/A18）：创建会话（选类型/岗位/模式）、对话式作答（文本/语音占位）、中途生成报告。
- 评估报告（A19）：综合分(0-100) + 4 维度(1-5) + 文字反馈 + 兜底标记 + 申诉/重跑入口。
**范围（不做 · 边界）**：真实 LLM 流式对话、真实语音 ASR、真实摄像头采集与上传、移动端完整模拟（PRD 规定移动端仅看报告）。这些在原型中为 mock/占位，真实能力在 V 阶段接契约 API。

## 2. 交互需求清单
| # | 交互 | 触发 | 行为 | 反馈 | 异常/边界 |
|---|------|------|------|------|-----------|
| R1 | 题集加载 | 进入"面试备战" | GET /interviews/questions(A16) 拉取 questionSets | 骨架→accordion 卡片（setId/title/questionCount/difficulty/tags） | 失败→错误态+重试；空→空态"AI 正在生成中，请稍后刷新" |
| R2 | 手风琴 | 点卡片标题 | 展开该卡、收起其他（同刻仅一张） | 展开动画(≤200ms) | 内容超长→内部滚动(≤2400px) |
| R3 | 模拟作答入口 | 点卡片内"模拟作答" | 跳"AI 面试模拟"并预选该题集 | 路由+预填 questionSetId | 未完善简历/未选岗位→拦截提示"请先完善简历并选择目标岗位" |
| R4 | 创建会话 | 点"开始面试" | POST /interviews/sessions(A17){jobId?,mode,questionSetId?}→sessionId+status(created→in_progress) | 进入对话视图，AI 开场白 | 每日次数超限→升级提示+仅看报告；请求失败→错误态 |
| R5 | 作答提交 | 输入文本/切语音占位→"发送" | POST /sessions/{id}/answer(A18){questionId,answer,mode}→accepted+score(0-1 可选) | 气泡追加"我"+AI 评估/追问气泡 | 麦克风拒→自动纯文本；断网→保留上下文可续 |
| R6 | 摄像头本地预览 | 点"开启本地镜像" | 仅本地画中画占位（不参与评估/不录制/不上传） | 预览框开关态 | 拒绝权限→仍正常进行；红线：绝不调用真实采集上传 |
| R7 | 结束并出报告 | 点"结束面试" | 生成报告 GET /sessions/{id}/report(A19) | 跳"评估报告"：overallScore+dimensions+feedback+degradeFlag | LLM 失败→degradeFlag=true+"题库兜底"提示 |
| R8 | 申诉/重跑 | 报告页"申诉"/"重跑" | appealEntry/rerunEntry 占位入口 | 提示（v2 接真实流程） | — |

## 3. 验收标准（对应契约字段）
- AC1：题集字段含 `setId/title/questionCount`(必填) + `difficulty(enum easy|medium|hard,nullable)` + `tags[]`，与 A16 + `interview-questions.response.schema.json` 一致。
- AC2：创建会话响应解析 `sessionId(string)` + `status(enum created|in_progress|completed|abandoned)`，与 A17 一致。
- AC3：作答提交请求含 `questionId` + `answer(text|audioRef)` + 可选 `asrProvider`；响应解析 `accepted(bool)` + `score(0-1,nullable)`，与 A18 一致。
- AC4：报告字段含 `sessionId` + `overallScore(0-100)` + `dimensions[{dim,rawScore(1-5),reason,score?(0-1)}]` + `feedback` + 可选 `degradeFlag(bool)`，与 A19 一致。
- AC5：评估 4 维度枚举与 PRD §693 对齐（回答完整性/技术准确性/结构化表达/与岗位匹配度），rawScore 在 1–5。

## 4. 边界与异常场景
- 无简历/未选岗位：R3 拦截 + 文案提示（PRD §650/§703）。
- 每日次数超限：套餐配额（专业版 10 次/日）展示剩余，超限引导升级并仅允许看历史报告（PRD §779/§708）。
- 摄像头/麦克风权限拒绝：降级为文本模式，功能不中断（PRD §685/§705）。
- LLM 超时/失败：degradeFlag=true，启用题库预设题兜底（PRD §706）。
- 中断网：保留上下文，恢复续答（PRD §707）。

## 5. 无障碍 + 动效要求
- 手风琴卡片标题须可键盘聚焦（Enter/Space 展开）、`aria-expanded` 标注；单卡展开语义清晰。
- 对话输入/发送、`aria-live` 播报 AI 新消息（读屏友好）。
- 摄像头预览框明确"本地·不参与评估"，不触发真实权限弹窗（红线）。
- 动效：卡片展开过渡≤200ms、消息滑入、报告分数计数动画；全部尊重 `prefers-reduced-motion`（见 `02-motion-system.html`）。

## 上游引用
- PRD：`prd/PRD-简历自动投递与面试模拟-最终版.md` §595-720（模块 5 面试模拟备战 ASCII/手风琴/移动端差异/边界；模块 6 AI 面试模拟布局/摄像头定义/面试类型/流程/评估维度/边界；模块 7 联动）。
- 契约：`design/contracts/external-api.registry.json` A16-A19 行；`interview-questions.response` / `interview-session-create.response` / `interview-session-answer.response` / `interview-session-report.response` 四个 schema。
- 设计基线：`design/ui/00-design-system.html`（组件 token）、`design/ui/ROLE-WORKBOOK.md` §2（PM 工作清单）。

## 下游交付
架构师（`U6-arch.md`）请重点读：§2 交互需求清单（R1–R8 作为组件/状态设计输入）、§3 验收标准（作为字段映射表依据）、§4 边界（作为状态模型与异常态依据）。工程师（`U6-interview.html` + `interaction-U6.md`）请读 §2/§3/§5 实现行为与无障碍。
