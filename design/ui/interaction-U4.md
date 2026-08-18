# U4 策略配置 · 交互规格（A12 / A13）

> 配套原型：`design/ui/screens/U4-strategy.html`（可交互 HTML，mock 数据，不接真实后端/凭据）。
> 契约对齐：`strategies`(response) / `strategies`(request) — matchThreshold(0–1) / dailyLimit(int≥0) / platforms[] / blacklist[]。

## 1. 屏幕目标
让求职者自助设定匹配门槛、每日限额、启用平台与黑名单，控制本机 Agent 的采集与投递行为（A12 读取 / A13 更新，PC 端为准 LWW）。

## 2. 信息结构
- 匹配阈值滑块（0–100% ↔ matchThreshold 0–1）。
- 每日投递限额数字输入（dailyLimit）。
- 启用平台 chips 多选（platforms 数组）。
- 黑名单标签输入（blacklist 数组，回车添加 / × 删除）。
- 保存 / 恢复默认。

## 3. 关键交互
| 交互 | 触发 | 行为 | 契约语义 |
|------|------|------|----------|
| 调阈值 | 滑块 | 实时显示百分比；语义提示绿/蓝/灰分档 | A12 `matchThreshold`(0–1) |
| 调限额 | 数字输入 | 联动 U3 限额展示；保存时校验非负整数 | A12 `dailyLimit` |
| 启用平台 | 点 chip | 切换 on/off；清空时显示警告「至少启用一个」 | A12 `platforms[]` |
| 黑名单 | 回车/添加 | tag 入列；× 删除 | A12 `blacklist[]` |
| 保存 | 「保存策略」 | 校验后写回（A13 PUT）；显示 `ok` + `updatedAt`；toast | A13 `ok + updatedAt` |
| 恢复默认 | 「恢复默认」 | 重置为默认策略 | 前端态 |

## 4. 校验 / 错误
- `matchThreshold` 越界（非 0–1）→ toast 拦截保存。
- `dailyLimit` 非整数/负数 → 拦截。
- `platforms` 为空 → 警告 + 拦截（否则无岗位可采集，属危险配置）。
- 黑名单重复项 → 不重复入列。

## 5. 与护栏/其他屏联动
- `dailyLimit` = U3「今日 X / 限额 N」的 N 来源，与**护栏 2（LLM 成本/投递量硬上限）**同源；达限额时 U3 确认禁用。
- `matchThreshold` 对应本机 Agent `plan()` 的 low 匹配过滤（LLD 本机 Agent v1.3）。
- `blacklist` 在匹配阶段预过滤，永不进入待确认队列。

## 6. 状态 / 空态 / 反馈
- 加载：初始值由 A12 读取填充（原型用默认 mock）。
- 反馈：保存后 `updatedAt` 回显（epoch→本地时间），符合「写操作有 toast 确认 + 契约返回可见」。

## 7. 与契约一致性
- 字段名/类型严格对齐：`matchThreshold` number(0–1)、`dailyLimit` integer(≥0)、`platforms`/`blacklist` 字符串数组。
- 平台枚举与 A07 一致（boss/liepin/zhaopin/51job/lagou）。

## 8. 评审结论（本轮）
- REVIEW-1 双闸门：未改契约/PRD/HLD，天然全绿。
- REVIEW-2：仅新增 UI 原型 + 交互规格，未偏离设计、未触 3 道在途护栏（双闸门/成本熔断/封号监控）。
- REVIEW-3：mock 数据、不接真实后端/凭据/部署，不触发红线，自动提交。
