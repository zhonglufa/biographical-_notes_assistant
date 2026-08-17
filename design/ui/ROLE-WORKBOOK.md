<!-- TRACE
role: Team Lead | 角色工作手册(规范)
package: 多角色流水线 · 全局规范
agent_run: 2026-08-17T20:50
author_of_record: Team Lead (主 agent)
upstream_read: [PROJECT_BRAIN.md §8/§9, design/ui/ROLES-HANDOFF.md, design/ui/00-design-system.html, design/contracts/]
downstream_write: [design/ui/ROLE-DELIVERABLES.md(交付台账), 各 Ux 包 roles/Ux-{pm|arch|qa}.md]
decisions: 把"多角色流水线"从流程描述升级为可审计的"工作清单+要素+产物模板+互相参考+留痕"规范；U5 起每个包必须四角色各出一份带 TRACE 头的产物，且互相显式引用。
status: DONE
-->

# 角色工作手册（Role Workbook）

> 本手册定义多角色流水线中**每个角色的具体工作清单、产物要素、文件模板、互相参考方式与工作留痕规范**。
> 目的：让"软件团队每个人的工作"可审计——**谁、在什么包、读了什么、产出了什么、交付给谁、留下了什么痕迹**，一目了然。
> 配套：`ROLES-HANDOFF.md`（交接纪律）、`ROLE-DELIVERABLES.md`（交付台账，按包登记四角色产物与状态）。

---

## 0. 五个角色与接力链

```
PM (software-product-manager)
   │  读 PRD + 契约 → 产 Ux-pm.md
   ▼
架构师 (software-architect)
   │  读 Ux-pm.md + 设计系统 → 产 Ux-arch.md
   ▼
工程师 (software-engineer)
   │  读 Ux-pm.md + Ux-arch.md → 产 Ux-*.html + interaction-Ux.md
   ▼
QA (software-qa-engineer)
   │  读上述全部 → 产 Ux-qa.md（不过退工程师修）
   ▼
Team Lead (主 agent)
   │  汇总四角色产物 → REVIEW 闸门 → 本地 commit → 更 PROJECT_BRAIN/台账/PROGRESS
```

**每个角色都是独立 agent 会话**，彼此不共享对话上下文，只通过本手册定义的文件 + TRACE 头传递信息。

---

## 1. 通用留痕规范（所有产物必须带 TRACE 头）

每个产物文件**第一行必须是 HTML 注释 TRACE 块**（人/脚本都可解析），字段固定：

```
<!-- TRACE
role: <PM|Architect|Engineer|QA|Team Lead> | <agent 类型>
package: <Ux 包名 + 对应契约编号，如 U5 适配器管理 UI (A14/A15)>
agent_run: <ISO 时间，本角色本次执行的时刻>
author_of_record: <角色名>
upstream_read: [<本角色实际读取的上游文件列表，越具体越好>]
downstream_write: [<本角色产出的、供下游读取的文件列表>]
decisions: <本角色在本包做的关键判断/取舍，逐条>
status: <DRAFT|REVIEW|DONE|BLOCKED>
-->
```

**留痕三要素**（缺任一视为不合格，QA 退回）：
1. `upstream_read` 必须真实列出本角色读过的文件（不能空着"凭印象"）；
2. `downstream_write` 必须列出本角色交付给下游的文件；
3. 正文必须有 `## 上游引用` 与 `## 下游交付` 两个小节，写明具体文件路径与对应章节/行，实现"互相参考"。

---

## 2. PM（产品经理）· 工作清单与产物

**工作清单（逐条）**
1. 读取 PRD 中本包对应 A 编号章节 + 对应契约 schema（`design/contracts/`）。
2. 提炼本包页面的**目标与范围**（含"不做什么"边界）。
3. 拆解**交互需求清单**：每条 = 触发 → 行为 → 反馈 → 异常/边界。
4. 写**验收标准**（可人工/机器验证，对应契约字段）。
5. 列出**无障碍 + 动效**要求（参照 `02-motion-system.html`，尊重 `prefers-reduced-motion`）。
6. 在 `## 下游交付` 显式指名架构师要读的自己这份文件。

**产物要素**：目标/范围、交互需求清单、验收标准、边界异常场景、契约字段对应、无障碍与动效要求。
**产物文件**：`design/ui/roles/Ux-pm.md`
**上游**：PRD、契约 Axx、设计系统。**下游**：`Ux-arch.md`、`Ux-*.html`、`interaction-Ux.md`。

---

## 3. 架构师（Architect）· 工作清单与产物

**工作清单（逐条）**
1. 读取 PM 的 `Ux-pm.md`（**必须先读，不凭空假设**）。
2. 读取设计系统（`00-design-system.html`/`01-app-shell.html`/`ia-nav.md`）+ 契约字段。
3. 产出**组件树**（页面→区块→组件，命名复用设计系统）。
4. 产出**状态模型**（加载/空/错误、各业务状态，映射契约返回字段）。
5. 写**复用决策**（哪些用既有组件、哪些新增、新增职责）。
6. 写**UI 字段 ↔ 契约字段映射表**。
7. 写关键交互的**状态流转**（如确认闸门状态机）。
8. `## 上游引用` 指向 `Ux-pm.md` 具体章节；`## 下游交付` 指向工程师要读的自己这份文件。

**产物要素**：组件树、状态模型、复用决策、字段映射表、状态流转。
**产物文件**：`design/ui/roles/Ux-arch.md`
**上游**：`Ux-pm.md`、设计系统、契约。**下游**：`Ux-*.html`、`interaction-Ux.md`。

---

## 4. 工程师（Engineer）· 工作清单与产物

