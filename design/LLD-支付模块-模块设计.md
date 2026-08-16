# LLD 详细设计：会员支付模块（服务端 Java）

> 文档版本：2026-08-16 · v1.0（交付级 LLD；闭合 HLD §9.4「§25.4 退款/试用/退订工作流」待 LLD 细化项 + 审查报告 P0 支付缺口，闭合 R-04 资损级风险）
> 编写依据：LLD 交付标准（IEEE 1016-2009 设计视图 / GB-T 8567—2006 详细设计 / Amazon LLD 模板）
> 关联上游：HLD v3.23（§3.10 会员支付模块 / §4.10 支付渠道回调契约 / §7.5 支付与会员异常 / §9.4 §25.4 / 错误码 §923–925·§962–964 / C5 `member.plan.changed` / §6.5 O 第三方依赖韧性 / §5.1 实体 ⑤ `MEMBER_ORDER` / §1242）× PRD v4.5 §22.2 支付对账掉单 / §12 定价与全局异常 / §20.2 订阅状态机 / §20.3 / §24.8 支付多扣 Runbook / §25.4 退款试用退订 / §31.2 同步 / §17.1·§32.1 风险定级
> 定位：LLD 序列之**会员支付模块**（服务端 Java Spring Boot，ADR-002 双语言异构中的业务服务侧）；与「用户与权限模块」(§3.1) 经 C5 事件衔接、与「通知推送模块」(§3.11) 经内部调用衔接
> 作者：资深架构师（AI 协作）

---

## 0. 模块定位与边界

支付模块是系统**资金链路的唯一权威**（R-04 资损级），统一承接：会员订单创建、支付渠道回调接收与对账、权益激活（仅产出事件）。核心约束（来自 HLD §3.10 / ADR-002 / I6 fail-closed）：

- **执行侧 = 服务端 Java（Spring Boot）**：订单状态机、回调验签、对账、退款、续费计费均在此侧；**不承载浏览器自动化**（已下沉本机 Agent，ADR-003），**不经本机 Agent**（HLD §4.10：渠道回调直连服务端）。
- **权益判定不在本模块**：只产出 `member.plan.changed` 事件（C5），由用户权限模块（§3.1）据此实时生效权益矩阵（HLD §3.10 边界 / §400）。
- **资损高危、fail-closed（I6）**：任何不确定状态不发货、不重复扣、不静默放行；对账异常暂停权益激活并告警。
- **双存储不冲突**：订单落服务端 MySQL（`member_order`）；用户 Cookie 密文只在本机，本模块不接触。

调用边界总览：

```
客户端 ──(A20 POST /payments/orders, Bearer)──> 支付模块(Java)
渠道 ──(A21 POST /api/v1/payments/callback, 渠道非对称签名)──> 支付模块(Java)
支付模块(Java) ──(C5 member.plan.changed)──> 用户权限模块(§3.1)
支付模块(Java) ──(定时 15min 对账: 拉渠道对账单)──> 微信/支付宝 bill API
支付模块(Java) ──(内部调用 续费提醒/退款通知)──> 通知推送模块(§3.11)
Redis(订单幂等锁)  ◀── 支付模块(Java)
```

---

## 1. 订单状态机（核心，PRD §22.2 五态）

**Canonical 五态 + 终态**（对齐 PRD §22.2「待支付→已支付→已开通→已过期→已退款」+ 未支付逾期终态）：

`pending(待支付) → paid(已支付) → activated(已开通) → expired(已过期) → refunded(已退款)`，外加终态 `closed(关闭，未支付逾期/作废)`。

