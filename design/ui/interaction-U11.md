<!--
TRACE-BLOCK
role: 工程师(Engineer)
package: U11 交互设计总纲（全局交互模式）
upstream_read: [design/ui/roles/U11-pm.md, design/ui/roles/U11-arch.md, design/ui/00-design-system.html, design/ui/02-motion-system.html, design/ui/UI-SELFCHECK.md]
downstream_write: [design/ui/roles/U11-qa.md]
status: DONE（Team Lead 代笔）
-->
# U11 交互设计总纲 · 工程师实现检查清单

> 每个 U 屏交付前逐条勾选。未达标不得 commit（依 U11-pm §7 验收基线）。

## 加载态
- [ ] >300ms 获取有骨架屏/loading 态，无白屏
- [ ] 按钮提交中禁用 + 「处理中」文案
- [ ] >8s 转错误态

## 错误态
- [ ] 失败有内联错误（`aria-live="polite"`）+ 重试入口
- [ ] 结构化错误原因（验证码/限额/网络/账号）
- [ ] 离线投递提示「上线后自动执行」，不误判失败

## 空态
- [ ] 无数据有引导（说明 + 主操作）
- [ ] 当日无活动不渲染空图表

## 确认闸门
- [ ] 删除/全部已读/支付/登出 二次确认 Modal（≤90vw）
- [ ] 半自动投递（U3）用户显式确认队列

## 撤销
- [ ] 软删/已发送类 5s 撤销窗口（Toast 内嵌撤销）
- [ ] 已支付/已投递等硬动作仅确认闸门兜底

## 无障碍
- [ ] 状态色+文字双标识
- [ ] 可点元素 ≥40px
- [ ] 图表附数据表；卡片 `aria-label` 含状态
- [ ] 全局 `prefers-reduced-motion` 降级

## 响应式（UI-SELFCHECK R1–R7）
- [ ] 375/768/1280 无横溢、无重叠、卡片纵向堆叠
- [ ] 动效时长/缓动引用 02-motion-system `--d-*`/`--e-*`，不私定义

## 数据契约
- [ ] mock 本地，无真实 PII/凭据/部署（U10 未登录不暴露业务数据）
