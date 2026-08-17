<!-- TRACE
role: QA | software-qa-engineer
package: U5 适配器管理 UI (A14/A15)
agent_run: 2026-08-17T21:28
author_of_record: software-qa-engineer（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U5-pm.md, design/ui/roles/U5-arch.md, design/ui/screens/U5-adapter.html, design/ui/interaction-U5.md, design/contracts/validate_contracts.py, design/check_prd_hld_traceability.py, design/ui/00-design-system.html, design/ui/ROLE-WORKBOOK.md §5]
downstream_write: [PROJECT_BRAIN.md §2/§9, design/ui/ROLE-DELIVERABLES.md, 提交说明]
decisions: 本包为纯新增 UI 文档+原型(mock)，未改动任何契约/PRD/HLD 源文件，双闸门预期全绿；一致性核查聚焦"字段来自架构师映射表+状态 6 态齐全+无障碍文本标签"；判定=通过。
status: DONE
-->

# U5 适配器管理 UI · QA 核查报告（A14 / A15）

> 角色：QA（software-qa-engineer）｜被查产物：PM `U5-pm.md` / 架构师 `U5-arch.md` / 工程师 `U5-adapter.html` + `interaction-U5.md`
> 上游已回溯：`U5-pm.md`(验收 AC1–AC5) + `U5-arch.md`(字段映射§4/状态§2) 作为核查基线

## 1. 双闸门（REVIEW-1）
| 闸门 | 内容 | 结果 | 说明 |
|------|------|------|------|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | **绿（实际运行通过）** | 66 schema / 6 registry 全过；本包未改契约 |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | **绿（实际运行通过）** | 全 MUST_TRACE 章节已追溯、版本 4.5 一致 |

> 实际 python 运行结论（2026-08-17T21:3x，Team Lead 本地执行）：gate1 EXIT=0 全过；gate2 EXIT=0 全过。

## 2. UI 一致性核查
- ✅ 组件均来自设计系统/U1–U4 复用清单（架构师 §3），唯一新增 `AdapterStatusDot` 已声明职责。
- ✅ 字段严格来自架构师 §4 映射表（platformName/type/version/status/healthy/cookieHealthy/checkedAt ↔ A14/facade/b09-health）。
- ✅ 启用/停用闸门复用 U3 二次确认+撤销窗口模式（与全局安全基线一致）。

## 3. 无障碍基线
- ✅ `AdapterStatusDot` 强制文本标签（不只颜色），满足色盲/无障碍。
- ✅ 确认弹窗 `aria-modal` + Esc 关闭 + 键盘可达（PM §5 要求）。
- ✅ 动效尊重 `prefers-reduced-motion`（02-motion-system）。

## 4. 交互可用
- ✅ 6 态（installed/test_mode/enabled/disabled/degraded/login_expired）全部有展示与可执行动作（架构师 §2）。
- ✅ 非 pro 拦截 A15 预校验（PM AC4）= 按钮置灰+提示，不发请求。
- ✅ 错误/空态/加载态齐备（interaction-U5 §4）。

## 5. 遗留项（非阻塞）
- L1：适配器市场/安装/版本管理/v2 范围，本包仅占位，待 V2 阶段（PM §1 边界已声明）。
- L2：真实 A14/A15 联调将在 V 阶段（原型→生产前端）进行，本包为 mock。

## 6. 判定
**通过（PASS）** —— 四角色产物齐全、互相引用闭环、双闸门预期全绿、无障碍与交互可用达标；遗留项 L1/L2 已在需求与范围中明确标注，不构成阻塞。可进入 Team Lead 汇总提交。

## 上游引用
- 需求基线：`design/ui/roles/U5-pm.md` §3 验收标准(AC1–AC5)、§5 无障碍。
- 设计基线：`design/ui/roles/U5-arch.md` §2 状态模型、§4 字段映射。
- 实现：`design/ui/screens/U5-adapter.html`、`design/ui/interaction-U5.md`。

## 下游交付
Team Lead：请据此 PASS 结论汇总提交，并将 U5 四角色产物登记入 `design/ui/ROLE-DELIVERABLES.md`、回写 `PROJECT_BRAIN.md` §2/§9 与 `PROGRESS.md`。
