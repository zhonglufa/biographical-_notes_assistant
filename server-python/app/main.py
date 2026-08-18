"""main.py — server-python FastAPI 应用（ADR-002：服务端 Python LLM 网关）

装配：
- 生命周期内构建 AIOrchestrator（LLM 网关 key 门控 + 内容安全 + 结果发布器接缝）
  与 AgentTriggerService（transport 接缝）；
- 挂载 B01–B05（/internal/v1/ai）与 B10/B11+B07+B09（/internal/v1/agent）路由，
  全部经 X-Internal-Token 鉴权依赖；
- 统一异常处理器：AppError → 规范错误信封；pydantic 校验失败 → INVALID_PARAM(400)；
  其余 → INTERNAL_ERROR(500)；fail-closed 不吞实现偏离；
- traceId 贯穿：每个请求生成/透传 X-Trace-Id（LLD §8 可观测性）；
- /healthz 开放存活探针（k8s liveness），其余内部接口均需令牌。
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers.router import router as agent_router
from app.routers.service import AgentTriggerService
from app.routers.transport import LocalAgentTransport
from app.gateways.content_safety import ContentSafety
from app.gateways.llm_client import LLMClient
from app.gateways.orchestrator import AIOrchestrator, LocalResultRecorder
from app.gateways.router import router as ai_router
from app.config import settings
from app.errors import AppError, envelope_from_error, error_envelope
from app.guard import build_guardrails


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时从契约注册表加载 SLA（单一真相源）
    settings.load_sla_from_contract()

    # 装配 5 护栏（成本熔断 / 监控 / 灰度开关 / crypto-shred / 审计链）
    guard = build_guardrails(settings)

    llm = LLMClient(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        primary_model=settings.llm_primary_model,
        backup_model=settings.llm_backup_model,
        cost_guard=guard["cost_guard"],
        monitor=guard["monitor"],
        audit=guard["audit"],
        feature_flags=guard["feature_flags"],
        per_call_cents=settings.llm_per_call_cents,
    )
    safety = ContentSafety(enabled=True)
    publisher = LocalResultRecorder()
    orchestrator = AIOrchestrator(llm, safety, publisher, settings.sla)

    transport = LocalAgentTransport()
    agent_service = AgentTriggerService(transport, monitor=guard["monitor"], audit=guard["audit"])

    app.state.orchestrator = orchestrator
    app.state.agent_service = agent_service
    app.state.publisher = publisher
    app.state.transport = transport
    app.state.guard = guard
    app.state.monitor = guard["monitor"]
    yield


app = FastAPI(title="resume-ai-python", version=settings.contract_version, lifespan=lifespan)
app.include_router(ai_router)
app.include_router(agent_router)


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.middleware("http")
async def monitor_middleware(request: Request, call_next):
    """护栏 3：逐内部请求记录到监控（错误率 / 逐端点计数）。"""
    response = await call_next(request)
    monitor = getattr(request.app.state, "monitor", None)
    if monitor is not None and request.url.path.startswith("/internal"):
        monitor.record_request(request.url.path, response.status_code, 0)
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    exc.trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(status_code=exc.http, content=envelope_from_error(exc))


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", "")
    # 请求契约违规（pydantic extra=forbid / 类型 / 必填）→ INVALID_PARAM(400)
    return JSONResponse(
        status_code=400,
        content=error_envelope("INVALID_PARAM", "Request validation failed", trace_id, False),
    )


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "")
    return JSONResponse(
        status_code=500,
        content=error_envelope("INTERNAL_ERROR", "Internal server error", trace_id, True),
    )


@app.get("/healthz")
async def healthz(request: Request):
    # 开放存活探针（k8s liveness）；附加护栏监控快照便于告警（非机器契约字段）
    snap = None
    svc = getattr(request.app.state, "agent_service", None)
    if svc is not None:
        snap = svc.monitor_snapshot()
    return {"status": "ok", "service": settings.service_name,
            "contractVersion": settings.contract_version, "guard": snap}
