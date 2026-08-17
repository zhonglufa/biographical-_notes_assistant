# U3 投递管理 · 交互规格（A09 / A10 / A11）

> 配套原型：`design/ui/screens/U3-applications.html`（可交互 HTML，mock 数据，不接真实后端/凭据）。
> 契约对齐：`applications-list`(response) + 投递状态机枚举（LLD §1 / ADR-008）+ A09 批量确认队列语义。

## 1. 屏幕目标
这是「半自动投递」安全模型的核心落地点。展示全部投递记录（A10）、单条状态机详情（A11），并通过显式确认闸门 + 二次确认 + 撤销窗口保障「发起投递」永远由用户主动触发（A09）。

## 2. 信息结构
- 工具栏：状态筛选 chips（全部/待确认/已投递/面试邀约/Offer/未通过）+ 「确认选中并投递（N）」按钮 + 今日限额提示。
- 列表（A10）：每条含 checkbox（仅 pending_confirm 可勾）/ 岗位标题 / 公司 / 平台 / 时间 / 状态徽标 / 查看详情。
- 详情面板（A11）：状态机进度可视化（10 态线性流，当前态高亮）+ 终态处理 + 单条确认按钮。

## 3. 关键交互
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 状态筛选 | 点 chip | 按 `status` 枚举过滤列表 | A10 `status` 查询 |
| 勾选待确认 | checkbox | 加入选中集，更新批量按钮计数 | 前端态（A09 队列） |
| 批量确认（闸门） | 「确认选中并投递（N）」 | 弹二次确认：显示**数量 + 各平台分布**；确认后选中项 `pending_confirm→submitted`，toast + **10s 撤销窗口** | A09 `POST /applications/batch` |
| 单条确认 | 详情「确认并投递这一个」 | 等同批量闸门（二次确认） | A09 |
| 撤销 | 撤销窗口按钮 | 选中项回退 `submitted→pending_confirm` | 前端态（A09 执行回滚） |
| 查看详情 | 「查看详情」 | 展开状态机进度流 + 终态标注 | A11 `GET /applications/{id}` |

## 4. 状态机可视化（A11）
- 10 态线性流：`pending_confirm → autofilling → submitted → viewed → contacting → interview_invited → interview_done → offer`；`rejected` / `closed` 为终态分支。
- 配色（与 ia-nav 基线一致）：pending=灰 / submitted/viewed=绿 / contacting=蓝 / interview*=accent(紫) / offer=绿 / rejected=红 / closed=neutral。
- 已完成态打勾，当前态主色 + 外环高亮，未完成态灰。终态（rejected/closed）单独高亮红/neutral，不渲染后续流。

## 5. 安全交互红线（核心）
- **显式确认**：任何「发起投递」必须用户点击，无静默自动投递。
- **二次确认**：批量确认弹窗显示数量与平台分布（防误投）。
- **撤销窗口**：投递后 10 秒内可一键撤销（降低误操作成本）。
- **限额可见**：工具栏常驻「今日 X / 限额 20」，达限额时禁用确认并说明剩余。
- **本机执行说明**：确认弹窗明确「由本机 Agent 在你的浏览器实例中执行」，UI 只收意图+闸门，不代发。

## 6. 状态 / 转场 / 空态 / 错误
- **加载**：列表加载用骨架（原型即时 mock，标注语义）。
- **空态**：筛选无记录 → 占位「该状态下暂无投递记录」，引导去首页/岗位浏览。
- **错误**：账号类异常（真实场景）由通知中心/适配器引导重连，本屏不暴露原始异常（符合全局基线）。

## 7. 与契约一致性
- `status` 严格用 10 态枚举；`applicationId/jobId/platformId/appliedAt(epoch ms)` 与 `applications-list.response` 一致。
- 状态机流转顺序与 LLD 投递状态机 / ADR-008 一致（pending_confirm 为合法起始，rejected/closed 为终态）。

## 8. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-2：仅新增 UI 原型 + 交互规格；虽触及「半自动确认闸门」设计（PIPL§24 缓解），但纯前端 mock 不读 Cookie/不登录/不碰凭据/不部署，**不触发 REVIEW-3 红线**，自动提交。
- REVIEW-3 评估：原型仅 mock 数据、不接真实后端/凭据/部署，不触发红线。
