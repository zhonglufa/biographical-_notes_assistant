# 角色交接规范（Handoff Spec）

多角色流水线中，每个角色是**独立 agent 会话**，彼此不共享对话上下文，只通过本项目文件传递信息。本规范定义每角色的「输入 / 产出 / 下游读取」，避免各写各的、对不上。

## 通用约定
- **状态源**：`PROJECT_BRAIN.md`（阶段与包进度唯一权威）
- **包锁**：`design/ui/.u-claims.json`（认领即写 `{包名: ISO时间戳}`，<40min 过期可 reclaim，防 3 条自动化重复认领）
- **设计基线**：`00-design-system.html` / `01-app-shell.html` / `ia-nav.md` / `02-motion-system.html`
- **范本**：`screens/U1-resume.html … U4-strategy.html` + `interaction-U1~U4.md`
- **契约**：A01–A25（`design/contracts/` + HLD §10）

## 角色职责与交接物

### PM（`software-product-manager`）
- **输入**：PRD 对应 A 章节 + U 阶段规范 + 设计系统
- **产出**：`design/ui/roles/Ux-pm.md`（交互需求清单 + 验收标准 + 边界/异常场景）
- **下游**：架构师读它定结构；工程师读它定行为

### 架构师（`software-architect`）
- **输入**：PM 产出 + 设计系统 + 契约 A01–A25
- **产出**：`design/ui/roles/Ux-arch.md`（组件树 + 状态 + 复用决策 + 与契约字段映射）
- **下游**：工程师读它实现

### 工程师（`software-engineer`）
- **输入**：PM + Arch 产出 + U1–U4 范本 + 契约
- **产出**：`screens/Ux-*.html`（可交互原型，mock 数据）+ `interaction-Ux.md`（交互规格）；**V 阶段**转为接入真实契约 API 的生产前端代码（本地不部署）
- **下游**：QA 读它核查

### QA（`software-qa-engineer`）
- **输入**：工程师产出 + 双闸门 + 设计系统 + 契约
- **产出**：`design/ui/roles/Ux-qa.md`（核查报告：双闸门结果 / UI 一致性 / 无障碍基线 / 交互可用 / 遗留项）
- **下游**：Team Lead 汇总结论；不通过退工程师修

### DevOps（`general-purpose` 代理，O 阶段；SoftwareCompany 体系无 DevOps agent）
- **输入**：`githooks/pre-commit` 三闸门 + `.github/workflows/dual-gate.yml` + `LightweightMonitor`
- **产出**：CI/CD 配置扩写 + 轻量 CD 脚本 + 监控接入代码（**不真部署**）
- **下游**：Team Lead 复核；部署上线须用户

## Team Lead（主 agent）
- 编排四角色 → 汇总 → 过 REVIEW-1/2 闸门 → 本地 commit（提交信息含四角色贡献摘要）→ 回写 `PROJECT_BRAIN.md` §2/§7 + 当日日志 + `PROGRESS.md`。

## 交接纪律
1. 每个角色**只写自己职责范围内的文件**，不越权改他人产出。
2. 下游角色**必须先读上游产出文件**再动手，禁止凭空假设。
3. 任何角色发现上游需求矛盾，在日志记 `↻ 需 PM/Arch 澄清` 并暂停该包，由 Team Lead 协调，不擅自改需求。
4. 文件命名统一：`roles/Ux-{pm|arch|qa}.md`、`screens/Ux-*.html`、`interaction-Ux.md`（x = 包号）。
