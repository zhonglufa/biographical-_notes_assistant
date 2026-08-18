"""agent/router.py — B10/B11 触发 + B07 任务状态 + B09 健康上报（/internal/v1/agent）

B10/B11：服务端受理「本机 Agent 采集触发命令」，经 transport 接缝下发（本环境仅记录）。
B07：按 taskId 查询任务状态（契约形状）。
B09：接收本机 Agent 健康上报。
全部挂载 require_internal_token（内部调用）。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.routers.models import GetJobDetailCommand, HealthReport, SearchJobsCommand
from app.contracts import validate_payload
from app.deps import get_agent_service
from app.errors import AppError
from app.security import require_internal_token

router = APIRouter(prefix="/internal/v1/agent", tags=["agent"],
                   dependencies=[Depends(require_internal_token)])


@router.post("/jobs/search")
def b10_search(cmd: SearchJobsCommand, svc=Depends(get_agent_service)):
    status = svc.search_jobs(cmd)
    body = status.model_dump()
    ok, err = validate_payload("b07-task-result.schema.json", body)
    if not ok:
        raise AppError("CONTRACT_BREACH", f"B07 status violates schema: {err}", http=500, retryable=False)
    return body


@router.post("/jobs/detail")
def b11_detail(cmd: GetJobDetailCommand, svc=Depends(get_agent_service)):
    status = svc.get_job_detail(cmd)
    body = status.model_dump()
    ok, err = validate_payload("b07-task-result.schema.json", body)
    if not ok:
        raise AppError("CONTRACT_BREACH", f"B07 status violates schema: {err}", http=500, retryable=False)
    return body


@router.get("/tasks/{task_id}")
def task_status(task_id: str = Path(...), svc=Depends(get_agent_service)):
    status = svc.get_task_status(task_id)
    body = status.model_dump()
    ok, err = validate_payload("b07-task-result.schema.json", body)
    if not ok:
        raise AppError("CONTRACT_BREACH", f"B07 status violates schema: {err}", http=500, retryable=False)
    return body


@router.post("/health")
def health_report(report: HealthReport, svc=Depends(get_agent_service)):
    return svc.record_health(report)


@router.get("/health/{platform_id}")
def health_get(platform_id: str = Path(...), svc=Depends(get_agent_service)):
    h = svc.get_health(platform_id)
    if h is None:
        raise AppError("RESOURCE_NOT_FOUND", f"no health report for {platform_id}", http=404, retryable=False)
    return h.model_dump()