| 转移 | 触发 | 守卫 / 动作 |
|------|------|------------|
| `pending → paid` | 渠道回调 `SUCCESS` 或 对账命中 | 幂等 by `order_no`；写 `paid_at`（渠道时间戳） |
| `pending → closed` | 超过 24h 未支付（定时扫描，PRD §12） | 未扣款，不退款；释放套餐占用配额 |
| `paid → activated` | 权益激活成功（发 C5 后） | 发 `member.plan.changed{plan, effectiveAt, orderNo}`；**激活失败则留在 `paid` 重试，不发货** |
| `activated → expired` | 套餐周期结束（含试用到期） | 触发续费流程或进入 grace |
| `activated → refunded` | 退款成功（经对账通道原路退回） | 发 `member.plan.changed{plan=free}` 回收权益 + 退款通知 |
| `expired → activated` | 续费扣费成功 | 新周期生效（renewal success） |
| `expired → downgraded` | 宽限期满未续费 | 权限模块响应 `member.plan.changed{plan=free}`，不删数据 |
| `any(已扣款) → refunded` | 退款 | 仅当 `paid/activated`；`pending/closed` 不可退款 |

> **二分设计（paid vs activated）**：回调确认收款（`paid`）与权益实际生效（`activated`）分离，使「收款成功但权益激活失败」可安全重试而不重复发货——这是 R-04 资损防护的关键不变量。

---

## 2. 下单流程（A20 `POST /api/v1/payments/orders`）

- **鉴权**：`Bearer`（JWT access≤15min，HLD §989）。
- **请求体**（机器可读：`payments-order.request.schema.json`）：`{ plan: enum(pro|team), months: int(1..12), couponCode?: string }`。
- **处理**：
  1. 校验套餐有效性（服务端权威价目表，绝不从客户端取价）。
  2. 计算 `amount`（整数**分**，按 `套餐单价 × months − 优惠`）；客户端只传 `plan/months`，金额服务端定。
  3. 校验重复未支付订单：同 `(user_id, plan, status=pending)` 存在 → 复用既有 `order_no`（或拒绝），避免重复建单。
  4. 写 `member_order(status=pending, expire_at=now+24h)`，生成 `order_no`（uk）。
  5. 返回（机器可读：`payments-order.response.schema.json`）：`{ orderNo, payUrl(渠道收银台), amount(分), expireAt(epoch ms) }`。
- **防**：金额客户端不可篡改；`order_no` 全局唯一；24h 未付 → `closed`（§1）。

---

## 3. 支付回调契约（A21 `POST /api/v1/payments/callback`，资损高危，HLD §4.10）

- **鉴权**：渠道非对称签名验签（微信 `Wechatpay-Signature` / 支付宝 `sign` + 平台公钥），**不用 Bearer**；验签失败返回 `400` 且不上状态（HLD §1050）。
- **请求体**（机器可读落盘：`payments-callback.request.schema.json`，源自 HLD §4.10 内联 schema）：
  `{ channel: enum(wechat|alipay), outTradeNo: string(order_no), transactionId: string, tradeStatus: enum(SUCCESS|CLOSED|REFUND), amount: int(分), sign: string, timestamp: int64 }`。
- **处理顺序**（fail-closed，任何不确定→不发货）：
  1. **验签**：失败 → `400 PAY_SIGN_INVALID`，不上状态，不回执成功（渠道按自身策略退避重推）。
  2. **单号校验**：`outTradeNo` 在 `member_order` 不存在 → `200` 已接收 + **告警人工**（标记可疑/错配，防伪造），不发货、不建单（避免渠道重试风暴）。
  3. **金额比对**：回调 `amount`(分) ≠ 订单 `amount`(分) → `400 PAY_AMOUNT_MISMATCH`，**告警人工**，不发货。
  4. **幂等**：以 `outTradeNo`(=order_no) 唯一键；已处理（`paid/activated`）→ `200 PAY_DUPLICATE`（retryable=false），不重复发货/改权益。
  5. **状态映射**：`SUCCESS → paid → activated + 发 C5`；`CLOSED → closed`（未支付关闭）；`REFUND → refunded + 发 C5(plan=free)`。
