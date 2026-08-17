<!-- TRACE
role: PM | software-product-manager
package: U5 适配器管理 UI (A14/A15)
agent_run: 2026-08-17T21:25
author_of_record: software-product-manager（本轮子 agent 调度瞬断，由 Team Lead 代笔，见 ROLE-DELIVERABLES.md 注）
upstream_read: [prd/PRD-简历自动投递与面试模拟-最终版.md §494-593(模块4 平台适配器系统), design/contracts/external-api.registry.json(A14/A15), design/contracts/adapter-facade.methods.json, design/contracts/adapter-enable.*.schema.json, design/contracts/b09-health.schema.json, design/ui/00-design-system.html, design/ui/ROLE-WORKBOOK.md §2]
downstream_write: [design/ui/roles/U5-arch.md, design/ui/screens/U5-adapter.html, design/ui/interaction-U5.md]
decisions: 本包仅做"适配器管理(查看/启用/停用/健康)"，不含"适配器市场安装/社区贡献/版本管理"(PRD 列为后续生态能力，超出 A14/A15 契约范围，标为 v2 范围)；启用/停用走确认闸门(A15 仅 pro)；健康度三态(正常/需登录/异常)映射 lifecycleStates。
status: DONE
-->

# U5 适配器管理 UI · 产品经理需求规格（A14 / A15）

> 角色：PM（software-product-manager）｜包：U5 适配器管理 UI｜对应契约：A14 适配器列表、A15 适配器启用/停用
> 配套：架构师产物 `U5-arch.md` ← 本文件被其引用；工程师产物 `U5-adapter.html` + `interaction-U5.md` ← 本文件被其引用

## 1. 目标与范围
**目标**：让用户在 PC 端一站式查看已接入招聘平台适配器的状态、健康度，并显式启用/停用某个适配器，从而控制"本机 Agent 在哪些平台执行投递"。
**范围（做）**：适配器列表（A14）、单适配器启用/停用（A15）、健康度展示、登录态提示、连接/健康异常引导。
**范围（不做 · 边界）**：适配器市场浏览/安装、社区贡献 PR、版本自动更新/回滚、灰度测试模式切换——这些属 PRD"适配器生态机制"后续能力，**不在 A14/A15 契约内**，标为 v2 范围，本包不实现入口。

## 2. 交互需求清单
| # | 交互 | 触发 | 行为 | 反馈 | 异常/边界 |
|---|------|------|------|------|-----------|
| R1 | 列表加载 | 进入"平台管理"页 | GET /adapters(A14) 拉取全部适配器 | 骨架屏→卡片列表按"首期/后续"分组 | 请求失败→错误态+重试；空数据→空态 |
| R2 | 健康度展示 | 列表渲染 | 按 `lifecycleStates` 显示状态徽标+色点 | 正常=绿/需登录=黄/停用=灰/异常(degraded)=红 | 连续 3 次 healthCheck 失败→自动置 degraded 并提示"平台暂时不可用" |
| R3 | 启用闸门 | 点"启用" | 弹二次确认：显示平台名+当前将变为 enabled | 确认→POST /adapters/{id}/enable{enabled:true}(A15)→状态变 enabled+toast | 非 pro 套餐→禁用按钮+提示"仅专业版可用"；请求失败→回滚+错误 toast |
| R4 | 停用警告 | 点"停用" | 弹警告确认：提示"停用后该平台不再参与投递调度" | 确认→A15{enabled:false}→状态变 disabled | 同 R3 失败处理 |
| R5 | 登录态失效引导 | 状态=login_expired | 显示"需重新登录"+「登录」按钮 | 点「登录」→获取 loginUrl/qr 引导(Adapter.LoginGuidance) | 仅引导，不代填凭据(红线) |
| R6 | 批量操作 | 多选适配器 | 工具栏出现"批量启用/停用" | 二次确认聚合数量 | 含非 pro 项时整批拦截并提示 |
| R7 | 连接失败重试 | 错误态 | 「重试」按钮 | 重新 R1 | 连续失败→指数退避提示，不无限刷 |

## 3. 验收标准（对应契约字段）
- AC1：列表字段含 `platformId/platformName/platformType/version/status/health`，与 A14 + `adapter-facade` + `b09-health` 一致。
- AC2：状态徽标枚举覆盖 `installed/test_mode/enabled/disabled/degraded/login_expired` 全 6 态（A14 lifecycleStates）。
- AC3：启用/停用调用 A15，请求体含 `enabled:boolean`，响应解析 `adapterId+status(enum enabled|disabled)`。
- AC4：非 pro 调用 A15 被拦截（A15 auth=Bearer+pro），UI 预校验并提示，不发请求。
- AC5：健康度色点与 `b09-health.healthy/cookieHealthy` 语义一致（healthy=false→红；cookieHealthy=false 且 login_expired→黄）。

## 4. 边界与异常场景
- 健康检查失败自动停用（PRD §547）：前端展示 degraded+通知文案，恢复需用户手动启用。
- 登录态失效（PRD §548）：前端展示 login_expired+「登录」引导，不代处理凭据。
- 版本冲突（PRD §549）：本包不实现版本管理，仅预留"更新"入口占位（置灰，标注 v2）。
- 网络/服务端错误：遵循全局错误基线——不暴露原始异常，统一错误态+"重试"。

## 5. 无障碍 + 动效要求
- 状态色点须配**文本标签**（不止颜色，满足色盲/无障碍基线）。
- 启用/停用确认弹窗须可键盘聚焦、Esc 关闭、`aria-modal`。
- 动效：列表入场轻过渡、状态变更高亮脉冲、toast 200ms 滑入；全部尊重 `prefers-reduced-motion`（关闭非必要动画）。见 `02-motion-system.html`。

## 上游引用
- PRD：`prd/PRD-简历自动投递与面试模拟-最终版.md` §494-593（模块 4 平台适配器系统、接口契约、异常场景、管理界面 ASCII）。
- 契约：`design/contracts/external-api.registry.json` A14/A15 行；`adapter-facade.methods.json`（login/healthCheck/isAvailable）；`adapter-enable.*.schema.json`；`b09-health.schema.json`。
- 设计基线：`design/ui/00-design-system.html`（组件 token）、`design/ui/ROLE-WORKBOOK.md` §2（PM 工作清单）。

## 下游交付
架构师（`U5-arch.md`）请重点读：§2 交互需求清单（R1–R7 作为组件/状态设计输入）、§3 验收标准（作为字段映射表依据）、§4 边界（作为状态模型与异常态依据）。工程师（`U5-adapter.html` + `interaction-U5.md`）请读 §2/§3/§5 实现行为与无障碍。
