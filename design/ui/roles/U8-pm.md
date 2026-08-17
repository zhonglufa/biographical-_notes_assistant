<!--
TRACE-BLOCK
role: PM
package: U8 通知中心 UI (A22 通知列表 / A23 WebSocket 实时推送)
upstream_read:
  - prd/PRD-简历自动投递与面试模拟-最终版.md §6.4 通知中心与消息通道（双通道分离/渠道降级/消息分级 L0-L3/频率聚合/免打扰/通知中心/去重/隐私）
  - prd/PRD-简历自动投递与面试模拟-最终版.md §20 系统核心实体（Notification 状态机 sent→read/deleted，到期 archived）
  - design/contracts/external-api.registry.json A22/A23 字段
  - design/contracts/notifications-list.response.schema.json（notification: id/level/title/body/read/createdAt/channel；unread）
  - design/contracts/notification-ws.response.schema.json（wsUrl）
  - design/ui/00-design-system.html（组件 token）/ 01-app-shell.html / ia-nav.md / 02-motion-system.html
  - design/ui/ROLE-WORKBOOK.md §2 PM 要素
downstream_write:
  - design/ui/roles/U8-arch.md
  - design/ui/screens/U8-notifications.html
  - design/ui/interaction-U8.md
  - design/ui/roles/U8-qa.md
status: DONE（由 Team Lead 代笔；子 agent 调度在此环境不稳定，依 UI-SELFCHECK §4 透明标注）
decisions:
  - 通知中心 = 站内信统一收件箱，始终可达（兜底），与移动端推送/邮件分离（双通道隔离）
  - 仅展示业务通知，不暴露系统信令（唤醒 Agent 的信令禁止出现在通知中心）
  - 锁屏隐私：默认「你有新的求职动态」，详情需解锁（遵循 PRD §6.4 隐私）
-->
# U8 通知中心 · 产品经理交互需求（A22/A23）

## 1. 目标与范围
**目标**：为求职者提供一个统一、可信、不打扰的「站内信收件箱」，覆盖投递状态、面试邀请、日报、系统告警等全部用户侧业务通知，并与移动端推送/邮件构成多通道兜底。
**范围**：通知列表浏览（A22）、实时推送连接状态感知（A23）、已读/未读、按级别筛选、批量已读、删除、归档提示。
**不做什么**：不实现「配置推送渠道/免打扰时段」（属 U10「我的」设置页与策略配置 U4 范畴，本屏仅展示状态与入口）；不实现系统信令通道 UI（禁止暴露）。

## 2. 交互需求清单（触发→行为→反馈→边界）
- **R1 列表加载**：进入通知中心 → 拉取 A22 `GET /notifications`（level?/page/pageSize）→ 渲染卡片列表 + 顶部未读计数徽标 → 加载中骨架、空态「暂无通知」、错误态重试。
- **R2 实时感知（A23）**：页面挂载 → 调用 A23 `GET /notifications/ws` 取得 `wsUrl` → 建立 WebSocket → 新通知到达时未读徽标 +1 并插入列表顶部（带「新」标记微动效）→ 连接断开自动重连（指数退避，最大 3 次），状态点显示「实时/重连中/离线」。
- **R3 级别筛选**：顶部 Tab（全部/L0 重要/L1/L2/L3）→ 点击筛选并重置分页 → 各级别用色彩 chip（L0 红/L1 橙/L2 蓝/L3 灰）区分；尊重 `prefers-reduced-motion`。
- **R4 已读交互**：单击卡片 → 标记 `read=true`、未读徽标 -1、卡片去高亮 → 提供「全部已读」按钮（二次确认，见 U11 确认闸门）。
- **R5 删除**：单条「删除」→ 标记 `deleted`（软删，状态机 sent→deleted）→ 滑出提示 + 撤销（5s 窗口，U11 撤销规范）→ 不物理删库（到期 90 天 archived）。
- **R6 多端已读同步**：标记已读时携带 `deviceId`，移动端已读 → PC 同步（PRD §6.4），PC 端轮询/WS 收到同步事件后更新徽标；离线时本地乐观更新，重连后校准。
- **R7 隐私与降级**：锁屏默认不显示公司/岗位名（仅「你有新的求职动态」）；渠道降级提示（如邮件失败→标「待站内展示」）；正文无敏感字段（身份证/手机号）。

## 3. 验收标准（可测）
- **AC1**：A22 返回 items 含全部 required 字段（id/level/title/read/createdAt）时列表正确渲染；缺字段降级为空卡片不崩溃。
- **AC2**：A23 取得 wsUrl 后 WS 连接成功，模拟推送 → 徽标实时 +1（≤1s 视觉反馈）。
- **AC3**：级别筛选 Tab 点击后列表仅含对应 level；未读徽标与 `unread` 字段一致。
- **AC4**：「全部已读」二次确认后，全部未读卡片转已读、徽标归零；撤销窗口内可还原。
- **AC5**：删除单条后该条移出列表且可 5s 内撤销；列表总数 -1。
- **AC6**（响应式）：375/768/1280 三档无横向溢出、卡片纵向堆叠、按钮 ≥40px 可点（UI-SELFCHECK R1–R7）。

## 4. 边界与异常
- A22 分页末页再下拉 → 提示「没有更多了」；网络错误 → 错误态 + 重试。
- A23 WS 失败 → 降级为轮询 A22（每 30s）补拉未读，状态点标「离线（轮询中）」，不阻断浏览。
- 单条通知 `channel=null`（站内信兜底）→ 隐藏渠道标签，仅标「站内」。

## 5. 无障碍 + 动效
- 级别 chip 同时用色彩 + 文字（L0 红「重要」），不依赖色盲不可辨；卡片 `aria-label` 含级别与已读态。
- 新通知插入用 200ms 淡入（尊重 reduced-motion）；徽标变化用 150ms 数字滚动。

## 上游引用
PRD §6.4 双通道隔离（通知中心=站内信兜底）、消息分级 L0–L3、频率聚合、免打扰、隐私锁屏；§20 Notification 状态机；契约 A22/A23 字段。

## 下游交付
架构师（`U8-arch.md`）须读 §2 R1–R7 + §3 AC1–AC6 来定组件树、NotificationCard 状态、`read/deleted/archived` 状态机映射与 A22/A23 字段映射表。