**工作清单（逐条）**
1. 读取 `Ux-pm.md` + `Ux-arch.md`（**两者都读，缺一不可**）。
2. 读取 U1–U4 范本（`screens/U1~U4*.html` + `interaction-U1~4.md`）对齐风格。
3. 实现**可交互 HTML 原型**（`screens/Ux-*.html`，mock 数据，带 TRACE 头）。
4. 写**交互规格**（`interaction-Ux.md`：状态、动效、异常、无障碍）。
5. UI 字段严格来自 `Ux-arch.md` 的映射表 + `Ux-pm.md` 的需求。
6. `## 上游引用` 指向 pm+arch 文件；`## 下游交付` 指向 QA 要核查的文件。

**产物要素**：可交互原型（mock）、交互规格、字段来源声明。
**产物文件**：`design/ui/screens/Ux-*.html` + `design/ui/interaction-Ux.md`
**上游**：`Ux-pm.md`、`Ux-arch.md`、范本。**下游**：`Ux-qa.md`、最终交付。

---

## 5. QA（测试）· 工作清单与产物

**工作清单（逐条）**
1. 读取工程师的 `Ux-*.html` + `interaction-Ux.md`。
2. 回溯读取 `Ux-pm.md`（验收标准）+ `Ux-arch.md`（字段映射）作为核查基线。
3. 跑**双闸门**（`validate_contracts.py` + `check_prd_hld_traceability.py`），记录绿/红。
4. 核查 **UI 一致性**（与设计系统/IA 对齐）、**无障碍基线**、**交互可用**（锚点/动效/异常）、**响应式三端**（375/768/1280 渲染、无横向溢出、无重叠、按钮≥40px 可点、模态≤90vw，依据 `UI-SELFCHECK.md §3`，逐条 PASS/FAIL 写入 `Ux-qa.md`）。
5. 产出**核查报告**：结论（通过/退回）+ 遗留项清单。
6. 不通过 → 在报告写 `↻ 退工程师修：<具体项>`，Team Lead 据此退回。
7. `## 上游引用` 列出全部被查文件；`## 下游交付` 指向 Team Lead 汇总。

**产物要素**：双闸门结果、UI 一致性结论、无障碍结论、交互可用结论、遗留项、通过/退回判定。
**产物文件**：`design/ui/roles/Ux-qa.md`
**上游**：`Ux-pm.md`/`Ux-arch.md`/`Ux-*.html`/`interaction-Ux.md`/双闸门。**下游**：Team Lead 汇总、最终交付。

---

## 6. Team Lead（主 agent）· 工作清单与产物

**工作清单（逐条）**
1. 每轮读 `PROJECT_BRAIN.md` §2/§9 + 当日日志末条，做续做自检。
2. 认领 ONE 包（写 `.u-claims.json` 锁）。
3. 依次派发 PM→Arch→Eng→QA 四角色（各自独立 agent）。
4. 汇总四角色产物，过 REVIEW-1（双闸门）/REVIEW-2（偏离自审）/REVIEW-3（红线）。
5. 本地 commit（提交信息含四角色贡献摘要 + REVIEW 结论）。
6. 更新 `PROJECT_BRAIN.md` §2/§9、`ROLE-DELIVERABLES.md` 台账、`PROGRESS.md`、当日日志、automation memory。

**产物要素**：提交、状态回写、台账登记。
**产物文件**：git commit + `ROLE-DELIVERABLES.md` 增行 + `PROJECT_BRAIN.md` 更新。
**上游**：四角色产物。**下游**：用户最终交付报告。

---

## 7. 包级交付台账（工作留痕总账）

`design/ui/ROLE-DELIVERABLES.md` 按包登记，每行一個包，列：包名 / 契约 / PM / Arch / Eng(screen) / Eng(interaction) / QA / 双闸门 / 状态。
- U1–U4：单 agent 时代产物（仅 screen+interaction，**无四角色拆分**，如实标注"legacy"）。
- **U5 起：必须四角色齐全且互相引用**，否则 Team Lead 不 commit。

---

## 8. 交接纪律（重申，违反即退回）
1. 每角色**只写自己职责文件**，不越权改他人产物。
2. 下游角色**必须先读上游产物再动手**，禁止凭空假设（TRACE 的 `upstream_read` 是证据）。
3. 发现上游矛盾 → 日志记 `↻ 需 PM/Arch 澄清` 并暂停该包，由 Team Lead 协调。
4. 文件命名：`roles/Ux-{pm|arch|qa}.md`、`screens/Ux-*.html`、`interaction-Ux.md`。

---

## 9. 响应式与 UI 自查规范（提交前必过闸门）

- **权威文件**：`design/ui/UI-SELFCHECK.md`——含自我反思（为什么之前乱/没响应式）、用户可用性结论、三端自查清单（§3）、防卡死派发纪律（§4）、响应式 CSS 范式（§5）。
- **设计系统源头**：`00-design-system.html §6` 已定义断点（--bp-sm:640 / --bp-md:768 / --bp-lg:1024）与"壳折叠 + 卡片堆叠"要求。
- **每个 U 屏必须**：`<style>` 末尾含对应 `@media` 块（带壳屏用 §5 上段、卡片屏用 §5 下段），覆盖 ≤768px 与 ≤480px。
- **QA 必查**：`UI-SELFCHECK.md §3` 七项（R1–R7）逐条判定，任一 FAIL 即退回工程师改，不得 commit 未过自查的屏。
- **派发纪律**：§4 的"派发后验证文件存在+重试+lead 代笔标注"为硬性规则，防止子 agent 瞬断导致"一直准备中/零产物"。
