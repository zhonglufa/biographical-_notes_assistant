# 编码期脚手架（D 阶段奠基切片）

本目录是「设计层已够细 → 编码期」的**奠基切片**，目标是证明 **contract-first**
落地可行性，而非全量多模块实现。全量代码按 README §3 顺序分阶段推进。

## 1. 设计原则

- **契约是设计文档，不是代码注释**：`design/contracts/*.schema.json`（schema 66 / 注册表 6）
  是「唯一真相源」，代码只是契约的执行者。
- **fail-closed**：请求/响应/事件发布前必过 `validate()`，不合规即拒绝，绝不悄悄放行。
- **换传输不改规则**：HTTP 框架（FastAPI/Flask）、消息队列（RabbitMQ）、本机 Agent
  进程间通信，都复用同一套 `contract_runtime.validate_payload()`，校验逻辑零分歧。
- **零外部依赖**：校验器为纯标准库实现（`design/contracts/validate_contracts.py`），
  本脚手架同样仅用标准库，CI 直接跑，无装包成本。

## 2. 当前切片已落地

| 文件 | 作用 |
|------|------|
| `src/contract_runtime.py` | 运行时加载 + 校验契约（复用 `design/contracts/validate_contracts.py`） |
| `src/event_bus.py` | 内存事件总线 stub，发布前对 `domain-events.event.schema.json` 校验；演示支付状态事件驱动会员权益（C5） |
| `src/stubs/core.py` | 端点抽象 `Endpoint/ApiStub` + 契约校验（含 None schema 容错）；**稳定基础设施，子代理禁改** |
| `src/stubs/<module>.py` | 各 A 层模块桩（auth/jobs/user/resume…），定义 `ENDPOINTS` 列表 |
| `src/stubs/__init__.py` | 扫描本包所有模块、汇总进全局 `API_STUB`（**新增模块零共享文件改动**） |
| `src/api_stub.py` | 向后兼容薄层，re-export `API_STUB` 并保留 `__main__` 注册表自检演示 |
| `tests/test_smoke.py` | 冒烟测试：契约校验、事件 fail-closed、接口 422 fail-closed（**注册表驱动，自动遍历所有端点**） |

## 3. 运行

```bash
cd scaffold
python tests/test_smoke.py
# 也可单独跑演示：
python -m src.contract_runtime
python -m src.event_bus
python -m src.api_stub
```

需 Python 3.10+。脚本自动回溯到仓库根，加载 `design/contracts/`。

## 4. 后续模块脚手架顺序（建议，待逐期推进）

按 HLD §9.4 闭环顺序与风险优先级：

1. **本机 Agent 与投递执行**（首选模块，R-03/R-04 已闭合）：落地进程监督 + 幂等收敛 + 投递状态机。
2. **支付模块**（R-04 已闭合）：状态机 + 回调验签 + 对账 + 退款 + 续费，所有出参过 `member_order` 相关 schema。
3. **平台适配器**（R-09 已缓解）：SelectorBundle + 速率整形 + 单平台降级，事件发 `delivery-state` / `adapter` 类。
4. **AI 编排 / 解析质量 / 面试域**：B01–B05、解析、rubric 对齐各自 LLD schema。
5. **横切**：密钥工程（本地信封）、可观测性（OpenTelemetry）、通知推送（去重窗口）、用户权限（T-UP-1 码表）。

每个端点落地时，先写对应 `*.schema.json`（若设计期未覆盖），再在 `stubs/` 下新建一个
`<module>.py` 定义该端点的 `Endpoint`（含 `example_request`）。注册表自动发现、
`test_smoke.py` 自动遍历所有端点断言，**无需改任何共享文件** —— 天然支持并行子代理
各写各模块、零冲突，让双闸门（设计期 + 运行期）形成闭环。

## 5. 与双闸门的关系

- **设计期闸门**：`design/contracts/validate_contracts.py` + `design/check_prd_hld_traceability.py`
  （pre-commit + CI 强制）。
- **运行期闸门**：本脚手架 `contract_runtime.validate_payload()`，保证线上实现永不偏离设计契约。

两者共享同一份 schema，因此「设计改了，代码校验自动跟着变」——这就是 contract-first 的核心价值。
