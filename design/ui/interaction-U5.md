<!-- TRACE
role: Engineer | software-engineer
package: U5 适配器管理 UI (A14/A15)
agent_run: 2026-08-17T21:27
author_of_record: software-engineer（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U5-pm.md(§2/§3/§5), design/ui/roles/U5-arch.md(§1/§2/§3/§4/§5), design/ui/screens/U3-applications.html(ConfirmDialog/撤销窗口范本), design/ui/02-motion-system.html, design/ui/ROLE-WORKBOOK.md §4]
downstream_write: [design/ui/screens/U5-adapter.html, design/ui/roles/U5-qa.md]
decisions: 原型用 mock 数据(6 态各一例)，不接真实 A14/A15；启用闸门复用 U3 二次确认+10s 撤销；AdapterStatusDot 为唯一新增组件；全部交互纯前端态，无凭据/部署/真实 PII。
status: DONE
-->

# U5 适配器管理 · 交互规格（A14 / A15）

> 配套原型：`design/ui/screens/U5-adapter.html`（可交互 HTML，mock 数据，不接真实后端/凭据）
> 上游：PM `U5-pm.md` + 架构师 `U5-arch.md` ← 本文件严格按其字段映射表(§4)与状态模型(§2)实现

## 1. 屏幕目标
"平台管理"页：查看已接入适配器状态/健康、显式启用/停用（A14/A15），控制本机 Agent 在哪些平台投递。安全模型同 U3——任何启用/停用由用户主动确认。

## 2. 信息结构
- 顶栏（AppShell 复用）：标题"平台管理"+ 健康总览（X/Y 正常）。
- Section 首期：AdapterCard 列表（BOSS/猎聘/前程/智联/拉勾），每卡含 `AdapterStatusDot` + MetaRow + HealthSummary + ActionBar。
- Section 后续：未安装平台占位 + "安装适配器"(灰，v2)。
- ConfirmDialog（复用 U3）：启用/停用二次确认，含平台名+目标态+10s 撤销窗口。
- Toast：操作结果反馈。

## 3. 关键交互（对应 PM R1–R7）
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 列表加载 | 进入页 | 骨架→mock 卡片按首期/后续分组 | A14 GET /adapters |
| 启用闸门 | 点"启用" | 二次确认(平台名+将变 enabled)→前端态 enabled+Toast+10s 撤销 | A15 POST {enabled:true} |
| 停用警告 | 点"停用" | 警告确认→前端态 disabled | A15 {enabled:false} |
| 登录引导 | 状态 login_expired | 显示"需登录"+「登录」→仅弹 loginUrl 引导(不代填) | Adapter.LoginGuidance |
| 批量 | 多选 | 工具栏"批量启用/停用"聚合确认 | A15×N |
| 重试 | 错误态 | 「重试」重渲染 mock | — |

## 4. 状态 / 转场 / 空态 / 错误
- 加载：Section 内 Skeleton。
- 空态：首期无适配器→"暂无可管理适配器，去适配器市场(v2)"。
- 错误：mock 注入失败按钮→ErrorState+"重试"。
- 6 态色点文本标签齐全（无障碍）。

## 5. 与契约一致性
- `status` 严格用 6 态枚举；`platformName/type/version` 来自 facade；健康来自 `b09-health`。
- 启用/停用仅前端态模拟 A15 响应 `{adapterId,status}`，不真发请求（mock）。

## 6. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-3：原型仅 mock、不接真实后端/凭据/部署，**不触发红线**，自动提交。

## 上游引用
- PM：`design/ui/roles/U5-pm.md` §2/§3/§5（交互清单/验收/无障碍）。
- 架构师：`design/ui/roles/U5-arch.md` §1/§2/§3/§4/§5（组件树/状态/复用/字段映射/闸门流转）。
- 范本：`design/ui/screens/U3-applications.html`（ConfirmDialog+撤销窗口）。

## 下游交付
QA（`U5-qa.md`）请核查：本文件 §3 交互 vs PM R1–R7、§5 字段 vs 架构师 §4 映射表、§6 红线判定；并跑双闸门。
