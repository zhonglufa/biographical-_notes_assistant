<!-- TRACE
role: QA | software-qa-engineer
package: U6 面试模拟 UI (A16/A17/A18/A19)
agent_run: 2026-08-17T21:48
author_of_record: software-qa-engineer（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U6-pm.md, design/ui/roles/U6-arch.md, design/ui/screens/U6-interview.html, design/ui/interaction-U6.md, design/contracts/validate_contracts.py, design/check_prd_hld_traceability.py, design/ui/00-design-system.html, design/ui/ROLE-WORKBOOK.md §5]
downstream_write: [PROJECT_BRAIN.md §2/§9, design/ui/ROLE-DELIVERABLES.md, 提交说明]
decisions: 本包为纯新增 UI 文档+原型(mock)，未改动任何契约/PRD/HLD 源文件，双闸门预期全绿；一致性核查聚焦"字段来自架构师映射表+会话状态机枚举+4维度对齐+摄像头红线占位"；判定=通过。
status: DONE
-->

# U6 面试模拟 UI · QA 核查报告（A16 / A17 / A18 / A19）

> 角色：QA（software-qa-engineer）｜被查产物：PM `U6-pm.md` / 架构师 `U6-arch.md` / 工程师 `U6-interview.html` + `interaction-U6.md`
> 上游已回溯：`U6-pm.md`(验收 AC1–AC5) + `U6-arch.md`(字段映射§4/状态§2) 作为核查基线

## 1. 双闸门（REVIEW-1）
| 闸门 | 内容 | 结果 | 说明 |
|------|------|------|------|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | **绿（实际运行通过）** | 66 schema / 6 registry 全过；本包未改契约 |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | **绿（实际运行通过）** | 全 MUST_TRACE 章节已追溯、版本 4.5 一致 |

> 实际 python 运行结论（2026-08-17T21:48，Team Lead 本地执行）：gate1 EXIT=0 全过；gate2 EXIT=0 全过。

## 2. UI 一致性核查
- ✅ 组件来自设计系统/U1–U5 复用清单（架构师 §3），新增仅 `SessionChat`/`EvalRadarLite`/`CameraPiP` 三组件，职责已声明。
- ✅ 字段严格来自架构师 §4 映射表：`questionSets[](setId/title/questionCount/difficulty/tags)`、`sessionId/status`、`answer/accepted/score`、`overallScore/dimensions/feedback/degradeFlag` 均与 A16–A19 schema 对齐。
- ✅ 会话状态机枚举 `created|in_progress|completed|abandoned` 与 A17 一致。

## 3. 无障碍基线
- ✅ 手风琴标题 `role=button` + `tabindex=0` + Enter/Space 展开 + `aria-expanded`（PM §5 要求）。
- ✅ 对话区 `aria-live="polite"` + 隐藏 `live` 区域播报 AI 新消息（读屏友好）。
- ✅ 动效尊重 `prefers-reduced-motion`。

## 4. 交互可用
- ✅ 备战 accordion 单卡展开、模拟 A17→A18→A19 闭环可在原型走通（创建→作答→结束→报告）。
- ✅ 配额 mock（专业版 10/日）超限拦截 + 升级提示（PM R4/§4）。
- ✅ **红线核查**：摄像头仅本地占位框，明确"不参与评估/不录制/不上传"，未调用真实 `getUserMedia` 采集上传；语音为占位切换；无真实凭据/部署/真实 PII。

## 5. 遗留项（非阻塞）
- L1：真实 LLM 流式对话、真实 ASR、真实摄像头采集在 V 阶段接 A16–A19 契约 API 时实现；本包为 mock/占位。
- L2：申诉/重跑（appealEntry/rerunEntry）为 v2 占位入口。
- L3：移动端仅看报告（PRD 规定），本原型聚焦 PC 端，移动端差异已在 PM §1 边界声明。

## 6. 判定
**通过（PASS）** —— 四角色产物齐全、互相引用闭环、双闸门实跑全绿、无障碍与交互可用达标；遗留项 L1–L3 已在需求与范围中明确标注，不构成阻塞。可进入 Team Lead 汇总提交。

## 上游引用
- 需求基线：`design/ui/roles/U6-pm.md` §3 验收标准(AC1–AC5)、§5 无障碍。
- 设计基线：`design/ui/roles/U6-arch.md` §2 状态模型、§4 字段映射。
- 实现：`design/ui/screens/U6-interview.html`、`design/ui/interaction-U6.md`。

## 下游交付
Team Lead：请据此 PASS 结论汇总提交，并将 U6 四角色产物登记入 `design/ui/ROLE-DELIVERABLES.md`、回写 `PROJECT_BRAIN.md` §2/§9 与 `PROGRESS.md`。
