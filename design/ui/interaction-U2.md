# U2 岗位浏览 · 交互规格（A07 / A08）

> 配套原型：`design/ui/screens/U2-jobs.html`（可交互 HTML，mock 数据，不接真实后端/凭据）。
> 契约对齐：`jobs-list`(response) / `jobs-search`(request) / `jobs-favorite`(request+response)。

## 1. 屏幕目标
求职者浏览跨平台岗位，用关键词/城市/平台/薪资下限筛选，按 AI 匹配度（matchBand）快速判断契合度，收藏送入待确认投递、忽略后不再推送。

## 2. 信息结构
- 筛选条：关键词 / 城市 / 月薪下限 / 搜索按钮（A07 查询参数：keyword/location/salaryMin/page/pageSize）。
- 平台筛选 chips：全部 / Boss直聘 / 猎聘 / 智联 / 前程无忧 / 拉勾（A07 `platform` 枚举）。
- 岗位列表：匹配度环（按 matchBand 着色）+ 标题/公司/平台/城市/薪资/来源 + 匹配理由 + 收藏/忽略/详情操作。
- 分页器（mock，page/pageSize 语义）。

## 3. 关键交互
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 搜索/筛选 | 输入 + 搜索 / 点平台 chip | 实时过滤本地 mock 集；结果数回显 | A07 `keyword/location/platform/salaryMin/page/pageSize` |
| 收藏 | 「收藏 →」 | `favorited=true`、亮「已收藏」徽标、toast「已送入待确认投递」 | A08 `action=favorite` → `status=favorited` |
| 取消收藏 | 「取消收藏」 | `favorited=false` | A08 `status=removed`（软删 favoriteId=null） |
| 忽略 | 「忽略」 | 卡片降透明度、`status=ignored`、toast「不再推送」；提供「撤销忽略」 | A08 `action=ignore` → `status=ignored` |
| 撤销忽略 | 「撤销忽略」 | 恢复卡片 | A08 状态回滚（前端态） |
| 详情 | 「详情」 | 打开岗位详情（mock，待采集路径细化） | `source=search|detail` |

## 4. 匹配度可视化（matchBand）
- `green` ≥80：绿底绿字（高契合，建议优先确认投递）。
- `blue` 60–79：蓝底蓝字（中等，可纳入）。
- `gray` <60：灰底灰字（低契合，默认不进待确认队列）。
- `matchScore=null`：显示「—」，环置灰（数据缺失不臆造）。

## 5. 状态 / 转场 / 空态 / 错误
- **加载**：搜索后列表即时刷新（原型 mock；真实为「匹配中…」骨架屏占位）。
- **空态**：无匹配 → 引导放宽筛选 / 去简历工作台更新偏好（正向文案，不责怪）。
- **错误**：薪资下限非法输入 → 解析失败提示「请输入数字」，不报错崩溃。

## 6. 确认闸门 / 反馈
- 收藏为轻写操作，即时 toast 确认；收藏即衔接首页待确认投递（A09 队列）。
- 忽略为可逆操作（撤销入口），符合「危险/过滤操作可撤销」基线。

## 7. 与契约一致性
- `platform` 严格用枚举 `boss|liepin|zhaopin|51job|lagou`；`matchBand` 仅 `green|blue|gray`；`source` 仅 `search|detail`；`salaryMin/Max` 为整数（元/月）或 null。
- 列表字段（jobId/title/company/platformId/location/matchScore/matchReason/favorited/collectedAt）与 `jobs-list.response` jobStub 一致。

## 8. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-2：仅新增 UI 原型 + 交互规格，未偏离设计、未触 3 道在途护栏。
- REVIEW-3：mock 数据、不接真实后端/凭据/部署，不触发红线，自动提交。
