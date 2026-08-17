"""
stubs/core.py — 端点抽象与注册表核心（A 层接口并行落地底座）

- Endpoint：契约优先端点，请求/响应均先校验再执行 handler；
  request_schema / response_schema 为 None 时跳过对应侧校验（覆盖尚无
  schema 文件的端点，如 ref 指向 HLD 章节的 A09/A11/A14，避免伪造契约）。
- ApiStub：端点注册表 + 按 id 分发。
- validate_payload：复用 contract_runtime（设计/契约 是真相源）。

⚠️ 本文件是「稳定基础设施」：并行子代理**禁止修改**本文件；
各模块只需在 stubs/<module>.py 定义 ENDPOINTS 列表即可被自动发现。
"""
import os
import sys

# 确保能 import 到同目录(src)下的 contract_runtime
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # .../src/stubs
sys.path.insert(0, os.path.dirname(_SRC_DIR))            # .../src

from contract_runtime import validate_payload  # 复用零依赖契约校验器


class Endpoint:
    """一个契约优先的端点。

    example_request: 该端点的一个合法示例请求，供冒烟测试自动遍历所有端点
    （新增模块无需改测试）。无请求体端点填 {} 或不传。
    """

    def __init__(self, name: str, request_schema, response_schema, handler,
                 example_request=None):
        self.name = name
        self.request_schema = request_schema
        self.response_schema = response_schema
        self._handler = handler
        self.example_request = example_request or {}

    def dispatch(self, request: dict) -> tuple:
        """分发一次调用，返回 (HTTP 状态码, body)。

        - 请求不合规 -> 422（fail-closed，绝不执行业务）
        - 响应不合规 -> 500（实现偏离契约，暴露而非吞掉）
        - 正常        -> 200 + handler 结果
        - request_schema 为 None -> 跳过入参校验（无请求体 / 暂无 schema）
        - response_schema 为 None -> 跳过响应校验（暂无响应 schema）
        """
        if self.request_schema is not None:
            ok, err = validate_payload(self.request_schema, request)
            if not ok:
                return 422, {"error": "request_schema_violation", "detail": err}

        resp = self._handler(request)

        if self.response_schema is not None:
            ok2, err2 = validate_payload(self.response_schema, resp)
            if not ok2:
                return 500, {"error": "response_schema_violation", "detail": err2}
        return 200, resp


class ApiStub:
    """端点注册表 + 按 id 分发。生产环境可挂 HTTP 层，此处仅演示契约校验。"""

    def __init__(self):
        self._endpoints = {}

    def register(self, endpoint: Endpoint) -> Endpoint:
        self._endpoints[endpoint.name] = endpoint
        return endpoint

    def dispatch_id(self, endpoint_id: str, request: dict) -> tuple:
        ep = self._endpoints.get(endpoint_id)
        if ep is None:
            return 404, {"error": "unknown_endpoint", "endpoint": endpoint_id}
        return ep.dispatch(request)

    def endpoint_ids(self) -> list:
        return list(self._endpoints.keys())

    def endpoints(self) -> list:
        return list(self._endpoints.values())
