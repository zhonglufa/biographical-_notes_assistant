<!--
TRACE-BLOCK
role: 架构师(Architect)
package: U8 通知中心 UI (A22/A23)
upstream_read:
  - design/ui/roles/U8-pm.md（R1-R7 交互需求 + AC1-AC6 验收）
  - design/ui/00-design-system.html（组件 token：卡片/按钮/chip/徽标）
  - design/ui/01-app-shell.html（顶部栏/未读徽标范式）
  - design/contracts/notifications-list.response.schema.json / notification-ws.response.schema.json
downstream_write:
  - design/ui/screens/U8-notifications.html
  - design/ui/interaction-U8.md
  - design/ui/roles/U8-qa.md
status: DONE（Team Lead 代笔；子 agent 调度不稳定，依 UI-SELFCHECK §4 标注）
decisions:
  - 组件树：NotificationCenterPage → FilterTabs + LiveStatusDot + NotificationList → NotificationCard
  - 复用设计系统已有：Card、Button、Chip、Badge、Skeleton、EmptyState、ErrorState
  - 新增：LiveStatusDot（实时连接态）、NotificationCard（级别色条 + 已读态）
  - 状态模型：列表 loading/empty/error/data；每条 read 布尔；连接 conn: live/reconnecting/offline(polling)
-->
# U8 通知中心 · 架构师组件设计（A22/A23）

## 1. 组件树
```
NotificationCenterPage
├─ TopBar（标题「通知中心」+ 未读徽标 Badge + 全部已读按钮）
├─ LiveStatusDot（A23：live 绿 / reconnecting 黄 / offline-poll 灰，含重连退避）
├─ FilterTabs（全部 / L0 / L1 / L2 / L3，色彩 chip 对齐级别）
└─ NotificationList
   ├─ Skeleton ×3（加载）
   ├─ EmptyState（无通知）
   ├─ ErrorState（加载失败 + 重试）
   └─ NotificationCard ×N
      ├─ LevelBar（L0 红/L1 橙/L2 蓝/L3 灰 左侧色条）
      ├─ Title（+ 「新」标记，未读加粗）
      ├─ Body（隐私模式默认脱敏，解锁后显详情）
      ├─ Meta（时间相对值 + 渠道标签）
      └─ 操作（标记已读 / 删除+撤销）
```

## 2. 状态模型（与契约字段映射）
| UI 状态 | 来源字段 | 说明 |
|---|---|---|
| 列表数据 | A22 `items[]` | id/level/title/body/read/createdAt/channel |
| 未读计数 | A22 `unread` | 顶部徽标，乐观更新后由 WS/轮询校准 |
| 连接态 | A23 `wsUrl` → WS 生命周期 | live / reconnecting / offline(poll) |
| 单条已读 | `read` 布尔 | 单击 → true；状态机 sent→read |
| 单条删除 | 软删 sent→deleted | 滑出提示 + 5s 撤销（U11） |
| 到期归档 | —（服务端 90 天） | 仅展示「已归档」分组入口，不在前端强删 |

## 3. 复用决策
- **复用**：Card、Button、Chip、Badge、Skeleton、EmptyState、ErrorState（设计系统已有）。
- **新增**：`LiveStatusDot`（连接态可视化，含指数退避重连逻辑）、`NotificationCard`（级别色条 + 已读去高亮 + 撤销）。
- 顶部栏未读徽标沿用 `01-app-shell.html` 的 Badge 范式。

## 4. UI 字段 ↔ 契约字段映射表
| UI 元素 | 契约字段 | 类型/枚举 |
|---|---|---|
| 级别色条/筛选 | `level` | L0/L1/L2/L3 |
| 标题 | `title` | string |
| 正文 | `body` | string（隐私模式脱敏） |
| 是否已读 | `read` | boolean |
| 相对时间 | `createdAt` | epoch ms → 「x 分钟前」 |
| 渠道标签 | `channel` | string｜null→「站内」 |
| 未读总数 | `unread` | integer |
| 实时连接 | `wsUrl`（A23） | 签名的 WS 地址（token 走 query） |

## 5. 关键交互状态流转
- **实时推送接入**：挂载 → A23 取 wsUrl → 建连（live）→ 收到推送 → 插入顶部 + 徽标+1；断线 → reconnecting（退避）→ 3 次失败 → offline(poll) 每 30s 拉 A22 补未读。
- **全部已读**：二次确认（U11 闸门）→ 批量置 read=true → 徽标归零 → 乐观更新，WS 同步多端。
- **删除撤销**：deleted 软删 + 5s 撤销窗口（U11 撤销规范），窗口内还原 `read` 态不变。

## 上游引用
`U8-pm.md` §2 R1–R7、§3 AC1–AC6、§5 无障碍/动效要求。

## 下游交付
工程师（`screens/U8-notifications.html` + `interaction-U8.md`）须依本组件树与 §4 映射表实现；QA（`U8-qa.md`）依 AC1–AC6 + 响应式 R1–R7 核查。
