# 可观测性模块 LLD（v1.0）

> 文档版本：2026-08-16 · v1.0 · 依据 HLD v3.32 / PRD v4.5
> 评审来源：设计评审清单 🟡 F-06 / H3 / H7 / 风险登记表 R-05（日志 schema 落库）
> 定位：闭环 R-05——定义结构化日志 schema、落库方案、SLI/SLO、指标与追踪。HLD §31.5 已有框架，本文补落库 schema 与指标定义。
> 关联：`部署运维手册.md` §5.2（SLI/SLO + deadman）、`测试计划.md` §1（安全/混沌层）。

---

## 1. 结构化日志 Schema（落库）

统一 JSON 日志，字段约束（与 `samples.json` 同机器可校验思路，后续出 schema）：

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| `ts` | string(UTC ISO8601) | 时间戳 | 必填 |
| `level` | enum | DEBUG/INFO/WARN/ERROR | 必填 |
| `service` | string | 服务名（agent/java-llm/mq-gateway/pay） | 必填 |
| `trace_id` | string | 链路追踪 ID（OpenTelemetry） | 选填 |
| `user_id` | string(hash) | **哈希化**，禁止明文 PII | 选填，必哈希 |
| `event` | string | 事件名（如 delivery.confirmed） | 必填 |
| `attrs` | object | 结构化附加字段 | 选填，禁含明文凭证/简历全文 |

- **脱敏规则**：`user_id` 一律哈希；Cookie/简历全文/密钥**禁止入日志**；敏感字段正则扫描拦截（威胁模型 I 维度）。
- **落库**：服务端日志 → Kafka → 存储（MySQL 归档表 / 或 ClickHouse 供查询）；本机 Agent 日志本地落盘 + 受控上报（不上报明文凭证）。

---

## 2. 指标（Prometheus）

| 指标 | 类型 | 维度 | 说明 |
|------|------|------|------|
| `delivery_total{status}` | counter | status=success/failed | 投递量 |
| `match_latency_seconds` | histogram | — | 匹配耗时 |
| `adapter_available_ratio{platform}` | gauge | platform | 适配器可用率（DOM 解析成功率） |
| `pay_reconcile_lag_seconds` | histogram | — | 支付对账延迟 |
| `agent_online` | gauge | — | 本机 Agent 在线数 |
| `llm_fallback_total` | counter | — | LLM 降级触发次数 |

---

## 3. SLI / SLO

| SLI | SLO 目标 | 窗口 | 告警 |
|-----|----------|------|------|
| 投递成功率 | ≥99.5% | 30d | <99% 触发 |
| 匹配 P95 延迟 | ≤2s | 7d | >5s 触发 |
| 适配器可用率（单平台） | ≥95% | 7d | <90% 触发（联动单平台降级 §31.3） |
| 支付对账延迟 | ≤15min | 实时 | 超 15min 掉单兜底触发 |
| 本机 Agent 在线率 | ≥99% | 7d | deadman（无心跳 >10min 告警） |

- **deadman 告警**：若指标流中断（无数据），主动告警（防「无告警=正常」假象，运维手册 §5.2）。

---

## 4. 追踪（OpenTelemetry）

- 跨本机 Agent → 服务端 → MQ → LLM 网关的 `trace_id` 串联；关键路径（采集→匹配→确认→回写→通知→日报）可全链路追因。
- 采样：关键业务 100%，批量任务 1/100。

---

## 5. 看板与告警

- 看板：投递总览 / 适配器健康 / 支付对账 / Agent 在线 / LLM 降级。
- 告警分级：SEV1（支付对账超窗/大规模封禁）→ 呼叫；SEV2（SLO  breach）→ 群告警；SEV3（单平台降级）→ 记录（运维手册 §24）。

---

## 6. 与现有设计对齐

- 闭环 R-05（日志 schema 落库）：原 §5.2 仅框架，本文补 schema + 指标 + SLO。
- 风险登记表 R-05 由「[LLD 细化]」升「[已缓解-设计态]」（落库 schema 已定，待编码期实现）。
- 对接 `部署运维手册.md` §5.2 SLI/SLO + deadman。

---

## 7. 验收（编码期）

- [ ] 日志 schema 出 JSON Schema 并入 `validate_contracts.py` 校验（防 PII 入日志）。
- [ ] Prometheus 指标 + Grafana 看板上线，SLO 告警 + deadman 生效。
- [ ] OpenTelemetry 串联关键链路 demo 通过。

---

> 结论：R-05 设计态闭环——结构化日志 schema、指标、SLO、追踪、看板告警均已定义；**待编码期实现并接入双闸门校验**，不阻塞编码启动。
