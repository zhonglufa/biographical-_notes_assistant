"""
api_stub.py — 向后兼容薄层（A 层接口已迁移到 stubs/ 包）

实际端点定义见 stubs/（按模块分文件 + 自动发现注册表）。
本文件仅 re-export 全局 API_STUB / Endpoint / ApiStub，并提供一个
「遍历注册表、逐个发示例请求」的 __main__ 演示（不再逐端点硬编码）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stubs import API_STUB, Endpoint, ApiStub, validate_payload

__all__ = ["API_STUB", "Endpoint", "ApiStub", "validate_payload"]


if __name__ == "__main__":
    print("=== 接口桩注册表自检（自动遍历所有端点）===")
    for ep in API_STUB.endpoints():
        code, body = API_STUB.dispatch_id(ep.name, ep.example_request)
        keys = list(body.keys()) if isinstance(body, dict) else type(body).__name__
        print(f"  {ep.name}: HTTP {code}  resp={keys}")
    print(f"共注册 {len(API_STUB.endpoint_ids())} 个端点")
