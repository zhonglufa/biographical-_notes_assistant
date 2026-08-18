"""agent/models.py — B10/B11 触发命令 + B09 健康上报 + B07 任务状态（pydantic v2）

字段约束对齐 design/contracts/：
- b10-search-jobs.schema.json / b11-get-job-detail.schema.json（服务端→本机 Agent 采集触发）
- b09-health.schema.json（本机 Agent→服务端 健康上报）
- b07-task-result.schema.json（任务结果查询响应形状）
extra="forbid" 镜像 additionalProperties:false。
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Forbid(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchJobsCommand(_Forbid):
    taskId: str = Field(min_length=1)
    platformId: str = Field(min_length=1)
    query: str = Field(min_length=1, max_length=200)
    filters: dict[str, Any] | None = None
    geo: str | None = None
    page: int | None = Field(default=None, ge=1)


class GetJobDetailCommand(_Forbid):
    taskId: str = Field(min_length=1)
    platformId: str = Field(min_length=1)
    externalJobId: str = Field(min_length=1)


class HealthMetrics(_Forbid):
    domParseSuccessRate: float = Field(ge=0, le=1)
    avgLatencyMs: int = Field(ge=0)
    cookieHealthy: bool
    selectorBundleVersion: str | None = None


class HealthReport(_Forbid):
    platformId: str = Field(min_length=1)
    healthy: bool
    reason: str | None = None
    metrics: HealthMetrics
    checkedAt: int


class TaskStatusResponse(_Forbid):
    taskId: str
    idempotencyKey: str
    status: str  # pending | running | done | failed
    outcome: str | None = None
    platformApplyId: str | None = None
    failReason: str | None = None
    evidence: dict[str, Any] | None = None
    updatedAt: int
