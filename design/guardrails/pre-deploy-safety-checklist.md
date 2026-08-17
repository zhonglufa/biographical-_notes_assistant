# 部署前安全核对清单 · 首上线安全剧本（Q17 · 护栏收口 + 防事故）

> 文档版本：2026-08-18 · v1.0（R1 自主补齐，对齐用户「确保不会生产事故发生 / 没有设计文档直接补充」）
> 关联上游：PROJECT_BRAIN §1 零生产事故 / 护栏 1–6；TASK-MECHANISM §3 R4 / §5 诚实边界；C1-RAG架构与成本方案 / C2-轻量监控接入
> 定位：**生产就绪检查单 + 首上线 runbook**。本文件为「设计/运行就绪文档」，物理部署(Q5)/真实凭据(Q6)/PIPL 签署(Q7) 仍仅用户触发；本文件使其「不事故」。
> 作者：架构师（AI 协作，全委托授权下自主推进）

---

## 0. 为什么需要本文件（背景）

循环此前已完成「生产就绪的设计 + 代码骨架 + UI 稿 + mock 测试，止于未上线」。在补齐过程中发现并修复一个**根因级隐患**：

- **护栏3（封号率/投递成功率监控）原为「孤儿代码」**：`monitor_hooks.attach_monitor()` 从未被任何入口调用，`server_app.py` 既不实例化 `LightweightMonitor` 也不挂接事件总线 → 生产环境 `apply.status.changed` 事件发射了却**没人接收**，监控「看起来有、实际收不到数据」，等同于无监控。
- 修复（2026-08-18 本轮回填）：`ServerApp` / `DeliveryOrchestrator` 构造时若拿到 `bus` 即自动创建并挂接 `LightweightMonitor`；`MatchService` 计费成功后回写 `record_llm_cost`；`DeliveryOrchestrator` 遇验证码挑战调 `record_ban`、遇失败发 `failed` 事件；`attach_monitor` 加幂等守卫防同一 monitor 被多处注入重复计数。四项指标现已全部真实流动（`test_server_app` / `test_llm_match` / `test_local_agent` 覆盖）。
- **但模块级修复 ≠ 部署级收口**：部署引导程序（bootstrap）仍须**只构造一个 `LightweightMonitor` + 一个 `EventBus`，并注入到 `ServerApp` + `DeliveryOrchestrator` + `MatchService`**，否则四个指标分散在多个 monitor 实例、snapshot 不收敛、告警失真。本文件把这条「引导程序接线契约」列为上线硬闸门。

本文件作用：把 6 道护栏 + 部署接线 + 首上线剧本固化为**可勾选的 go/no-go 闸门**，让 Q5（部署）在用户触发时按剧本走，不凭记忆、不跳步。

---

## 1. 上线硬闸门（Go / No-Go）

> 任一项为 No-Go → **禁止上线**，标 `PENDING 人工复核` 转用户/专家，循环不伪造「已部署/已合规」。

### 1.1 护栏接线闸门（代码已就位，部署须确认生效）

| # | 闸门 | 代码现状（2026-08-18） | 部署确认点（Q5 引导程序） | 触发者 |
|---|---|---|---|---|
| G1 | 双闸门 CI 本地三闸门 | ✅ `githooks/pre-commit`（gate0 版本戳/gate1 契约/gate2 PRD-HLD） | 远端 CI（`.github/workflows/ci-cd.yml`）须启用为 Required status check | 用户/运维 |
| G2 | LLM 成本硬上限+熔断 | ✅ `cost_policy.BudgetPolicy` + `llm_match.CostGuard` | 部署时配置**真实日硬上限金额**（非 DEMO ¥500） | 用户/运维 |
| G3 | 封号率监控（4 指标全活） | ✅ 四项指标已接线（见 §0） | bootstrap 须**单 monitor+单 bus 注入三组件**，否则 snapshot 不收敛 | 用户/运维 |
| G4 | 灰度开关 fail-safe | ✅ `feature_flags.py` 默认全关 + kill-switch | 首上线**默认全关**，仅必要时按场景开 | 用户 |
| G5 | PIPL crypto-shred | 🟡 `crypto_shred.py` 代码就绪，**真实 KEK/KMS 未配、律师签字未签** | 处理真实 PII 前须配 KMS + 完成 Q7 签署 | 用户/法务 |
| G6 | 法检哈希链 | 🟡 `audit_log.py` SHA256 哈希链就绪，专家复核动作未安排 | 上线前安排真实法检 Pro 复核 | 用户 |

> G5/G6 为「代码基座就绪、物理/法检动作待用户」——如实标注，不伪造「已合规」。

### 1.2 账号安全闸门（头号生产事故源）

