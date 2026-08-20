# DPIRA · 知识库自有任务执行框架（非行业标准缩写）

> 来源：用户于 2026-08-19 指定作为本仓库推进至「部署就绪 / 合并 master」的驱动框架。
> 核心思想：**先把设计与验收口径冻结，再实施；每个工作项分别审查，全部完成后做一次整批审计。**

---

## 0. 一句话定义

```
(D → P → I ⇄ R) × N → A
```

- **D** Design/Define — 设计与定义
- **P** Plan Review — 设计审查（实施前闸门）
- **I** Implementation — 实施
- **R** Implementation Review — 实施审查（单工作项）
- **× N** — 本批次有 N 个宏观工作项（feature / 实现批次，**不拆到函数/文件/handler 级**）
- **A** Audit — 批级审计（整批 review + 测试 + 构建 + 运行时验证 + 交付回执）

---

## 1. 各阶段职责、产物与出口闸门

### D — Design / Define（设计冻结）
- **职责**：理解需求、代码库、约束；冻结**目标 / 范围 / 依赖 / 禁止项 / 写入边界 / 技术协议 / 可机器验证的验收口径**；登记已知偏差与 truth gap。
- **产物**：`DPIRA-BATCH-XXX.md`（冻结件：目标、范围 in/out、禁止项、依赖、验收口径、工作项 W1..WN、已登记偏差）。
- **出口闸门（进 P）**：冻结件存在且自洽；验收口径逐条可机器验证；与既有已采纳决策（ADR-001/002/004/010、PROJECT_BRAIN §3 核心约束、护栏 1/2/3）无冲突；未知项已显式登记为待决，未假装已覆盖。

### P — Plan Review（设计审查）
- **职责**：在实施前独立审查 D 冻结件——范围是否完整、依赖是否明确、验收是否可判定、是否与既有决策冲突。
- **产物**：P 阶段审查结论（通过 / 打回 D），写入 `DPIRA-BATCH-XXX.md`。
- **出口闸门（进 I）**：审查结论为「通过」。任一重大冲突 → 打回 D（不进入实施）。

### I — Implementation（实施）
- **职责**：按冻结设计**连续实施**；只做廉价静态检查与写入前检查，不在此阶段做整批判定。
- **出口（进 R）**：工作项实现完成、随附单测/文档到位。

### R — Implementation Review（实施审查）
- **职责**：对**单个工作项**审查 diff、静态结果、允许的定向快速测试；发现问题 → 回到 I 修正。
- **回路**：`I ⇄ R`（同一工作项内循环，直到该工作项 `draft_complete`）。
- **出口（工作项达 draft_complete）**：该工作项验收口径逐条通过（机器验证）；遗留偏差已登记。

### A — Audit（批级审计）
- **职责**：所有工作项达 `draft_complete` 后，统一做整批 **review + 测试 + 构建 + 运行时验证 + 交付回执**。
- **产物**：批级审计结论 + 交付回执（写入 `DPIRA-BATCH-XXX.md` 终稿 + 回写 `PROJECT_BRAIN.md` / `TASK-QUEUE.md` / `TASK-LOG.md` / `GO-LIVE-LOG.md`）。
- **回路（两种）**：
  - **普通实施缺陷 → `A ↩ I`**：同批次集中修复，修完只重跑 A，**不重走 D/P**。
  - **系统性/方向性问题 → `A ↺ D/P`**：设计/范围/基本假设有问题，另立批次重新设计与审查。

---

## 2. 状态机

### 批次状态
```
DEFINING → PLAN_REVIEW → IMPLEMENTING → AUDITING → DONE
                  │              │
                  └─(打回)──→ DEFINING
```
- `AUDITING` 失败普通缺陷 → 回 `IMPLEMENTING`（A↩I）。
- `AUDITING` 失败系统问题 → 回 `DEFINING`（A↺D/P，另立批次）。

### 工作项状态
```
TODO → IN_PROGRESS → DRAFT_REVIEW → DRAFT_COMPLETE
                              │
                              └─(问题)──→ IN_PROGRESS (I⇄R)
```
- 全部工作项 `DRAFT_COMPLETE` 方可进入 `AUDITING`。

### 状态词汇（与既有机制对齐）
- 沿用 `TASK-QUEUE.md` 状态：`待办 / 进行中 / 已完成 / 阻塞(待用户拍板) / 阻塞(物理动作·用户)`。
- DPIRA 新增：`DEFINING / PLAN_REVIEW / IMPLEMENTING / AUDITING / DONE`（批次级）+ `DRAFT_COMPLETE`（工作项级，= 通过 R 审查、待批级 A）。

---

## 3. 与既有仓库机制的关系（不重复造轮子）

| 既有物 | 在 DPIRA 中的角色 |
|---|---|
| `PROJECT_BRAIN.md` §3 核心约束 / §4 已固化决策 | D 阶段的「禁止项 / 写入边界」权威来源 |
| ADR-001/002/004/010、HLD、PRD | D 阶段设计符合性核对基准（R4 标准优先） |
| 双闸门（契约校验 + PRD/HLD 追溯） | P 阶段「验收可判定」与 A 阶段「批级测试」的硬门禁 |
| `TASK-QUEUE.md` / `TASK-LOG.md` / `TASK-ALERTS.md` | DPIRA 工作项与状态回写的落点（阶段②分发 / ④状态回传 / ⑤告警） |
| `scripts/dpira.py`（本框架 CLI） | 状态驱动：读/写批次与工作项状态，出审计快照 |
| 护栏 1/2/3（已就位） | 贯穿 I/R/A，不得削弱 |
| 护栏 4/5/6（用户 2026-08-17 延后） | 不在本批次范围，如实标注「用户延后」，不伪造 |

---

## 4. 诚实边界（贯穿全框架，不可逾越）

1. **不伪造验证**：未实证的事（如「已在真实 MySQL 跑通」「CI 已绿」）不得写进交付物；未跑的验证显式标「未验证 / 待用户在具备 X 的环境执行」。
2. **偏差显式登记**：发现设计符合性偏差 / truth gap，立即登记为「待决/偏差」，不隐藏、不假装已覆盖（呼应 PROJECT_BRAIN §5 诚信纪律）。
3. **物理动作仅用户**：部署生产 / 真实凭据 / 上线开关 / PIPL 签署 → 标「待用户触发」，循环不代做。
4. **不删用户文件**：本框架执行过程不删除用户个人目录文件；空间不足时改用「重定向到 E:」等无删除方案。
5. **不直推保护分支**：经 GitHub 连接器推到非保护分支 → 开 PR → gates 绿 → 合并 master；以远端 API（ls-tree/contents/commit status）为铁证。

---

## 5. `scripts/dpira.py` 用法（零依赖）

```bash
python scripts/dpira.py init <batch_id>            # 初始化批次状态 JSON
python scripts/dpira.py status                     # 打印批次 + 工作项状态树
python scripts/dpira.py phase <DEFINING|PLAN_REVIEW|IMPLEMENTING|AUDITING|DONE>
python scripts/dpira.py item <Wx> <TODO|IN_PROGRESS|DRAFT_REVIEW|DRAFT_COMPLETE>
python scripts/dpira.py audit <PASS|FAIL_A_I|FAIL_A_DP> [note]
python scripts/dpira.py snapshot                    # 导出审计快照（供 A 阶段结论）
```
- 状态存于 `DPIRA-STATE.json`（纳入 git，本地不 push 外）。
- 所有命令只读写该 JSON + 打印，无副作用于代码库。
