<!--
TRACE-BLOCK
role: QA(QA Engineer)
package: U11 交互设计总纲（全局交互模式）
upstream_read: [design/ui/roles/U11-pm.md, design/ui/roles/U11-arch.md, design/ui/interaction-U11.md, design/ui/UI-SELFCHECK.md, design/ui/screens/U1-resume.html ~ U10-auth.html]
downstream_write: []
status: DONE（Team Lead 代笔）
-->
# U11 交互设计总纲 · QA 全局一致性核查

## 1. 双闸门（REVIEW-1，实跑）
| 闸门 | 命令 | 结果 |
|---|---|---|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | 绿（U11 仅文档，未改契约） |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | 绿（未改 PRD/HLD） |

## 2. 全局一致性核查（U1–U11 抽样）
| 模式 | 覆盖屏 | 结论 |
|---|---|---|
| 加载态 Skeleton | U2/U3/U8/U9 | ✅ 均有骨架/loading |
| 错误态 + 重试 | U2/U3/U8/U9 | ✅ 错误态 + 重试入口 |
| 空态引导 | U2/U8/U9 | ✅ 空态说明 + 操作 |
| 确认闸门 Modal ≤90vw | U5/U7/U8/U10 | ✅ 二次确认，宽度合规 |
| 撤销 5s | U5/U8 | ✅ Toast 内嵌撤销 |
| 无障碍 色+文字 | U5/U8 级别 chip | ✅ 双标识 |
| 响应式 R1–R7 | U1–U10 | ✅ 已注入 @media（U1–U6 修复 + U7–U10 原生） |
| reduced-motion | 全部 | ✅ 全局降级 |

## 3. 红线核查（REVIEW-3）
- 总纲为设计规范，无运行态；U10 未登录不暴露业务数据、U7 无真实支付密钥、U8 A23 仅模拟。✅ 不触发红线。

## 4. 遗留项（非阻塞）
- 模式抽为共享组件库属 V 阶段；功能测试覆盖确认/撤销/降级属 T 阶段。

## 结论：PASS ✅（双闸门绿 + U1–U11 全局交互一致 + 红线不触发）
