<!--
TRACE-BLOCK
role: QA(QA Engineer)
package: U10 用户与登录 UI (A01/A02/A03)
upstream_read: [design/ui/roles/U10-pm.md, design/ui/roles/U10-arch.md, design/ui/interaction-U10.md, design/ui/screens/U10-auth.html, design/ui/UI-SELFCHECK.md §3]
downstream_write: []
status: DONE（Team Lead 代笔）
-->
# U10 用户与登录 · QA 核查报告（A01/A02/A03）

## 1. 双闸门（REVIEW-1，实跑）
| 闸门 | 命令 | 结果 |
|---|---|---|
| gate1 契约校验 | `design/contracts/validate_contracts.py` | 绿（仅新增 UI） |
| gate2 PRD-HLD 追溯 | `design/check_prd_hld_traceability.py` | 绿（未改 PRD/HLD） |

## 2. UI 一致性 + 无障碍
- 复用 Card/Button/Input/Tabs/Toast/ProgressBar；新增 AuthGuard/LoginCard 命名一致。✅
- 错误提示 `aria-live`；表单 label 关联。✅
- **红线核查（REVIEW-3）**：本原型严格遵循 PRD §797——未登录仅展示引导页、不暴露业务数据；令牌仅存本机（模拟），无真实凭据/部署。✅ 不触发红线。

## 3. 响应式三端自查（R1–R7）
| 项 | 375 | 768 | 1280 | 结论 |
|---|---|---|---|---|
| R1 无横溢 | ✅(max-width 480 居中) | ✅ | ✅ | PASS |
| R2 无重叠 | ✅ | ✅ | ✅ | PASS |
| R3 单列 | ✅ | ✅ | ✅ | PASS |
| R4 按钮≥40px | ✅(44-46px) | ✅ | ✅ | PASS |
| R5 模态 | 无模态 ✅ | ✅ | ✅ | PASS |
| R6 导航可达 | Tab 可达 ✅ | ✅ | ✅ | PASS |
| R7 reduced-motion | ✅ | ✅ | ✅ | PASS |

## 4. 遗留项（非阻塞）
- 真实 OAuth/微信扫码、A02 拦截器、多设备互斥后端实现属 V 阶段；本包仅 UI 与本地模拟。

## 结论：PASS ✅（双闸门绿 + 响应式 R1–R7 全 PASS + 红线不触发）
