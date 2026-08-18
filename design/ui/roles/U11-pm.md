<!--
TRACE-BLOCK
role: PM
package: U11 交互设计总纲（全局交互模式：加载/错误/空态/确认闸门/撤销/无障碍）
upstream_read:
  - design/ui/00-design-system.html（组件 token）/ 01-app-shell.html / 02-motion-system.html（动效 token + reduced-motion）
  - design/ui/UI-SELFCHECK.md §3（R1-R7 响应式三端自查）
  - design/ui/interaction-U1.md ~ U10.md（既有交互规格，提炼共性）
  - prd/PRD-简历自动投递与面试模拟-最终版.md §6.3（异常处理与用户感知）/ §6.4（通知分级/免打扰）
  - design/ui/ROLE-WORKBOOK.md §2
downstream_write: [design/ui/roles/U11-arch.md, design/ui/interaction-U11.md, design/ui/roles/U11-qa.md]
status: DONE（Team Lead 代笔；子 agent 调度不稳定，依 UI-SELFCHECK §4 标注）
decisions:
  - U11 是跨切面交互基线（非单屏），产出一份《交互设计总纲》供 U1–U10 与 V/T 阶段统一遵循
  - 覆盖 6 大全局模式：加载态 / 错误态 / 空态 / 确认闸门 / 撤销 / 无障碍
  - 与 02-motion-system.html（动效）+ UI-SELFCHECK.md（响应式）构成完整交互规范三层
-->
# U11 交互设计总纲 · 产品经理（全局交互模式）

> 本文件是 resume-ai-prod 全部用户面的**统一交互基线**。U1–U10 各屏均须遵循本总纲；V 阶段生产前端、T 阶段测试依此验收。

## 1. 加载态（Loading）
- **原则**：任何 >300ms 的数据获取必须给反馈；不出现白屏/无响应。
- **模式**：骨架屏（列表/卡片占位，带 shimmer 动效）优先于 spinner；按钮提交中显 loading 态（禁用 + 文案「处理中」）。
- **动效**：shimmer 1.3s 循环；尊重 `prefers-reduced-motion` 时降级为静态灰块。
- **超时**：>8s 无响应转错误态（见 §2），不无限转圈。

## 2. 错误态（Error）
- **原则**：失败必须可见、可恢复、不丢数据；结构化错误原因（验证码/限额/网络/账号异常，PRD §6.3）。
- **模式**：内联错误提示（`aria-live="polite"`，红字）+ 「重试」入口；全局错误 Toast 不阻断上下文。
- **分级**：L0/L1 错误（投递失败需处理、登录态失效）按 PRD §6.4 走重要通道；普通错误轻提示。
- **离线**：PC 离线投递 → 提示「将在电脑上线后自动执行」，不视为失败（PRD §6.3）。

## 3. 空态（Empty）
- **原则**：无数据时给引导而非空白；说明「为什么空」+ 「下一步做什么」。
- **模式**：图标 + 一句话说明 + 主操作按钮（如「去连接平台」「今日无投递活动」）。
- **边界**：当日无活动 → 友好空摘要，不渲染空图表（U9 边界）。

## 4. 确认闸门（Confirmation Gate）
- **原则**：破坏性/不可逆/涉及花费的动作必须二次确认（删除、全部已读、支付、登出）。
- **模式**：底部/居中 Modal（≤90vw），标题 + 后果说明 + 「取消/确认」双按钮；确认按钮用主色，取消弱化。
- **例外**：高频低风险操作（如标已读）免确认，直接执行 + 可逆反馈（见 §5）。
- **半自动投递闸门**（U3 核心）：批量投递前必须用户显式确认队列，本机 Agent 异步执行（PRD §15）。

## 5. 撤销（Undo）
- **原则**：软性删除/已发送类操作提供 5s 撤销窗口，降低误操作成本。
- **模式**：Toast 内嵌「撤销」按钮（U5 删除适配器、U8 删除通知均遵循）；撤销窗口内还原原状态，不写库。
- **边界**：已支付/已投递等硬动作不可撤销，仅确认闸门兜底。

## 6. 无障碍（Accessibility）
- **色彩**：状态不仅靠颜色（级别 L0–L3 用色+文字双标识，色盲可辨）。
- **触控**：所有可点元素 ≥40px；移动端 Tab 横滚、操作区转横排。
- **读屏**：图表附数据表（U9 趋势）；卡片 `aria-label` 含状态；错误 `aria-live`。
- **动效**：全局尊重 `prefers-reduced-motion`；动效仅服务反馈（02-motion-system）。
- **响应式**：375/768/1280 三档无横向溢出、无重叠、卡片纵向堆叠（UI-SELFCHECK R1–R7）。

## 7. 验收基线
- 任一新屏须声明遵循本总纲 + 通过 UI-SELFCHECK R1–R7 + 动效 reduced-motion 检查，否则不得 commit。

## 上游引用
02-motion-system.html、UI-SELFCHECK.md §3、PRD §6.3/§6.4、U1–U10 交互规格。

## 下游交付
架构师（`U11-arch.md`）将本总纲映射为可复用组件模式库；QA（`U11-qa.md`）据此做全局一致性核查。
