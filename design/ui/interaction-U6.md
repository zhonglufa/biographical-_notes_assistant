<!-- TRACE
role: Engineer | software-engineer
package: U6 面试模拟 UI (A16/A17/A18/A19)
agent_run: 2026-08-17T21:46
author_of_record: software-engineer（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U6-pm.md(§2/§3/§5), design/ui/roles/U6-arch.md(§1/§2/§3/§4/§5), design/ui/screens/U3-applications.html, design/ui/02-motion-system.html, design/ui/ROLE-WORKBOOK.md §4]
downstream_write: [design/ui/roles/U6-qa.md]
decisions: 原型三视图(备战/模拟/报告)切换；备战 accordion 单卡展开(≤200ms)；模拟走 A17→A18→A19 流程 mock；摄像头本地占位绝不调真实采集(红线)；语音为占位切换不调真实麦克风；配额 mock。全部纯前端态，无凭据/部署/真实 PII。
status: DONE
-->

# U6 面试模拟 · 交互规格（A16 / A17 / A18 / A19）

> 配套原型：`design/ui/screens/U6-interview.html`（可交互 HTML，mock 数据，不接真实后端/凭据）
> 上游：PM `U6-pm.md` + 架构师 `U6-arch.md` ← 本文件严格按其字段映射表(§4)与状态模型(§2)实现

## 1. 屏幕目标
在 PC 端补齐"投递 → 备战 → 复盘"闭环的面试侧：浏览 AI 备战题集（A16）、进行一场 AI 模拟面试（A17 建会话 / A18 作答 / A19 报告）、查看结构化评估报告。安全模型：摄像头仅本地预览、绝不采集上传；语音为占位；配额按套餐展示。

## 2. 信息结构
- 顶栏（AppShell 复用）：标题"面试模拟" + 今日剩余次数（套餐配额 mock：专业版 10/日）。
- Tabs：[面试备战 | AI 面试模拟 | 评估报告]。
- 备战视图（A16）：`Accordion` 题集卡片（setId/title/questionCount/difficulty/tags）+ 每卡"模拟作答"。
- 模拟视图（A17/A18）：SetupPanel（类型/岗位/模式/开始）+ CameraPiP（本地预览占位）+ SessionChat（对话气泡 + aria-live）+ InputBar（文本/发送/结束）。
- 报告视图（A19）：ScoreCard(overallScore 0-100) + EvalRadarLite(4 维度 1-5 条形) + FeedbackBlock + DegradeNote + 申诉/重跑占位。

## 3. 关键交互（对应 PM R1–R8）
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 题集加载 | 进入备战 | 骨架→accordion（A16 questionSets） | GET /interviews/questions |
| 手风琴 | 点标题 | 单卡展开/收起（≤200ms，aria-expanded） | — |
| 模拟作答 | 点"模拟作答" | 跳模拟并提示已预选题集 | A17 questionSetId? |
| 创建会话 | 点"开始面试" | 配额-1→mock A17{sessionId,status:in_progress}→AI 开场白 | POST /interviews/sessions |
| 作答提交 | 点"发送" | 追加"我"气泡→mock A18{accepted,score}→AI 追问 | POST /sessions/{id}/answer |
| 摄像头本地预览 | 点开关 | 仅本地画中画占位（不参与评估/不录制/不上传） | 红线：不调真实采集 |
| 结束出报告 | 点"结束面试" | mock A19→跳报告视图渲染 | GET /sessions/{id}/report |
| 申诉/重跑 | 报告页按钮 | 占位（v2 接真实流程） | appealEntry/rerunEntry |

## 4. 状态 / 转场 / 空态 / 错误
- 加载：备战视图注入 3 个 Skeleton，500ms 后渲染（模拟 A16 异步）。
- 空态：报告视图"暂无报告"；题集空→"AI 正在生成中，请稍后刷新"。
- 配额超限：今日剩余=0 → 显示升级提示 + 拦截开始面试 + 仅允许看历史报告（PRD §708/§779）。
- 会话状态机：created→in_progress→completed（映射 A17 status 枚举）；abandoned 预留。
- 摄像头/麦克风降级：拒绝不影响功能（本地预览仅占位；语音占位切文本）。

## 5. 与契约一致性
- 题集严格用 A16 `setId/title/questionCount(+difficulty?,tags?)`。
- 会话 `sessionId` + `status(enum created|in_progress|completed|abandoned)`（A17）。
- 作答 `answer(text|audioRef)` + `questionId` + 可选 `asrProvider`；响应 `accepted(bool)` + `score(0-1,nullable)`（A18）。
- 报告 `overallScore(0-100)` + `dimensions[]{dim,rawScore(1-5),reason,score?}` + `feedback` + 可选 `degradeFlag`；4 维度枚举对齐 PRD §693（A19）。

## 6. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-3：原型仅 mock、摄像头仅本地占位不采集不上传、无真实凭据/部署/真实 PII，**不触发红线**，自动提交。

## 上游引用
- PM：`design/ui/roles/U6-pm.md` §2/§3/§5（交互清单/验收/无障碍）。
- 架构师：`design/ui/roles/U6-arch.md` §1/§2/§3/§4/§5（组件树/状态/复用/字段映射/流转）。
- 范本：`design/ui/screens/U3-applications.html`（安全交互基线）、`U5-adapter.html`（Card/Dialog/Toast）。

## 下游交付
QA（`U6-qa.md`）请核查：本文件 §3 交互 vs PM R1–R8、§5 字段 vs 架构师 §4 映射表、§6 红线判定；并跑双闸门。
