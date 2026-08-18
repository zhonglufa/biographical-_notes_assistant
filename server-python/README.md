# server-python — 服务端 Python LLM 网关（ADR-002 双语言异构）

> 定位：AI 编排服务（B01–B05）+ 服务端侧 Agent 任务编排（B10/B11 + B07/B09）。
> 依据：`design/LLD-AI编排服务-模块设计.md` v1.0、`design/contracts/b0x-*.schema.json`、ADR-002（FastAPI）。
> 状态：**契约完整落地 + 35 项测试本地全绿**；真实 LLM / MQ / Agent 传输为「文档化接缝」，未伪造生产就绪。

## 1. 架构总览

```
Java 业务服务 ──(B01–B05, 内网 REST, X-Internal-Token)──> server-python (FastAPI)
   ▲                                                          │
   └──────(MQ: ai.task.result 事件, B02/B04/B05 异步回写)──────┘
                                    │
                                    ▼
               AIOrchestrator 门面：主 LLM → 备用 LLM → 规则兜底 → LLM_DEGRADED
               （fail-closed：响应过机器 schema 校验，偏离即 500 暴露）
```

- `app/main.py`：FastAPI 应用，装配编排器 + Agent 服务，统一异常→错误信封，traceId 贯穿，开放 `/healthz`。
- `app/ai/orchestrator.py`：五个方法 b01–b05，三级降级链 + 内容安全门 + `ai.task.result` 事件发布。
- `app/ai/rule_engine.py`：降级兜底（规则匹配 / 题库 / advise / 模板 / 启发式 ATS），确定性、可单测。
- `app/agent/*`：B10/B11 触发受理 + B07 任务状态 + B09 健康上报（经 transport 接缝下发本机 Agent）。
- `app/contracts.py`：复用 `design/contracts/validate_contracts.py`（零依赖）做 fail-closed 响应校验。

## 2. 目录结构

```
server-python/
  app/
    config.py          # 配置：INTERNAL_TOKEN / LLM_API_KEY(可选) / SLA 从契约注册表加载
    contracts.py       # 复用设计层零依赖校验器
    errors.py          # error-envelope（error-codes.json 注册表一致）
    security.py        # X-Internal-Token 依赖（未配置令牌→拒绝全部，fail-closed）
    main.py            # FastAPI 装配 + 异常处理器 + traceId 中间件
    deps.py            # 依赖注入入口（便于测试 override）
    ai/{models,llm_client,content_safety,rule_engine,orchestrator,router}.py
    agent/{models,transport,service,router}.py
  tests/               # 35 项 pytest（auth / 契约 fail-closed / 各 B 端点 / agent / health）
  requirements.txt  pytest.ini  .gitignore
```

## 3. 运行与测试

```bash
# 依赖（已装入 managed venv；本地包管理，不消耗 WorkBuddy 积分）
python -m pip install -r requirements.txt
# 本地起服务
uvicorn app.main:app --host 0.0.0.0 --port 8080
# 测试（FastAPI TestClient，全部本地可跑）
python -m pytest -q
```

## 4. 鉴权（HLD §4.5 / §939）

所有 `/internal/v1/*` 必须带 `X-Internal-Token` 且等于服务端配置令牌。
**config 默认令牌为空 → fail-closed**：生产/非 dev 必须显式设置环境变量 `INTERNAL_TOKEN`，否则 `security.require_internal_token` 一律 401 拒绝全部内部调用（防误配置裸奔，无 dev 兜底令牌）。`/healthz` 开放（k8s 存活探针）。
> 测试期由 `tests/conftest.py` 注入已知测试令牌（`test-internal-token`），不依赖默认非空值。

## 5. 降级优先（防生产事故）

`LLM_API_KEY` 缺省 → LLM 网关不可用 → 每个方法自动走规则兜底（model/status 标识来源），
服务不崩溃、AI 功能降级而非全断。**测试默认即覆盖降级链**；主 LLM 链路经注入 FakeLLM 单独验证。

## 6. 已登记接缝 / 待决项（显式，非静默）

| 项 | 现状 | 说明 |
|----|------|------|
| 真实 LLM 调用 | 接缝 | `llm_client.complete` 真实 DeepSeek 调用已写好，仅在 `LLM_API_KEY` 配置后触发；本环境无 key → 不触网、不消耗额度。 |
| 内容安全层 | 接缝 | `content_safety.check` 默认放行；真实审核模型为文档化扩展点（golden set 歧视命中=0 待接入后覆盖）。 |
| ai.task.result MQ 回写 | 接缝 | `LocalResultRecorder` 校验事件契约后落内存；RabbitMQ 发布器为文档化扩展（未启用 broker）。 |
| B10/B11 真实 Agent 传输 | 接缝 | `LocalAgentTransport` 记录命令并返回受理回执；真实 RPC/gRPC 下发本机 Agent 为扩展点（不在此环境连接真实 Agent，防越权触发投递）。 |
| 异步 taskId-first | 设计张力 | LLD §1 称 b02/b04/b05 异步返回 taskId 后经 MQ 回写，但机器可读 response schema（b02/b04/b05）规定返回最终结果。本实现以「契约是真相源」为准：HTTP 同步返回最终结果（合规），并额外发 `ai.task.result` 事件。完整 taskId-first 异步化是后续迭代接缝。 |
| error-codes 新增 | 设计变更 | 为响应信封新增 `INTERNAL_ERROR`(500) / `CONTRACT_BREACH`(500) 到 `design/contracts/error-codes.json`（已通过静态契约校验）。 |

## 7. 与双闸门 / 契约一致性

- 复用 `design/contracts/validate_contracts.py`（与 scaffold / CI 同一校验器），所有 B 成功响应与错误信封过机器 schema。
- 请求模型（pydantic `extra="forbid"` + 字段范围约束）镜像机器 schema 的 `additionalProperties:false` 与 min/max。
- 本目录测试**不**改变 CI 既有双闸门（契约静态校验 + PRD-HLD 追溯 + scaffold 15+ 测试）；server-python 测试需在 CI 追加一步（见 §3），待 push 解锁后接入。
