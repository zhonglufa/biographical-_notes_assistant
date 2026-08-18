<!--
TRACE-BLOCK
role: 工程师(Engineer)
package: U8 通知中心 UI (A22/A23)
upstream_read:
  - design/ui/roles/U8-pm.md（R1-R7 + AC1-AC6）
  - design/ui/roles/U8-arch.md（组件树 + 字段映射）
  - design/ui/00-design-system.html / 01-app-shell.html（Badge/LiveStatusDot 范式）
downstream_write:
  - design/ui/screens/U8-notifications.html（已交付）
  - design/ui/roles/U8-qa.md
status: DONE（Team Lead 代笔）
-->
# U8 通知中心 · 交互规格（A22/A23）

## 1. 页面结构
- 顶部栏：标题「通知中心」+ 实时连接态（LiveStatusDot）+ 未读徽标（Badge）+「全部已读」按钮。
- 筛选 Tab：全部 / L0 / L1 / L2 / L3（色彩 chip 对齐级别）。
- 列表：NotificationCard（级别色条 + 标题 + 正文 + 相对时间 + 渠道 + 已读/删除）。

## 2. 关键交互
| 交互 | 触发 | 行为 | 反馈 |
|---|---|---|---|
| 加载 | 进入 | A22 拉取，骨架屏 | 数据/空态/错误态 |
| 实时推送 | A23 wsUrl 建连 | 新通知插顶 + 徽标+1 + 「新」标记 | 200ms 淡入（reduced-motion 关闭） |
| 断线重连 | WS 断开 | 指数退避 ≤3 次 | 状态点 黄「重连中」 |
| 降级轮询 | 重连失败 | 每 30s 拉 A22 补未读 | 状态点 灰「离线(轮询)」 |
| 筛选 | 点击 Tab | 过滤 + 重置分页 | 列表重渲 |
| 标已读 | 单击卡片 | read=true、徽标-1、去高亮 | 乐观更新 |
| 全部已读 | 按钮 | 二次确认闸门 → 批量置已读 | 徽标归零 |
| 删除 | 单条删除 | 软删 sent→deleted + 5s 撤销 | Toast + 撤销 |
| 隐私解锁 | 锁屏态点「解锁」 | 正文去模糊显详情 | 本地态，不改动后端 |

## 3. 状态机（与契约对齐）
`Notification`: `sent` → `read`（已读）/ `deleted`（软删，5s 可撤销）→ 服务端 90 天 `archived`。
`Connection`: `live` → `reconnecting` → `offline(poll)` → `live`。

## 4. 无障碍与动效
- 级别色 + 文字双标识（色盲可辨）；卡片 `aria-label` 含级别与已读态。
- 徽标数字变化 150ms；新通知淡入 200ms；全部尊重 `prefers-reduced-motion`。
- 按钮 ≥40px 可点；移动端 Tab 横滚、ops 转横排。

## 5. 数据契约（mock 本地）
A22 `GET /notifications` → `items[]`(id/level/title/body/read/createdAt/channel) + `unread`。
A23 `GET /notifications/ws` → `wsUrl`（前端建连；本原型仅模拟推送，不建真实 WS、无真实令牌）。
