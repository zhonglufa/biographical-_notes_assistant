# API 契约文档（OpenAPI 3.1 + Mock）

由 [`../contracts/`](../contracts/) 下的**机器可读契约**自动导出，闭合 HLD §10「API 契约文档（含 Mock）」项。
源契约经 `../contracts/validate_contracts.py` 校验器闭环（schema 30 / 注册表 6 全绿）。

## 文件

| 文件 | 说明 |
| --- | --- |
| `openapi.json` | 导出产物（OpenAPI 3.1.0），可直接被 Swagger UI / Redoc / Prism / 代码生成器消费 |
| `gen_openapi.py` | 零依赖生成器（仅用 Python 标准库）。重生成：`python gen_openapi.py` |
| `README.md` | 本文件 |

## 覆盖率（41 个 operation / 39 个 component）

| 层 | 端点 | 契约严格度 | 来源 |
| --- | --- | --- | --- |
| **A 层 · 外部 API** | A01–A25（25 个 REST 端点） | `outlined`（human-readable 字段大纲 best-effort 解析，标 `x-contract-status: outlined`） | `external-api.registry.json` |
| **B 层 · AI 编排** | b01–b05（内部 REST） | **严格**（直引机器可读 `b0X-*.request/response.schema.json`，含 Mock 示例） | `ai-orchestrator.methods.json` + b0X schema |
| **面试模拟域** | 6 个 facade 方法（内部 REST） | `outlined`（getReport 响应直引 `interview-evaluation` 严格组件） | `interview-domain.methods.json` |
| **C 层 · 设备/支付（HTTP）** | device/register、device/token、device/token/revoke、device/handshake、payments/callback | `outlined`（由内联请求/响应字段字典解析） | `agent-server-rpc.methods.json` |
| **C 层 · WSS 双向 RPC** | serverToAgent 5 + agentToServer 5 | 非 HTTP，挂在 `info.x-agent-rpc` 扩展（信封：`rpc-envelope` / `event-envelope`） | 同上 |

统一信封与错误码一并纳入：`error-envelope`（§4.7）、`event-envelope`（§4.6）、`rpc-envelope`（§4.9）、23 个错误码（`error-codes.json` → `info.x-error-codes`）。

## 用法

### 1. 重新生成
```bash
python gen_openapi.py
```
生成器自带双闸门自检：① 全部 `$ref` 必须可解析（本版 77 处全解析）；② 无 `nullable` 残留（draft 2020-12 → OAS 3.1 联合类型转换）。任一失败即报错退出。

### 2. 可视化文档（任选其一）
- **Redoc**：`npx redoc-cli serve openapi.json`
- **Swagger UI**：用 `swagger-ui` 挂载 `openapi.json`
- 在线粘贴 `openapi.json` 内容到 https://editor.swagger.io 或 https://redocly.github.io/redoc/

### 3. Mock 服务（本交付的核心「含 Mock」）
```bash
npx @stoplight/prism mock -s openapi.json
```
Prism 会基于各 operation 的 schema（及 B 层嵌入的 `examples`）动态返回符合契约的 Mock 响应。
- B 层（b01–b05）返回严格、贴近真实样本的 Mock（示例来自 `../contracts/samples.json` 正向样本）。
- A 层 / 面试域 / device 端点返回 outlined 结构的 Mock（字段类型 best-effort，足以驱动前端联调）。
- 错误响应统一返回 `error-envelope` 结构。

### 4. 客户端代码生成
```bash
npx openapi-generator-cli generate -i openapi.json -g typescript-axios -o ./sdk
```

## 与源契约的关系

`../contracts/` 是**权威机器可读契约**（JSON Schema + 注册表，经 CI/pre-commit 双闸门校验）。
本 `openapi.json` 是其**导出视图**：A 层与面试域为 outlined 投影，B 层为严格投影。
若源契约更新，重跑 `gen_openapi.py` 即可同步；不要手工改 `openapi.json`（会被覆盖）。

## 已知边界（诚实登记，非未定义）

- A 层多数端点 `contractStatus=outlined`：请求/响应为字段大纲投影，非逐字段机器可读 schema；严格契约随对应 LLD 细化推进（见 HLD §9.4「待 LLD 细化」项）。
- `interviewEvaluation` 等引用类型已解析为严格组件；A 层 `jobStub`/`job`/`hrStatus` 等 outlined 引用以轻量 stub 组件兜底（保证 `$ref` 可解析），待对应 LLD 细化后可替换为严格 schema。
- WSS RPC 方法未建模为 HTTP path（OpenAPI 不原生支持 WS RPC），以 `info.x-agent-rpc` 扩展承载，供文档查阅与后续专用工具消费。