- **读写**：回调后强制读主库（ADR-003 读写分离例外，HLD §1110）。

---

## 4. 对账工作流（15min，掉单兜底，PRD §22.2 + HLD §6.5 O）

- **调度**：定时任务每 15min 拉渠道对账单（微信/支付宝 bill API）覆盖上一窗口。
- **双源校验（webhook + polling）**：回调即时更新；轮询兜底——webhook 丢失时 15min 内轮询补单（PRD §31.2 / §1900）。
- **比对逻辑**：
  - 渠道已支付 & 本地 `pending` → **补单**：置 `paid→activated` + 发 C5（掉单修复）。
  - 渠道 `REFUND` & 本地 `activated` → 置 `refunded` + 发 C5(plan=free) + 退款通知。
  - 本地 `paid` & 渠道无记录（超时）→ 转「待确认」**不重复扣**（续费场景同）；持续无凭证超阈值 → 告警人工。
  - 渠道有扣款 & 本地无订单（差额>0）→ **告警 + 人工核实**（防伪造/错配），不直接建单发货。
- **SLA/容错**：差异 ≤15min 内告警（§4.10）；兜底原路退回 + T+3 到账，不产生不可逆资损；对账异常 fail-closed（I6）——暂停权益激活并告警，不静默放行（HLD §648）。

---

## 5. 退款工作流（§25.4 + §22.2）

- **触发（PRD §25.4）**：
  - 7 天无理由退款：付费后 7 天内且自动投递完成量 <10 份（产品问题导致）支持退款，超量按天折算。
  - 试用退款：7 天试用期内未达套餐日投递上限 50% 可退。
  - 功能不可用退款。
- **流程**：退款经对账通道执行（原路退回），记录 **Refund 状态机**：`created → submitted(channel) → success / failed(retry) → closed`。
- **防重复退**：以 `order_no + 退款批次` 幂等；对账核对无掉单 / 重复退（§25.4 验收标准）。
- **SLA**：原路退回 T+3 内到账；退款成功后订单置 `refunded` + 发 C5(plan=free) 回收权益 + 退款通知。
- **降级/冻结**：高级降专业版多出版本冻结不删（§25.4）；退款不删用户数据。

---

## 6. 自动续费与宽限期（§12 + §20.2）

- **提醒**：订阅周期结束前尝试扣费；扣费前 3 天发续费提醒（通知模块，L1 重要级，PRD §871·§1170）。
- **grace**：扣费失败 → 进入 **7 天宽限期**（grace），功能不受影响，关键节点提醒；宽限期内成功扣费 → 续期 `activated`。
- **降级**：宽限期满未恢复 → 降级免费版（权限模块响应 `member.plan.changed{plan=free}`），不立即停服、不删数据（§25.4）。
- **双源校验**：续费场景同样适用「超时转待确认不重复扣」（§31.2）。
- **续费失败信号**：支付模块内部发 `member.renewal.failed`（**待注册 typed event**，见 §11 待决 T-PAY-1）——驱动通知 + 权限 grace；当前作内部信号，不阻塞本版。

---

## 7. 幂等与资损防护

- **Redis 订单幂等**（HLD §3.10 依赖）：`order_no → 处理锁 + 处理状态`；回调并发/重推安全。
- **DB `uk(order_no)`** 最终约束；回调以渠道为准（PRD §12「以支付平台回调为准」）。
- **金额服务端权威**：下单算价、回调比价；客户端不传金额。
- **读写**：支付回调后强制读主库（ADR-003）。
- **掉单/多扣**：对账兜底（§4）；支付多扣 Runbook（§24.8）暂停计费 + 对账补单/退款。

---

## 8. 事件契约

- **C5 `member.plan.changed`**（已注册，HLD §876）：`{ userId, plan: enum(free|pro|team), effectiveAt, orderNo }`；按 `orderNo` 去重；强一致（影响权益），失败阻塞重试。触发时机：`paid→activated`、`refunded`、`renewal success`、`downgrade`。
- **`member.renewal.failed`**（待注册，§11 T-PAY-1）：续费扣费失败时驱动通知 + 权限 grace。

