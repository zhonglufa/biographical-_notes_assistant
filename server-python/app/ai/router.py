"""ai/router.py — B01–B05 内部 REST 端点（/internal/v1/ai）

全部挂载 require_internal_token 依赖（HLD §4.5：仅内网 + X-Internal-Token）。
请求由 pydantic 模型解析（extra=forbid 镜像 additionalProperties:false）；
响应由 orchestrator 内部过机器 schema 校验（fail-closed），此处直接返回 dict。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.ai.models import (
    AtsRequest,
    EvaluateRequest,
    MatchRequest,
    OptimizeRequest,
    QuestionsRequest,
)
from app.deps import get_orchestrator
from app.security import require_internal_token

router = APIRouter(prefix="/internal/v1/ai", tags=["ai"],
                   dependencies=[Depends(require_internal_token)])


@router.post("/match")
def b01_match(req: MatchRequest, orch=Depends(get_orchestrator)):
    weights = req.weights.model_dump() if req.weights is not None else None
    return orch.match(req.jd, req.resume, weights)


@router.post("/questions")
def b02_questions(req: QuestionsRequest, orch=Depends(get_orchestrator)):
    return orch.questions(req.jd, req.resume, req.count, req.lang)


@router.post("/evaluate")
def b03_evaluate(req: EvaluateRequest, orch=Depends(get_orchestrator)):
    return orch.evaluate(req.questionId, req.answer, req.rubricDims)


@router.post("/resume/optimize")
def b04_optimize(req: OptimizeRequest, orch=Depends(get_orchestrator)):
    return orch.optimize(req.resume, req.target)


@router.post("/ats")
def b05_ats(req: AtsRequest, orch=Depends(get_orchestrator)):
    return orch.ats(req.resume)