| # | 闸门 | 要求 | 现状 |
|---|---|---|---|
| B1 | 半自动 + 用户显式确认 | 候选清单须用户确认后才执行；未确认绝不静默全自动 | ✅ `local_agent.require_confirmation` + U3 二次确认闸门 + 10s 撤销 |
| B2 | 日投递限额 | 默认 ≤20/账号（A3 KPI），免费版 30/专业版 80–100 | ✅ `DeliveryStrategy.daily_quota` + U3 限额可见 |
| B3 | 幂等去重 | 同岗不重复消耗限额 | ✅ `DeliveryOrchestrator._applied_today` |
| B4 | 验证码/封号暂停 | 遇验证码挑战立即暂停并 `record_ban` | ✅ `MockAdapter.captcha_required` → `record_ban` |
| B5 | 平台 ToS 守规 | 禁凭据抓取/模拟登录滥用；仅用官方接口 + 用户授权 | ⚠️ 真实适配器(Q6)须逐项核对 Boss/猎聘 ToS |

### 1.3 密钥与部署闸门

| # | 闸门 | 要求 | 触发者 |
|---|---|---|---|
| K1 | 密钥入 vault | 真实 API Key/凭据不落明文、不进 git | 用户 |
| K2 | CD 门控 | `scripts/cd-deploy.sh` 须 `DEPLOY_TOKEN` 才能触达生产 | 用户 |
| K3 | 不自动 push | 循环只本地 commit，绝不自动 push 远端 | 循环（已遵守） |
| K4 | 回滚预案 | `feature_flags` kill-switch + 单机器/小容器可回滚 | 用户/运维 |

---

## 2. 首上线安全剧本（Canary Runbook）

> 目标：用最小爆炸半径验证「不事故」，再逐步放量。

### 2.1 放眼前准备（用户触发 Q5 前）
1. 按 §1 全部闸门勾选 Go。
2. bootstrap 完成 §0 的「单 monitor + 单 bus 注入三组件」接线，并 `monitor.snapshot()` 打印 4 指标基线。
3. 配置真实日硬上限（G2）、活跃账号基数（`monitor.bans.set_active_accounts(N)`）。
4. 灰度开关全关（G4）。

### 2.2 金丝雀（第 1–3 天）
- **仅 1–2 个真实账号**（Boss + 猎聘 首发，A6 已采纳），日投递 ≤ 上限的 50%。
- 持续盯盘（Prometheus 文本导出见 `scripts/export_metrics.py`）：
  - 封号率 **< 1%/账号/月**（A3 KPI，护栏3 阈值 2% 告警）→ 超则立即 kill-switch 暂停。
  - LLM 日成本 **< 配置硬上限** → 触顶自动熔断（护栏2）。
  - 投递成功率 **≥ 80%**（护栏3 阈值）→ 低于则排查适配器/平台策略。
  - 错误率 **< 5%** → 高于则排查服务端。
- 任何账号触发验证码 → 自动暂停 + `record_ban`，人工介入前不恢复。

### 2.3 放量（金丝雀无事故后）
- 按周翻倍账号数，每档观察 3–7 天；全程保持封号率/成本/成功率/错误率看板。
- 仅在指标稳定后开启对应灰度开关（G4）。

### 2.4 回滚
- 任一硬指标越线 → `feature_flags` kill-switch 一键关对应能力；单机器/小容器部署可直接回滚上一镜像。
- PIPL 相关（G5）异常 → 立即 crypto-shred KEK，历史备份不可解密，止损。

---

## 3. 诚实边界（本文件不替代的动作）

- **Q5 部署**：运行 `scripts/cd-deploy.sh` + `DEPLOY_TOKEN` 或手动 6 步 → **仅用户可做**。
- **Q6 真实平台凭据**：配置真实 Boss/猎聘 账号·API Key → **仅用户可做**（循环不碰真实凭据）。
- **Q7 PIPL 法定签署**：上线前法定最终签署 → **仅用户/法务可做**。
- 本文件使上述动作「按剧本不事故」，但**不代替、不伪造**其执行。循环报告对 Q5/Q6/Q7 一律标「待用户触发」。

---

## 4. 与现有自动化的关系

- 3 条错峰自动化（:00/:20/:40）已 **ACTIVE**（用户 2026-08-18「用起来」授权）。
- 本文件为循环「阶段④⑤」的状态回传与告警提供**上线前安全基线**；循环在 Q5 之前只会：① 持续监控护栏代码/测试绿；② 待用户向 `TASK-QUEUE.md` 投放新 R1 任务或答 A1–A6/Q1/Q5–Q7 后继续；③ 不伪造「已部署」。
- 若用户在部署中遇任一 §1 闸门 No-Go，循环在 `TASK-ALERTS.md` 登记并停下对应包，等用户。
