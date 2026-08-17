# A 层接口落地索引（Implementation Index）

> 映射：**契约 ID → 桩文件(stubs/) → 真实实现(待 B 阶段) → 契约 schema 状态**。
> 自动发现机制：`stubs/__init__.py` 扫描本包所有 `*.py` 汇总 `ENDPOINTS`，
> **新增模块 = 新建一个 `stubs/<module>.py`，无需改任何共享文件**（并行安全）。

图例：
- `✓` = `design/contracts/` 下已有对应 schema 文件（契约已 machine-readable）。
- `None(无体)` = 无请求体 GET 端点，入参校验跳过。
- `pending` = 该端点的 ref 指向 HLD 章节（如 `HLD §4.2`）或尚无 schema 文件；
  桩侧将缺失一侧填 `None`（**不伪造契约**），待 B 阶段补 schema。

| 契约ID | 方法/路径 | 模块文件 | 端点 name | 请求 schema | 响应 schema | 真实实现(待 B) | 状态 |
|--------|-----------|----------|-----------|-------------|-------------|----------------|------|
| A01 | POST /auth/login | stubs/auth.py | A01 auth-login | auth-login.request ✓ | auth-login.response ✓ | 服务端 Auth | 桩✅ |
| A02 | POST /auth/refresh | stubs/auth.py | A02 auth-refresh | auth-refresh.request ✓ | auth-refresh.response ✓ | 服务端 Auth | 桩✅ |
| A03 | GET /users/me | stubs/user.py | A03 users-me | None(无体) | user-me.response ✓ | 服务端 User | 桩✅ |
| A04 | POST /resumes | stubs/resume.py | A04 resumes-create | resumes-create.request ✓ | resumes-create.response ✓ | 服务端 Resume | 桩✅ |
| A05 | GET /resumes/{id}/versions | stubs/resume.py | A05 resumes-versions | None(无体) | resume-versions.response ✓ | 服务端 Resume | 桩✅ |
| A06 | POST /resumes/{id}/ats | stubs/resume.py | A06 resumes-ats | resume-ats.request ✓ | resume-ats.response ✓ | 服务端 Resume | 桩✅ |
| A07 | GET /jobs | stubs/jobs.py | A07 jobs-search | jobs-search.request ✓ | jobs-list.response ✓ | 服务端 Jobs | 桩✅ |
| A08 | POST /jobs/{id}/favorite | stubs/jobs.py | A08 jobs-favorite | jobs-favorite.request ✓ | jobs-favorite.response ✓ | 服务端 Jobs | 桩✅ |
| A09 | POST /applications/batch | stubs/applications.py | A09 applications-batch | None(HLD§4.2) | None(HLD§4.2) | 服务端 Applications | 桩✅(req/resp schema pending·HLD§4.2) |
| A10 | GET /applications | stubs/applications.py | A10 applications-list | None(无体) | applications-list.response ✓ | 服务端 Applications | 桩✅ |
| A11 | GET /applications/{id} | stubs/applications.py | A11 applications-detail | None(HLD§4.3) | None(HLD§4.3) | 服务端 Applications | 桩✅(resp schema pending·HLD§4.3) |
| A12 | GET /strategies | stubs/strategies.py | A12 strategies-get | None(无体) | strategies.response ✓ | 服务端 Strategies | 桩✅ |
| A13 | PUT /strategies | stubs/strategies.py | A13 strategies-update | strategies.request ✓ | strategies.response ✓ | 服务端 Strategies | 桩✅ |
| A14 | GET /adapters | stubs/adapters.py | A14 adapters-list | None(HLD§4.4) | None(HLD§4.4) | 服务端 Adapters | 桩✅(req/resp schema pending·HLD§4.4) |
| A15 | POST /adapters/{id}/enable | stubs/adapters.py | A15 adapter-enable | adapter-enable.request ✓ | adapter-enable.response ✓ | 服务端 Adapters | 桩✅ |
| A16 | GET /interviews/questions | stubs/interview.py | A16 interview-questions | None(无体) | interview-questions.response ✓ | 服务端 Interview | 桩✅ |
| A17 | POST /interviews/sessions | stubs/interview.py | A17 interview-session-create | interview-session-create.request ✓ | interview-session-create.response ✓ | 服务端 Interview | 桩✅ |
| A18 | POST /interviews/sessions/{id}/answer | stubs/interview.py | A18 interview-session-answer | interview-session-answer.request ✓ | interview-session-answer.response ✓ | 服务端 Interview | 桩✅ |
| A19 | GET /interviews/sessions/{id}/report | stubs/interview.py | A19 interview-session-report | None(无体) | interview-session-report.response ✓ | 服务端 Interview | 桩✅ |
| A20 | POST /payments/orders | stubs/payments.py | A20 payments-order | payments-order.request ✓ | payments-order.response ✓ | 服务端 Payments | 桩✅ |
| A21 | POST /payments/callback | stubs/payments.py | A21 payments-callback | payments-callback.request ✓ | None(HLD§4.10) | 服务端 Payments | 桩✅(resp schema pending·HLD§4.10) |
| A22 | GET /notifications | stubs/notifications.py | A22 notifications-list | None(无体) | notifications-list.response ✓ | 服务端 Notifications | 桩✅ |
| A23 | GET /notifications/ws | stubs/notifications.py | A23 notification-ws | None(无体) | notification-ws.response ✓ | 服务端 Notifications | 桩✅ |
| A24 | GET /daily-report/today | stubs/dailyreport.py | A24 daily-report-today | None(无体) | daily-report-today.response ✓ | 服务端 DailyReport | 桩✅ |
| A25 | PUT /users/daily-report/preference | stubs/dailyreport.py | A25 daily-report-preference | daily-report-preference.request ✓ | daily-report-preference.response ✓ | 服务端 DailyReport | 桩✅ |

## 待补 schema（B 阶段或并行子代理落地时处理）
- **A09 / A11**：ref `HLD §4.2 / §4.3`，需从 HLD 提取请求/响应 schema 后落地严格校验。
- **A14**：ref `HLD §4.4`，同上。
- **A21 响应**：ref `HLD §4.10`，仅请求 schema 已存在，响应 schema 待补。
- **A10 请求**：GET 查询参数（platform/status/page/pageSize）暂无 body schema，
  桩侧 request_schema=None（查询参数不进 body 契约），如需严格可补 query schema。

> 索引与 `external-api.registry.json` 同源；registry 的 `contractStatus` 为
> `fully-detailed` 仅代表 A 层接口设计粒度，不等同于「桩已实现」——
> 本表的「状态」列才是桩落地真相。
