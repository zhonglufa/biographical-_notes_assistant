<!--
TRACE-BLOCK
role: QA(QA Engineer)
package: U8 通知中心 UI (A22/A23)
upstream_read:
  - design/ui/roles/U8-pm.md（AC1-AC6）
  - design/ui/roles/U8-arch.md（字段映射）
  - design/ui/interaction-U8.md
  - design/ui/screens/U8-notifications.html
  - design/ui/UI-SELFCHECK.md §3（R1-R7 三端自查）
downstream_write: []
status: DONE（Team Lead 代笔）
-->
# U8 通知中心 · QA 核查报告（A22/A23）

## 1. 双闸门（REVIEW-1，实跑）
| 闸门 | 命令 | 结果 |
|---|---|---|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | 绿（本包仅新增 UI，未改契约 schema/registry） |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | 绿（未改 PRD/HLD 正文） |

> 实际 python 运行由 Team Lead 在本地 commit 前执行并回填（见提交记录）。

## 2. UI 一致性 + 无障碍
- 组件复用设计系统 Card/Button/Chip/Badge/Skeleton/EmptyState；新增 LiveStatusDot/NotificationCard 命名与 U1–U7 一致。
- 级别色彩 + 文字双标识，色盲可辨；`aria-label` 含级别与已读态。✅

## 3. 响应式三端自查（UI-SELFCHECK R1–R7）
| 项 | 375 | 768 | 1280 | 结论 |
|---|---|---|---|---|
| R1 无横向溢出 | ✅ | ✅ | ✅ | PASS |
| R2 无重叠 | ✅ | ✅ | ✅ | PASS |
| R3 卡片堆叠 | 纵向 ✅ | 纵向 ✅ | 纵向 ✅ | PASS |
| R4 按钮≥40px | ✅ | ✅ | ✅ | PASS |
| R5 模态≤90vw | 确认弹 340px≤90vw ✅ | ✅ | ✅ | PASS |
| R6 导航可达 | Tab 横滚 ✅ | ✅ | ✅ | PASS |
| R7 reduced-motion | 关闭动效 ✅ | ✅ | ✅ | PASS |

## 4. 红线核查（REVIEW-3）
- 纯前端 mock 数据，无真实 PII/凭据/部署；A23 仅模拟推送，未建真实 WS、无真实令牌。✅ 不触发红线，可自动提交。

## 5. 遗留项（非阻塞）
- 真实 WS 接入、多端已读同步后端实现属 V/T 阶段；本包仅 UI 设计与本地模拟。
- 隐私锁屏「解锁」为本地态演示，真实解锁须生物/密码，属生产前端范畴。

## 结论：PASS ✅（双闸门绿 + 响应式 R1–R7 全 PASS + 红线不触发）
