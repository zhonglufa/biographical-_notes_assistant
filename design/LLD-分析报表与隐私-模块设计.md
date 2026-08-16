# LLD：分析报表与隐私（防重识别）模块设计（v1.0）

> 文档版本：2026-08-16 · v1.0（闭合 HLD §9.4 §31.10「分析数据隐私（防重识别）」）
> 编写依据：LLD 交付标准（IEEE 1016-2009 / GB-T 8567—2006 / Amazon LLD 模板）
> 关联上游：HLD §6.13.5.3（分析隐私 k=50 已注册为设计约束，PRD §31.10 深化）；HLD §5.1/§5.2（核心实体与字段）；`LLD-数据库设计-模块设计.md`（聚合源表）；`design/contracts/`（错误码注册表）
> 定位：报表聚合**查询层** + 隐私保护，不新增业务存储表（落实「默认不产细粒度 per-user 统计」，聚合基于现有业务表）
> 作者：资深架构师（AI 协作）

---

## 0. 为什么单独成档

HLD §6.13.5.3 已把「分析隐私 k=50」从延后项提升为**设计约束**提前注册，要求 LLD 报表模块必须遵守、不得绕过。但 §9.4 此前仍把 §31.10 整体标为「待 LLD 细化」——这是状态标注不一致（本次 v3.22 对齐审计已修正）。本档把该约束落成可验证实现，使 §31.10 进入「部分闭环」。

> 说明：§31.10 的「防重识别」核心（k=50 抑制 + 差分隐私）已在本档闭环；与之无关的用户侧「我的数据」明细视图（per-user 本人视角）不受 cell suppression 约束，但同样不对外聚合、不进入分析报表，由前端/权限模块保证。

## 1. 范围

| 项 | 范围 | 非范围 |
| --- | --- | --- |
| 输入 | 服务端 MySQL 业务表（见 §3 源表） | 本机 SQLite 本地库（不跨设备聚合） |
| 处理 | 聚合查询层 + 两道隐私闸门（cell suppression + 差分隐私） | 实时 OLTP 写入、细粒度 per-user 统计产出 |
| 输出 | 对外/分析报表小计（已抑制 + 已加噪） | 原始记录导出（受 §31.11 被遗忘权 + §25.6 数据携带权约束，另行闭环） |

不新增存储表：报表为查询派生，结果可缓存但非权威源；缓存键须包含 `(维度组合, k, ε, 噪声种子)` 以保证同参数可复现。

## 2. 两道隐私闸门（落实 HLD §6.13.5.3）

### 2.1 闸门一：Cell Suppression（k-anonymity，k=50）

- **规则**：任一聚合分组（含嵌套小计）的组大小 `< k` 时，该 cell **直接抑制不展示**（返回 `null` 或占位 `—`），不降级为「少量」近似。
- **嵌套检查**：带小计的层级报表（如「城市→行业」两级），每一级分组均独立判定 `COUNT >= k`；上级小计若依赖被抑制子项，则上级同样抑制（避免从上级反推下级）。
- **k 默认值 50**，由配置中心可调（见 §5），但**只能上调不能下调**（下限锁 50，防止运营为「好看」调小）。

伪代码：
```
def aggregate(rows, dims, k=50):
    groups = group_by(rows, dims)
    result = []
    for g_key, g_rows in groups:
        if len(g_rows) < k:
            result.append(suppress(g_key))   # 抑制，不展示
            continue
        result.append(compute(g_rows))       # 进入闸门二
    return enforce_nested(result, k)         # 上级依赖被抑制子项则级联抑制
```

### 2.2 闸门二：差分隐私噪声（Laplace / Gaussian）

- **适用**：通过闸门一的聚合**小计/连续值**（如投递成功率、平均评分），注入可控噪声。
- **机制**：默认 **Laplace**（连续值，敏感度 Δf 易界定）；可选 **Gaussian**（需严格 (ε,δ)-DP 时使用，δ 默认 ≤ 1e-6）。
- **尺度**：Laplace 噪声 `scale = Δf / ε`；Δf = 单条记录对聚合值的最大影响（如比率类 Δf=1/n_group，计数类 Δf=1）。
- **ε 全局预算**：设全局隐私预算池（默认候选 `ε_total = 1.0`），按报表子项拆分（每报表子预算 `ε_i`，Σε_i ≤ ε_total）；预算耗尽的新报表须复用已分配或申请扩容（架构评审）。
- **非 per-user**：噪声仅作用于**对外/分析聚合小计**，绝不作用于用户本人「我的数据」视图。
- **边界处理**：比率/百分比加噪后若越界（<0 或 >1/100%），clip 到合法区间并标记 `degraded=true`；计数加噪后四舍五入取整、下限 0。

## 3. 报表聚合查询设计（源表对齐数据库设计 LLD）

