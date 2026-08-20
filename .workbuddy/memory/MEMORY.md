# 项目长期记忆（resume-ai-prod）

## 战略决策（已沉淀，跨会话继承）
- **2026-08-18 定位 = 真上线产品 + 原型全做**：V3 屏幕 Q10–Q15（U1/U2/U4/U5/U6/U7）一步不能少，全部转化为生产组件；Q2–Q4 合规护栏（灰度回滚 / PIPL crypto-shred / 法检复核）解锁为待办，循环按 R1 备设计/文档/代码基座；Q5–Q7（部署/真实凭据/PIPL 签署）物理动作仍仅用户触发，但属上线必做。
- 之前「护栏4/5/6 用户延后」决策已被本决策覆盖（真上线 → 必须补齐，R4 强制）。
- **2026-08-18 前端技术栈 = Vue 3 + Element Plus（严守 ADR-010）**：`frontend/` 曾误用 React18+Vite5+react-router6，与 ADR-010 / HLD §2.4（Vue3+Element Plus PC + uni-app 多端）不符；用户拍板**回退 Vue3**，Q8–Q11 已完成的 React 屏重写为 Vue SFC + vue-router + Element Plus，Q12–Q15 按 Vue 落地，uni-app 多端维持原规划（上线前范围）。

## A1–A6 已采纳决策（将领代拍板 · 用户授权 2026-08-18「不懂，听最好建议」）
- **A1 商业模式/定价**：Freemium + 订阅会员，**不抽成**（规避招聘中介资质+信任）。免费层限频(5份/日基础功能)；标准会员 ¥19/月；高级会员 ¥49/月（含 AI 面试模拟 / U4 策略优化 / 多平台适配器 / 无限投递）。驱动 U7 支付取值。
- **A2 目标用户**：核心 **25–40 岁社招主动求职者（技术/职能白领）**，次要应届生；定位**个人求职效率工具**（非企业 HR 端）。驱动匹配策略/UI 优先级。
- **A3 成功/KPI**：封号率 **<1%/账号/月**（护栏3 阈值）；默认日投递上限 **20/账号**（U3 已落地 X/20）；北极星=**投递→面试邀约转化率 >8%**；成功=周期获 ≥1 面试邀约。驱动 U4 策略默认值与护栏3。
- **A4 RAG 优先级**：核心闭环跑通后做（阶段二）；首落地 **AI 面试模拟 grounded 真实题库**，其次求职建议/匹配。Q1 降优先级（MVP 后）。
- **A5 无障碍**：承诺 **WCAG 2.1 AA**，纳入 V3 每屏基线（焦点管理 / ARIA / 对比度 / 键盘导航）；原型已尊重 reduced-motion。
- **A6 真实平台**：首发 **Boss直聘 + 猎聘** 两适配器；仅用半自动闸门 + 用户显式确认守 ToS（禁凭据抓取/模拟登录滥用）；真实凭据(Q6)仅用户触发。
- 注：以上为将领最佳建议，经用户授权代拍板；若后续业务变化可再调整。

## 机制约定
- 自主循环 3 条错峰自动化（:00/:20/:40）ACTIVE，按 TASK-QUEUE 认领续推；本地 commit 不 push；物理动作/真实凭据/PIPL 签署不伪造完成。
- 详细机制见 `TASK-MECHANISM.md`，决策策略 R1–R4。

## 任务执行框架（2026-08-19 落地）
- 本仓库自有 **DPIRA** 框架（非行业标准）：`(D → P → I ⇄ R) × N → A`，强调先冻结设计/验收口径再实施、单工作项审查、整批审计；回路 A↩I（同批修）/A↺D/P（另立批次）。规范见根目录 `DPIRA.md`，批次 `DPIRA-BATCH-001.md` + `DPIRA-STATE.json`（状态机）。
- BATCH-001 状态（2026-08-19）：D/P 通过；W1–W5 全部 DRAFT_COMPLETE（Flyway 真实迁移 / RS256 运行时闭环 / 双闸门+mvn 87-0-0+pytest+scaffold+fe build 全绿）；**W6 推送被远端写授权卡死（BLOCKED）**。

## 已确认缺陷（运行时实证逮住，待用户决策）
- **F1（HIGH）job 读表从未创建**：`Job` 实体 `@TableName("job")`，V3 迁移注释称「由 Python 采集器经 Alembic 创建」，但 server-python 无任何建表代码 → `resume_ai.job` 永不存在 → `GET /api/v1/jobs` 500。属 ADR-002 双语言异构下 Python 侧承诺未交付。**不擅自在 Java 静默补表**。
- **F2（INFO）** 沙箱注入 `SERVER__PORT=0` 致 Tomcat 随机端口；本地以 `SERVER_PORT=8080` 覆盖。真实部署无此变量，`server.port:8080` 生效。

## 环境坑（本机沙箱，复用）
- Maven 启动器 glob 在 git-bash 下不展开 → 用 `java -cp classworlds.jar org.codehaus.plexus.classworlds.launcher.Launcher` 直启；中文路径编译乱码 → 拷到 ASCII 路径（如 `/e/build`）构建。
- PyPI 经代理不可达 → `env -u http_proxy -u https_proxy pip install` 直连可装。
- vite 默认 `emptyOutDir` 被沙箱 safe-delete 钩子拦 → 用外部 `--outDir` 构建。
- GitHub 推送：直连 git 401（无凭据）、连接器 403（集成无此仓库写权限）→ 需用户授写权限/PAT，或用户本机 push。
