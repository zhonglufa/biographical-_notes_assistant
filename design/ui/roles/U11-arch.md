<!--
TRACE-BLOCK
role: 架构师(Architect)
package: U11 交互设计总纲（全局交互模式）
upstream_read: [design/ui/roles/U11-pm.md, design/ui/00-design-system.html, design/ui/02-motion-system.html, design/ui/UI-SELFCHECK.md]
downstream_write: [design/ui/interaction-U11.md, design/ui/roles/U11-qa.md]
status: DONE（Team Lead 代笔）
decisions:
  - 将 U11 总纲固化为 6 个可复用组件模式：Skeleton/ErrorState/EmptyState/ConfirmModal/UndoToast/A11yKit
  - 这些模式已在 U1–U10 各自内联实现，本文件统一约定接口与降级规则，避免各屏漂移
-->
# U11 交互设计总纲 · 架构师（模式库映射）

## 1. 组件模式 ↔ 总纲条款
| 总纲条款 | 复用组件 | 接口约定 |
|---|---|---|
| §1 加载态 | `Skeleton` | `variant: card｜list｜text`；shimmer 1.3s；reduced-motion 降级静态 |
| §2 错误态 | `ErrorState` | `message` + `onRetry`；`aria-live="polite"`；结构化错误码 |
| §3 空态 | `EmptyState` | `icon` + `hint` + `action{label,onClick}` |
| §4 确认闸门 | `ConfirmModal` | `title` + `body` + `onConfirm/onCancel`；宽度 ≤90vw；双按钮 |
| §5 撤销 | `UndoToast` | `message` + `onUndo`；5s 窗口；自动消失 |
| §6 无障碍 | `A11yKit` | 全局：色+文字双标识、≥40px、读屏 `aria`、reduced-motion |

## 2. 一致性约束
- 动效时长/缓动统一引用 `02-motion-system.html` 的 `--d-*`/`--e-*`，禁止各屏私定义。
- 响应式断点统一 `00-design-system.html §6`：640/768/1024；窄屏卡片堆叠、壳折叠。
- 确认闸门/撤销语义在 U5（删适配器）、U8（删通知/全部已读）、U10（登出）、U7（支付）已落地，须与本表一致。

## 3. 与 V 阶段的衔接
- V 阶段生产前端须将这些模式抽为共享组件（Storybook 或等价），U1–U10 原型的内联实现作为迁移来源。
- T 阶段功能测试须覆盖：确认闸门二次确认、撤销 5s 窗口、reduced-motion 降级、错误重试。

## 上游引用
`U11-pm.md` §1–§7。

## 下游交付
QA（`U11-qa.md`）依本模式库对 U1–U11 做全局一致性核查。
