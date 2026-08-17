# O 阶段 · 运维就绪交付说明

> 角色：DevOps（SoftwareCompany 无 DevOps agent，由 general-purpose 代理；Team Lead 复核）。
> 对应 PROJECT_BRAIN §1 V/T/O 七阶段之 **O 阶段（O1/O2/O3）**。
> 本阶段做到「生产就绪脚本」级：**不真部署**——部署上线 / 真实凭据 / 真实用户属用户独有动作，循环标「待用户触发」，不伪造完成。

## 1. 交付物
- **O1 · CI/CD 配置**：重写 `.github/workflows/dual-gate.yml` 为 `ci-cd.yml` 分层门禁——
  - `gates`：双闸门（契约 + PRD/HLD 追溯），prd/design 改动触发（保留原有）；
  - `test`：scaffold 全量 Python 测试（T 阶段 13 文件），任意源码改动触发；
  - `build-frontend`：前端 React+Vite 生产构建（V 阶段产物），上传 `frontend-dist` 制品；
  - `package-cd`：轻量 CD 打包（O2），受 `secrets.DEPLOY_TOKEN` 门控（无凭据仅本地打包）。
  - 复用既有 `githooks/pre-commit` 三闸门（闸门0 版本戳 / 闸门1 契约 / 闸门2 PRD-HLD）。
- **O2 · 轻量 CD 脚本**：`scripts/cd-deploy.sh`——合并后自动构建「单机器/小容器」部署包：前端 `npm ci && npm run build` → `frontend/dist`；服务端桩 + 监控接入点打包为 `dist-cd/server` 并生成 `MANIFEST.txt`。所有对外动作（docker push/ssh/拉起）受 `$DEPLOY_TOKEN` 门控，无凭据仅本地打包并打印人工上线 6 步。
- **O3 · 监控接入代码**：`scaffold/src/monitor_hooks.py`——把 `LightweightMonitor`（护栏 3）接入运行期事件流 `apply.status.changed`，自动累计投递成功率；提供 `record_llm_cost` / `record_ban` 接入点（护栏 2 与 3 共享 LLM 成本计数）。配套 `scripts/export_metrics.py` 将 snapshot 导出为 **Prometheus 文本格式**（零依赖），供运维挂 `/metrics` 由 Prometheus 抓取。

## 2. 验证
- `python scaffold/src/monitor_hooks.py` 自测通过（事件流正确累计成功率 0.75 并触发 `apply_success_low` 告警，验证阈值逻辑）。
- `python scripts/export_metrics.py` 演示输出 Prometheus 指标（成功率/封号率/错误率/LLM成本/告警）正常。
- `scripts/cd-deploy.sh` 在无 `DEPLOY_TOKEN` 下仅本地打包、打印人工步骤，不触达生产（设计预期）。
- 双闸门（REVIEW-1）：契约校验（gate1）+ PRD/HLD 追溯（gate2）实跑全绿；scaffold 13 测试文件全绿。

## 3. 与运维采纳结论对齐（PROJECT_BRAIN §4）
- CI 必留 ✅（双闸门 + test + build 三道云端门禁）。
- CD 轻量 ✅（合并后自动构建单机器/小容器部署包，非 GitOps 重型流程）。
- 监控必要 ✅（比 K8s 更该先有；Prometheus 文本导出范式已就位）。
- K8s 现阶段不要 ✅（部署包为单机器/小容器，未引入 K8s 编排）。

## 4. 已知事项 / 不伪造完成
- O 阶段产物均为「生产就绪脚本」；**真实部署 / 真实凭据 / 真实用户 / 监控生产后端**属用户独有动作，循环标「待用户触发」。
- 真实 LLM 日硬上限金额、监控阈值（护栏 2/3 生产值）由部署方/用户按预算配置（DEMO 默认 ¥500/天、封号率>2% 告警），循环不代设真实金额、不花钱、不订阅。
- 护栏 4/5/6（灰度回滚 / PIPL crypto-shred+合规 / 法检复核）= 用户 2026-08-17 延后，不计入本次 /goal，如实标注「用户延后」。

## 5. 结论
O 阶段（运维就绪）**达成** ✅：CI/CD 配置（O1）+ 轻量 CD 脚本（O2）+ 监控接入代码（O3）齐备，全部「生产就绪、不真部署」。
至此 **A+B+C+U+V+T+O 七阶段 + 护栏 1/2/3 全部达成** → **GOAL REACHED**，产出「产品交付结果报告 v2」。
