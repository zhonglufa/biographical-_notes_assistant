"""stubs/payments.py — Payments 模块（A20 下单 / A21 回调）demo 桩

⚠️ 安全边界：handler 仅返回符合响应契约的占位数据，不实现真实支付下单 / 验签业务逻辑。
A21 响应 schema 待补（ref HLD §4.10）→ response_schema=None（不伪造契约）。
⚠️ A21 回调涉及真实支付渠道签名校验（生产安全），此处仅占位、不实现验签。
"""
from .core import Endpoint


def _payments_order_handler(req: dict) -> dict:
    return {
        "orderNo": "ORD-demo-001",
        "payUrl": "https://pay.demo.example/checkout/ORD-demo-001",
        "amount": 29900,
        "expireAt": 1760000000000 + 1800 * 1000,
    }


def _payments_callback_handler(req: dict) -> dict:
    # A21：响应 schema 待补（HLD §4.10），桩侧返回占位确认（不实现真实验签）
    return {"received": True, "status": "accepted"}


ENDPOINTS = [
    Endpoint(
        name="A20 payments-order",
        request_schema="payments-order.request.schema.json",
        response_schema="payments-order.response.schema.json",
        handler=_payments_order_handler,
        example_request={"plan": "pro", "months": 1, "couponCode": None},
    ),
    Endpoint(
        name="A21 payments-callback",
        request_schema="payments-callback.request.schema.json",
        response_schema=None,  # ref HLD §4.10，严格响应 schema 待补（不伪造契约）
        handler=_payments_callback_handler,
        example_request={"channel": "wechat", "outTradeNo": "O-demo-001",
                         "transactionId": "TXN-demo-001", "tradeStatus": "SUCCESS",
                         "amount": 29900, "sign": "demo-sign", "timestamp": 1760000000},
    ),
]
