<!-- TRACE
role: Architect | software-architect
package: U6 面试模拟 UI (A16/A17/A18/A19)
agent_run: 2026-08-17T21:43
author_of_record: software-architect（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U6-pm.md(§2 交互清单/§3 验收/§4 边界), design/ui/00-design-system.html, design/ui/01-app-shell.html, design/ui/ia-nav.md, design/contracts/external-api.registry.json(A16-A19), design/contracts/interview-questions.response.schema.json, design/contracts/interview-session-report.response.schema.json, design/ui/ROLE-WORKBOOK.md §3]
downstream_write: [design/ui/screens/U6-interview.html, design/ui/interaction-U6.md]
decisions: 单一 U6-interview.html 内做三视图(备战/模拟/报告)切换，复用 AppShell 顶栏+Tab+Card+Dialog+Toast；新增唯一组件=EvalRadarLite(4维度条形)+SessionChat(对话气泡容器)；会话状态机 created→in_progress→completed 映射 A17 status 枚举；摄像头仅本地占位(不调真实 API)。评估报告 4 维度严格来自 A19 dimensions.rawScore(1-5)。
status: DONE
-->

# U6 面试模拟 UI · 架构师设计（A16 / A17 / A18 / A19）

> 角色：Architect｜包：U6｜上游：`U6-pm.md`（需求/验收/边界）← 本文件引用其 §2/§3/§4｜下游：工程师 `U6-interview.html` + `interaction-U6.md` ← 本文件被其引用

## 1. 组件树
```
AppShell (复用 01-app-shell.html 顶栏+侧栏，激活"面试"导航)
└─ Page: 面试模拟 (U6)
   ├─ Tabs: [面试备战 | AI 面试模拟 | 评估报告]
   ├─ View 备战 (A16)
   │  └─ Accordion
   │     └─ PrepCard × N        // 复用 Card；标题可聚焦 aria-expanded
   │        ├─ MetaRow (title/questionCount/difficulty/tags)
   │        └─ ActionBar [模拟作答]
   ├─ View 模拟 (A17/A18)
   │  ├─ SetupPanel (类型/岗位/模式/剩余次数)
   │  ├─ CameraPiP (本地预览占位·不采集)  // 【新增安全占位】
   │  ├─ SessionChat (对话气泡容器)        // 【新增】
   │  │  ├─ Bubble(AI) / Bubble(我)
   │  │  └─ liveRegion (aria-live)
   │  └─ InputBar (文本/🎤切换/发送/结束)
   └─ View 报告 (A19)
      ├─ ScoreCard (overallScore 0-100)
      ├─ EvalRadarLite (4 维度条形)       // 【新增】
      ├─ FeedbackBlock (feedback 文本)
      └─ DegradeNote + EntryRow(申诉/重跑占位)
```

## 2. 状态模型
**页面级**：`loading → ready(tab) → error(retry)`。
**会话业务态**（映射 A17 `status` 枚举）：
| 契约态 | 展示 | 可执行动作 |
|--------|------|-----------|
| created | 已创建，待开场 | 进入对话 |
| in_progress | 面试进行中 | 作答/结束 |
| completed | 已完成 | 查看报告/重跑 |
| abandoned | 已放弃 | 重新创建 |

**配额子态**：`dailyLimit`(套餐值，专业版=10) / `used` / `remaining`；`remaining<=0`→升级引导。

**报告维度态**（A19 `dimensions`，4 维固定）：
`回答完整性 / 技术准确性 / 结构化表达 / 与岗位匹配度`，`rawScore` ∈ 1–5，`degradeFlag`(bool,nullable)。

## 3. 复用决策
- **复用（设计系统/U1–U5）**：AppShell、Tabs、Card、Badge、Dialog、Skeleton、ErrorState、Toast、Button 变体、状态色点。
- **新增（仅 3 个）**：
  - `SessionChat` —— 对话气泡容器 + `aria-live` 播报。
  - `EvalRadarLite` —— 4 维度 1–5 条形可视化（非雷达图，更轻、更读屏友好）。
  - `CameraPiP` —— **纯本地占位框**（明确"不参与评估/不录制/不上传"，绝不调用真实 `getUserMedia` 上传），满足 PRD §685 的安全定义。
- **模式复用**：Dialog/Toast/撤销窗口沿用 U3/U5 安全交互基线；手风琴单卡展开沿用 PRD §641 交互。

## 4. UI 字段 ↔ 契约字段映射表
| UI 字段 | 契约来源 | 说明 |
|---------|----------|------|
| 题集标题/题量/难度/标签 | A16 `questionSets[]{setId,title,questionCount,difficulty,tags}` | 备战展示 |
| 模拟作答入口 | A16→A17 `questionSetId?` | 预选 |
| 会话标识 | A17 `sessionId` | 写 |
| 会话状态 | A17 `status` | 状态机 |
| 面试类型/岗位/模式 | A17 `jobId?,mode(enum text|voice)` | SetupPanel |
| 作答内容 | A18 `answer(text|audioRef)` + `questionId` + `asrProvider?` | 写 |
| 作答接收/即时分 | A18 `accepted(bool)` + `score(0-1,nullable)` | 读 |
| 综合分 | A19 `overallScore(0-100)` | 报告头部 |
| 维度分 | A19 `dimensions[]{dim,rawScore(1-5),reason,score?}` | EvalRadarLite |
| 反馈/兜底/入口 | A19 `feedback` + `degradeFlag?` + `appealEntry?` + `rerunEntry?` | 报告尾部 |

## 5. 关键交互状态流转（模拟面试 + 报告）
```
[SetupPanel] --开始面试--> POST A17 --200--> status=created→in_progress
   └─ 进入 SessionChat，AI 开场白
[SessionChat] --发送(A18 answer)--> accepted + (score?) --> AI 评估/追问气泡
   ├─ 麦克风拒 → 自动纯文本模式
   ├─ 断网 → 保留上下文，恢复续答
   └─ 结束面试 --> GET A19 report --> status=completed
[报告 View] overallScore + 4 维度 + feedback；degradeFlag=true→"题库兜底"提示
   └─ 申诉/重跑(appealEntry/rerunEntry 占位)→v2
每日配额 remaining<=0 → 升级引导 + 仅允许看历史报告
```

## 上游引用
- 需求/验收/边界：`design/ui/roles/U6-pm.md` §2（R1–R8）、§3（AC1–AC5）、§4（异常场景）。
- 设计基线：`design/ui/00-design-system.html`（token）、`01-app-shell.html`（壳）、`ia-nav.md`（导航位置=侧栏"面试"）。
- 契约：`external-api.registry.json` A16-A19 + 四个 response schema。
- 复用范本：`screens/U5-adapter.html`（Card/Dialog/Toast）、`U3-applications.html`（安全交互基线）。

## 下游交付
工程师（`U6-interview.html` + `interaction-U6.md`）请读：§1 组件树（DOM 结构）、§2 状态模型（会话 FSM + 配额 + 4 维度）、§3 复用决策（仅新增 3 组件）、§4 字段映射表（UI 字段严格来自此表）、§5 流转。
