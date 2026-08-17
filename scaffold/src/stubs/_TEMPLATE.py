"""
stubs/_TEMPLATE.py — 新增 A 层模块的模板（并行子代理照抄此文件）

照做四步：
1. 复制本文件，重命名为 stubs/<module>.py（如 applications.py、interview.py）。
2. 在 ENDPOINTS 列表里，为本模块的每一个 A 层端点写一个 Endpoint(...)。
3. 每个 Endpoint 的字段：
   - name           : 必须是注册表里的 "Axx ..." 形式（见 design/contracts/external-api.registry.json）
   - request_schema : design/contracts/ 下的请求 schema 文件名；若无（ref 指向 HLD 章节）→ None
   - response_schema: design/contracts/ 下的响应 schema 文件名；若无 → None
   - handler        : 只返回符合响应契约结构的占位 dict，**不实现真实业务逻辑**
   - example_request: 一个能跑通（返回 200）的合法请求示例；无请求体端点填 {}
4. 不要 import / 修改任何其他文件（core.py / __init__.py / api_stub.py /
   test_smoke.py / 其他模块）。注册表会自动发现本文件并汇总。

⚠️ 若端点的响应契约是 None（暂无 schema）：handler 返回 {} 即可；
   并在 design/contracts/implementation-index.md 标记该端点「schema pending」。
"""
from .core import Endpoint


def _example_handler(req: dict) -> dict:
    # TODO: 替换为符合本模块响应契约的占位数据（若 response_schema=None 可返回 {}）
    return {"ok": True}


ENDPOINTS = [
    # Endpoint(
    #     name="Axx module-endpoint",
    #     request_schema="xxx.request.schema.json",   # 无则 None
    #     response_schema="xxx.response.schema.json", # 无则 None
    #     handler=_example_handler,
    #     example_request={},
    # ),
]