---

## 9. 错误码域 `PAY_*`（已注册于 `error-codes.json`，HLD §923–925·§962–964）

| 码 | HTTP | retryable | 语义 | 处理 |
|----|------|-----------|------|------|
| `PAY_SIGN_INVALID` | 400 | false | 支付回调签名验签失败 | 不上状态，渠道退避重推 |
| `PAY_DUPLICATE` | 200 | false | 支付幂等冲突（重复回调） | 已处理，不重复发货 |
| `PAY_AMOUNT_MISMATCH` | 400 | false（告警人工） | 回调金额与订单不符 | 不发货，人工核实 |

- 下单 / 查询级错误复用通用码（`NOT_FOUND` / `VALIDATION` 等）；如需专用 `ORDER_*` 码，登记 `error-codes.json`（待决，§11 T-PAY-2）。

---

## 10. 数据表对齐与缺口登记（非静默）

- 本模块持久化：`member_order`（HLD §5.1 实体 ⑤ / 数据库设计 LLD）。
- **缺口（已发现，显式登记）**：数据库设计 LLD `member_order.status` 当前枚举为 `('pending','paid','refunded','closed')`，**缺 PRD §22.2 canonical 五态中的 `activated` 与 `expired`**。建议修正为：
  `ENUM('pending','paid','activated','expired','refunded','closed')`（保留 `closed` 作未支付逾期终态）。
  → 本 LLD 已据此建议更新 `LLD-数据库设计-模块设计.md` §3.1 的 DDL（补 `activated`/`expired`）。
- **金额单位约定**：渠道回调 `amount` 为整数**分**（§4.10）；订单内部 `amount` 建议统一以分存储或明确 DECIMAL 元↔分换算；DB 当前 `DECIMAL(10,2)` 元，回调比对需显式换算，已在 §2/§3/§4 注明（待决 T-PAY-3）。
- **机器可读契约索引**（均纳入 `validate_contracts.py` 双闸门）：
  - `payments-order.request.schema.json`（A20 请求，由 outlined 升 detailed）
  - `payments-order.response.schema.json`（A20 响应）
  - `payments-callback.request.schema.json`（A21 请求体落盘 §4.10）

---

## 11. 待决项登记（非静默，不覆盖）

| 项 | 状态 | 说明 |
|----|------|------|
| T-PAY-1 `member.renewal.failed` 是否注册为 typed event | 待决 | 当前作内部信号；若采用 typed event 需补 §4.6 + event-envelope + schema |
| T-PAY-2 `ORDER_*` 专用错误码是否登记 | 待决 | 当前复用通用码；登记进 `error-codes.json` |
| T-PAY-3 金额存储单位（分整数 vs 元 DECIMAL）最终约定 | 待决 | 编码期配置中心确认，影响 DB 列与比对换算 |
| T-PAY-4 对账窗口与渠道 bill API 字段映射 | 待决 | 编码期对接微信/支付宝文档 |

---

## 12. 机器可读契约索引

| 文件 | 用途 |
|------|------|
| `payments-order.request.schema.json` | A20 创建订单请求 |
| `payments-order.response.schema.json` | A20 创建订单响应 |
| `payments-callback.request.schema.json` | A21 支付渠道回调请求体（HLD §4.10 落盘） |
| `error-codes.json`（PAY_* 三段） | 错误码注册表（已存在，本 LLD 引用） |
| `external-api.registry.json`（A20/A21） | A 层端点注册表（A20 由 outlined 升 detailed） |

契约版本协商沿用 HLD §6.13.4：服务端/调用方 `contractVersion` 不匹配返回 `426 Upgrade Required` + 最低兼容版本，消费者（Pact）驱动契约纳入 CI。
