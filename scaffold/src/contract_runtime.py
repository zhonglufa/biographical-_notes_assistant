"""
contract_runtime.py — 契约优先运行期加载/校验（D 阶段奠基切片）

职责：让代码在运行时复用 design/contracts/ 的机器可读契约（schema 66 / 注册表 6），
      对任意请求/响应/事件 payload 做「契约校验」，确保实现不偏离设计基线。

设计哲学（contract-first）：
  设计文档里的 *.schema.json 是「唯一真相源」；代码只是契约的执行者。
  每次接口入参/出参、每次事件发布前，都先过一遍 validate()，失败即 fail-closed。

依赖：纯标准库 + 复用 design/contracts/validate_contracts.py 的 validate()（零外部依赖）。
"""
import json
import os
import sys

# 把 design/contracts 加入搜索路径，复用既有零依赖校验器（不重复造轮子）
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CONTRACTS_DIR = os.path.join(_REPO_ROOT, "design", "contracts")
sys.path.insert(0, _CONTRACTS_DIR)

import validate_contracts  # 复用其内部 validate() 函数


def load_schema(schema_name: str) -> dict:
    """按文件名加载一个 JSON Schema。

    schema_name: 例如 "auth-login.request.schema.json"
    返回：解析后的 dict（schema 对象）
    """
    path = os.path.join(_CONTRACTS_DIR, schema_name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_payload(schema_name: str, payload) -> tuple[bool, str]:
    """对 payload 用指定 schema 做校验。

    返回 (是否通过, 错误信息)。错误信息为空串表示通过。
    复用 validate_contracts.validate —— 失败时抛 SchemaError，这里包成布尔。
    """
    schema = load_schema(schema_name)
    try:
        validate_contracts.validate(payload, schema)
        return True, ""
    except validate_contracts.SchemaError as e:
        return False, str(e)


if __name__ == "__main__":
    # 自测：校验一个合法登录请求 + 一个非法（含未声明额外字段）登录请求
    ok, err = validate_payload("auth-login.request.schema.json",
                                {"channel": "email", "deviceId": "dev-001",
                                 "email": "user@x.com", "password": "secret123"})
    print("合法登录请求 ->", "通过" if ok else f"失败: {err}")

    bad, err2 = validate_payload("auth-login.request.schema.json",
                                  {"channel": "email", "deviceId": "dev-001",
                                   "foo": "bar"})  # 含 additionalProperties:false 禁止的额外字段
    print("非法登录请求 ->", "通过(异常!)" if bad else f"正确拒绝: {err2}")