聚合基于现有业务表，**不加新表**。主要源表与维度：

| 源表（服务端） | 主要维度 | 典型聚合 |
| --- | --- | --- |
| `application` | `platform_id` / `city` / `job_category` / `date(apply_date)` / `status` | 投递量、各状态占比、成功率 |
| `interview_evaluation` | `date` / `job_category` / `platform_id` | 平均 `weighted_score`、各维度均分 |
| `daily_report` | `date` / `user_segment` | 日活、投递趋势 |
| `notification_stat` | `channel` / `date` | 到达率、点击率 |
| `user` | `city` / `segment` / `created_date` | 注册分布、留存 |

**示例（城市×行业 投递成功率，带抑制 + 加噪）**：
```sql
SELECT city, industry,
       COUNT(*)                         AS grp_size,
       SUM(CASE WHEN status='offer' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS offer_rate
FROM application
WHERE apply_date BETWEEN :start AND :end
GROUP BY city, industry
HAVING COUNT(*) >= :k;          -- 闸门一：组大小 < k 直接剔除（不返回）
```
> 应用层对通过 `HAVING` 的结果再施加 §2.2 噪声（SQL 仅做筛选，噪声在应用层注入以便复用 ε 预算与种子）。

## 4. 噪声注入实现要点

- **RNG**：使用密码学安全随机数（`os.urandom` 派生 / `secrets`）生成 Laplace/Gaussian 样本；**可复现种子**由配置中心下发（同 `(维度, k, ε, seed)` 产出同结果，便于审计与回归）。
- **预算分配**：全局 `ε_total` → 每报表 `ε_i` 静态分配表（配置中心），新增报表须登记预算，超限拒绝发布（fail-closed）。
- **记录**：每次加噪记录 `(report_id, dims, k, ε_i, mechanism, seed_hash, scale)`，供审计追溯与方差校验。

## 5. 配置中心参数（默认档，编码期可调，下限锁）

| 参数 | 默认 | 下限锁 | 说明 |
| --- | --- | --- | --- |
| `privacy.k` | 50 | 50（不可下调） | cell suppression 阈值 |
| `privacy.epsilon_total` | 1.0 | 0.1 | 全局差分隐私预算 |
| `privacy.mechanism` | laplace | — | laplace / gaussian |
| `privacy.delta`（gaussian 时） | 1e-6 | — | (ε,δ)-DP 的 δ |
| `privacy.enforce` | true（生产强制） | — | 调试可临时 false，但**审计标记 bypass**，生产环境强制 true |

## 6. 抑制与隐私事件审计

- 每次报表生成记录**抑制事件**入 `audit_log`（维度组合、被抑制组大小、时间、操作人/系统），不记录被抑制的具体内容（避免间接泄露）。
- 监控指标：**抑制率**（被抑制 cell / 总 cell），异常升高（如 >30%）触发告警（可能暗示维度过细或数据稀疏）。
- 与 `LLD-密钥与凭证工程` 无关（报表层不接触 Cookie/KEK）；与数据库设计 LLD 审计字段（§1426 统一审计日志）对齐。

## 7. 与错误码 / 契约对齐

- `design/contracts/error-codes.json` 无专门隐私错误码；预算超限/配置 bypass 复用通用 `CONFIG_INVALID` / `POLICY_VIOLATION` 类（若有），本档不新增错误码。
- 报表为内部聚合查询，**不纳入公开 API 契约**（openapi.json 未含报表端点，符合 §4 范围）；若未来对外暴露分析 API，须先补契约 + 在闸门外再加 API 级限流。

## 8. 测试与验收

| 用例 | 期望 |
| --- | --- |
| k 边界：组大小 49 / 50 / 51 | 49 抑制、50 与 51 通过闸门一 |
| 嵌套小计依赖被抑制子项 | 上级级联抑制 |
| 差分隐私：同参数重复运行 | 输出一致（种子可复现）；不同 seed 方差符合 `2*(Δf/ε)^2`（Laplace） |
| 比率加噪越界 | clip 到 [0,1] 且 `degraded=true` |
| `privacy.enforce=false` 生产 | 审计标记 bypass，告警 |
| k 配置下调 < 50 | 拒绝（下限锁） |

## 9. 自检：对齐点清单

- [x] 与 HLD §6.13.5.3 对齐：k=50 cell suppression + Laplace/Gaussian 噪声 + 默认不产 per-user 统计，已全部落成可验证实现。
- [x] 与数据库设计 LLD 对齐：聚合源表 `application` / `interview_evaluation` / `daily_report` / `notification_stat` / `user` 均为该档定义的服务端表，未引入新表。
- [x] 与 contracts 对齐：不新增错误码、不新增公开 API 契约。
- [x] 与 §9.4 状态对齐：§31.10 由「待 LLD 细化」修正为「部分闭环」（核心约束已注册 + 本档落细）。
