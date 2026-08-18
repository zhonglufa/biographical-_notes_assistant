"""agent/service.py — 服务端侧 Agent 任务编排（B10/B11 受理 + B07 状态 + B09 健康）

职责边界（ADR-003）：服务端只「受理触发命令 + 记录任务状态 + 接收健康上报」，
真实采集由本机 Agent 进程执行（经 transport 接缝下发）。此处不连接真实 Agent，
不触发真实投递 —— 防越权/防生产事故。任务状态以 B07 形状对外查询。
"""
from __future__ import annotations

import time

from app.agent.models import GetJobDetailCommand, HealthReport, SearchJobsCommand, TaskStatusResponse
from app.agent.transport import AgentTransport
from app.errors import AppError


class AgentTriggerService:
    def __init__(self, transport: AgentTransport):
        self.transport = transport
        self._tasks: dict[str, dict] = {}
        self._health: dict[str, HealthReport] = {}

    def _persist_pending(self, task_id: str, action: str) -> None:
        now = int(time.time() * 1000)
        self._tasks[task_id] = {
            "taskId": task_id,
            "idempotencyKey": task_id,
            "status": "pending",
            "action": action,
            "updatedAt": now,
        }

    def _to_status(self, task_id: str) -> TaskStatusResponse:
        rec = self._tasks.get(task_id)
        if rec is None:
            raise AppError("RESOURCE_NOT_FOUND", f"unknown taskId: {task_id}", http=404, retryable=False)
        return TaskStatusResponse(
            taskId=rec["taskId"],
            idempotencyKey=rec["idempotencyKey"],
            status=rec["status"],
            outcome=rec.get("outcome"),
            platformApplyId=rec.get("platformApplyId"),
            failReason=rec.get("failReason"),
            evidence=rec.get("evidence"),
            updatedAt=rec["updatedAt"],
        )

    def search_jobs(self, cmd: SearchJobsCommand) -> TaskStatusResponse:
        self.transport.dispatch("searchJobs", cmd.model_dump())
        self._persist_pending(cmd.taskId, "searchJobs")
        return self._to_status(cmd.taskId)

    def get_job_detail(self, cmd: GetJobDetailCommand) -> TaskStatusResponse:
        self.transport.dispatch("getJobDetail", cmd.model_dump())
        self._persist_pending(cmd.taskId, "getJobDetail")
        return self._to_status(cmd.taskId)

    def record_health(self, report: HealthReport) -> dict:
        self._health[report.platformId] = report
        return {"platformId": report.platformId, "recorded": True, "healthy": report.healthy}

    def get_task_status(self, task_id: str) -> TaskStatusResponse:
        return self._to_status(task_id)

    def get_health(self, platform_id: str) -> HealthReport | None:
        return self._health.get(platform_id)
