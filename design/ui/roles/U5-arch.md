<!-- TRACE
role: Architect | software-architect
package: U5 适配器管理 UI (A14/A15)
agent_run: 2026-08-17T21:26
author_of_record: software-architect（本轮子 agent 调度瞬断，由 Team Lead 代笔）
upstream_read: [design/ui/roles/U5-pm.md(§2 交互清单/§3 验收/§4 边界), design/ui/00-design-system.html, design/ui/01-app-shell.html, design/ui/ia-nav.md, design/contracts/external-api.registry.json(A14/A15), design/contracts/adapter-facade.methods.json, design/contracts/b09-health.schema.json, design/ui/ROLE-WORKBOOK.md §3]
downstream_write: [design/ui/screens/U5-adapter.html, design/ui/interaction-U5.md]
decisions: 复用 U1-U4 既有组件(卡片/徽标/确认弹窗/骨架/错误态/toast)而非新增；新增唯一组件=AdapterStatusDot(6态色点+文本标签)；启用/停用走与 U3 一致的"二次确认闸门"模式；列表分组(首期/后续)用既有 Section 容器。
status: DONE
-->

# U5 适配器管理 UI · 架构师设计（A14 / A15）

> 角色：Architect｜包：U5｜上游：`U5-pm.md`（需求/验收/边界）← 本文件引用其 §2/§3/§4｜下游：工程师 `U5-adapter.html` + `interaction-U5.md` ← 本文件被其引用

## 1. 组件树
```
AppShell (复用 01-app-shell.html 顶栏+侧栏)
└─ Page: 平台管理 (U5)
   ├─ Section: 首期 (复用 U1-U4 Section 容器)
   │  └─ AdapterCard × N        // 复用卡片+徽标
   │     ├─ AdapterStatusDot    // 【新增】6态色点+文本
   │     ├─ MetaRow (platformName/type/version/author)
   │     ├─ HealthSummary (healthy/cookieHealthy/checkedAt)
   │     └─ ActionBar [启用|停用|登录|更新(占位)]
   ├─ Section: 后续 (未安装，显示"安装适配器"占位→v2)
   └─ ConfirmDialog (复用 U3 二次确认闸门)
      └─ Toast (复用)
```

## 2. 状态模型
**页面级**：`loading → loaded(empty|list) → error(retry)`。
**单适配器业务态**（映射 A14 `lifecycleStates`，6 态）：
| 契约态 | 展示 | 色点 | 文本标签 | 可执行动作 |
|--------|------|------|----------|-----------|
| installed | 已安装未启用 | 灰 | "已安装" | 启用 |
| test_mode | 测试模式 | 蓝 | "测试中" | 启用(转正)/停用 |
| enabled | 正常 | 绿 | "正常" | 停用 |
| disabled | 已停用 | 灰 | "已停用" | 启用 |
| degraded | 健康异常 | 红 | "异常" | 启用(恢复)/查看 |
| login_expired | 需登录 | 黄 | "需登录" | 登录(引导) |

**健康子态**（来自 `b09-health`）：`healthy(bool)`、`cookieHealthy(bool)`、`checkedAt(epoch)`、`avgLatencyMs`。

## 3. 复用决策
- **复用（来自设计系统/U1-U4）**：AppShell、Section 容器、Card、Badge、ConfirmDialog（二次确认闸门）、Skeleton、ErrorState、Toast、Button 变体。
- **新增（仅 1 个）**：`AdapterStatusDot` —— 封装 6 态色点+强制文本标签（满足无障碍：不止颜色）。其余均不新增组件。
- **模式复用**：启用/停用确认闸门直接复用 U3 的"二次确认 + 撤销窗口"交互模式（安全交互基线一致）。

## 4. UI 字段 ↔ 契约字段映射表
| UI 字段 | 契约来源 | 说明 |
|---------|----------|------|
| 平台名 | `platformName` (adapter-facade) | 展示 |
| 类型 | `platformType` (social/campus/state-owned/headhunter/other) | 展示+图标 |
| 版本 | `version` | 展示 |
| 状态徽标 | `status` (lifecycleStates) | 6 态映射见 §2 |
| 健康点 | `b09-health.healthy` | 红/绿 |
| Cookie 健康 | `b09-health.cookieHealthy` | 影响 login_expired 判定 |
| 最后检查 | `b09-health.checkedAt` | epoch→相对时间 |
| 启用动作 | A15 `POST /adapters/{id}/enable` `{enabled}` | 写 |
| 启用响应 | A15 `response{adapterId,status}` | 回写 status |
| 列表数据 | A14 `GET /adapters` | 读 |

## 5. 关键交互状态流转（启用闸门）
```
[disabled/installed] --点启用--> ConfirmDialog(显示平台名+将变 enabled)
   --确认--> POST A15{enabled:true} --200--> status=enabled + Toast(--撤销窗口10s--> 可回退 disabled)
   --取消--> 保持原态
   --非pro--> 拦截不发请求 + 提示"仅专业版"
   --失败--> 回滚原态 + 错误 Toast
```
停用对称（A15{enabled:false}→disabled）。

## 上游引用
- 需求/验收/边界：`design/ui/roles/U5-pm.md` §2（R1–R7）、§3（AC1–AC5）、§4（异常场景）。
- 设计基线：`design/ui/00-design-system.html`（token）、`01-app-shell.html`（壳）、`ia-nav.md`（导航位置=侧栏"平台管理"）。
- 契约：`external-api.registry.json` A14/A15、`adapter-facade.methods.json`、`b09-health.schema.json`。
- 复用范本：`screens/U3-applications.html` 的 ConfirmDialog/撤销窗口模式。

## 下游交付
工程师（`U5-adapter.html` + `interaction-U5.md`）请读：§1 组件树（按此实现 DOM 结构）、§2 状态模型（6 态展示+健康子态）、§3 复用决策（只新增 AdapterStatusDot）、§4 字段映射表（UI 字段严格来自此表）、§5 启用闸门流转。
