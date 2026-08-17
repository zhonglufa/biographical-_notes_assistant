# U1 简历工作台 · 交互规格（A04 / A05 / A06）

> 配套原型：`design/ui/screens/U1-resume.html`（可交互 HTML，mock 数据，不接真实后端/凭据）。
> 契约对齐：`resumes-create` / `resume-versions` / `resume-ats` 三个 response schema。

## 1. 屏幕目标
让求职者在本机集中管理简历、查看多版本快照、触发 ATS 通过率评分，并一键进入「待确认投递」匹配流程。

## 2. 信息结构
- 左栏：简历列表（卡片：标题 / 模板 / 版本数 / 首选版本徽标 + 操作）。
- 右栏：选中简历的版本面板（版本时间线 + 设为首选 + 结构化 diff 入口）。
- ATS 评分任务卡嵌在每份简历卡片下方（异步状态机）。

## 3. 关键交互
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 新建简历 | 「＋ 新建简历」→ 弹窗 → 创建 | 表单（标题/正文/模板）→ 列表顶部插入新卡；toast 显示 `resumeId` | A04 响应：`resumeId / versionId / createdAt` |
| 查看版本 | 「查看版本」 | 右栏展开该简历版本时间线（versionNo / createdAt / note / isPreferred） | A05：`versions[]` + `diffAvailable` |
| 设为首选 | 版本行「设为首选」 | 该版本 `isPreferred=true`、其余 false；列表/面板刷新 | A05 `isPreferred` |
| 版本对比 | 「对比两版」 | 仅当版本数≥2（diffAvailable=true）可用；否则禁用并说明 | A05 `diffAvailable` |
| 触发 ATS 评分 | 「触发 ATS 评分」 | 生成 `taskId`，状态 pending→running→done（进度条 + 文案）；done 展示 mock 评分环与维度分 | A06 响应：`taskId / status(pending|running|done|failed)` |
| 去匹配 | 「去匹配 →」 | 跳转首页待确认投递（mock 导航，待 U3 落地） | 衔接 A09/A10/A11 |

## 4. 状态 / 转场 / 空态 / 错误
- **加载**：首次列表加载用行内 skeleton（原型中为即时 mock，标注「匹配中…」占位语义）。
- **空态**：无简历 → 引导「＋ 新建简历」；版本面板未选 → 占位「尚未选择简历」。
- **ATS 状态机**：`pending`→`running`（45%）→`done`✅；`failed` 分支预留（真实由后端回填，UI 显示「评分失败，可重试」并提供重试按钮，不暴露原始异常）。
- **错误**：创建表单缺标题 → 行内 toast 提示，不提交；ATS 失败 → 行内「重试」入口。

## 5. 确认闸门 / 反馈
- 新建为写操作，提交后有 toast 确认（`resumeId` 回显，便于用户核对契约返回）。
- 无删除/危险操作于本屏；「设为首选」为轻量切换，即时生效 + toast。

## 6. 与契约一致性
- 枚举/字段严格对齐：ATS `status` 仅用 `pending|running|done|failed`；版本字段 `versionId/versionNo/createdAt/isPreferred` 与 schema 一致；`diffAvailable` 按版本数推导。
- `createdAt` 为 epoch 毫秒（schema `minimum:0`），UI 展示时转为「X月X日」。

## 7. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-2：仅新增 UI 原型 + 交互规格，未偏离设计、未触 3 道在途护栏（双闸门/成本熔断/封号监控）。
- REVIEW-3：原型仅 mock 数据、不接真实后端/凭据/部署，不触发红线，可自动提交。
