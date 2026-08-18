# 护栏4 · 灰度开关 + 回滚预案（Runbook）— Q2

> 阶段：D（Q2，R1 合规基座，循环可自驱）｜关联：`scaffold/src/feature_flags.py`（开关编排，已落地单测）
> 诚实边界：灰度**策略取值**（百分比/白名单）属运维/业务决策，默认保守（0%）；真实「谁来改开关、谁来审计」属 Q5 上线物理动作与 Q4 法检范畴。**物理灰度开关启用仍仅用户触发**。

## 1. 目标
新功能上线不一次性全量；经灰度逐步放量，异常可一键回滚（kill-switch）。对齐行业 release-gating 实践（渐进交付 / feature flag / 紧急止血）。

## 2. 开关模型（`feature_flags.py`）
- 每个功能一个 flag，**默认 False（fail-safe）**：未显式灰度开启不生效。
- 维度：白名单（user_id 列表）/ 百分比（pct:N）/ 全局 override。
- **kill-switch（全局回滚）**：`trigger_kill_switch(True)` → 所有灰度功能强制关闭，优先于一切 override。
- 运行时 override 持久化到本地覆盖文件，重启仍生效（紧急止血可审计）。

## 3. 灰度流程（Runbook）
```
1. 代码合入（feature flag 包裹新功能，默认 off）
2. 合并后 CI 绿（ci-cd.yml 已含 build+test+契约闸门）
3. 内部灰度：override 开启白名单（内部账号）观察 24h
4. 小流量：pct:5 → pct:20 → pct:50（每档观察核心指标：投递成功率/封号率/LLM成本/错误率，见 O3 监控）
5. 全量：pct:100；保留 kill-switch 7d
6. 回滚：指标越阈值 → trigger_kill_switch(True) → 功能全关，不回滚代码
```
## 4. 回滚触发阈值（建议值，待运维定稿）
| 指标 | 回滚阈值 |
|---|---|
| 投递成功率 | < 90% 持续 10min |
| 单平台封号率 | > 2% / 平台·日 |
| LLM 成本 | 超护栏2 硬上限（cost_policy） |
| 5xx 错误率 | > 1% 持续 5min |

## 5. 验收
- [x] 开关编排逻辑单测通过（test_guardrails.py::test_feature_flags）
- [ ] 灰度策略取值（百分比/白名单）由运维在发布前配置（用户决策点）
- [ ] kill-switch 联调（管理端点触发 → 功能全关）
- [ ] Runbook 演练一次
