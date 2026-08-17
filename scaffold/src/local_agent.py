"""
local_agent.py — 本机 Agent 投递编排核心（B1 · 契约优先、可单测）

职责（对齐 HLD §2.2 流程一「批量投递闭环」+ LLD-本机Agent v1.3）：
  - 应用规划 plan()：把匹配岗位按匹配度/策略过滤成「候选投递清单」
  - 岗位过滤：仅 high/medium 匹配带进入候选；low 直接排除（避免低命中投递）
  - 人工确认闸门 require_confirmation() + execute()：半自动核心——
    候选清单须用户显式确认后才执行，未确认绝不静默全自动（对应 PIPL§24 缓解设计）
  - 适配器调用 execute()：经可 mock 的 AdapterPort 执行浏览器投递，服务端不持凭据
  - 限额/幂等/验证码：当日限额、幂等键去重、验证码暂停

防生产事故设计约束：
  - 浏览器驱动经 AdapterPort 接口隔离（默认 MockAdapter），纯逻辑可单测，不依赖真实浏览器/凭据
  - 不读取真实 Cookie / 不登录账号（属用户本机 + 物理动作，循环不碰；cookie_ref 仅作引用透传）
  - 事件发布严格对齐 domain-events 契约（apply.status.changed + applyStatusChanged payload）
  - ⚠️ 「半自动/用户确认」能否真规避 PIPL§24 仍未经律师验证；该假设因 D 阶段跳过转为「用户延后」，
    本模块正确实现了闸门逻辑，但不构成法律豁免（如实登记，不伪造）。
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Protocol, runtime_checkable


class MatchBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {"low": 0, "medium": 1, "high": 2}[self.value]


@dataclass
class JobCandidate:
    job_id: str
    title: str
    company: str
    match_band: MatchBand
    match_score: float
    platform: str = "BOSS"


@dataclass
class ApplyOutcome:
    job_id: str
    status: str   # applied | skipped_low_match | skipped_quota |
                 # skipped_duplicate | skipped_unconfirmed | pending_captcha | failed
    detail: str = ""


@runtime_checkable
class AdapterPort(Protocol):
    """浏览器投递适配器端口（本机 Agent 经此执行，服务端不实现）。"""

    def apply(self, job: JobCandidate, *, cookie_ref: str | None = None) -> dict:
        """执行一次浏览器投递，返回 {"status": ..., "detail": ...}。"""
        ...


class MockAdapter:
    """默认可测适配器：按 job_id 决定结果，不触真实浏览器/凭据。"""

    def __init__(self, captcha_jobs: Iterable[str] = (), fail_jobs: Iterable[str] = ()):
        self.captcha_jobs = set(captcha_jobs)
        self.fail_jobs = set(fail_jobs)
        self.applied: list[str] = []

    def apply(self, job: JobCandidate, *, cookie_ref: str | None = None) -> dict:
        if job.job_id in self.captcha_jobs:
            return {"status": "captcha_required", "detail": "需人工验证码，暂停"}
        if job.job_id in self.fail_jobs:
            return {"status": "failed", "detail": "模拟投递失败"}
        self.applied.append(job.job_id)
        return {"status": "applied", "detail": "模拟投递成功"}


# 岗位平台中文名 -> domain-events 契约 platformId 枚举
PLATFORM_MAP = {
    "BOSS": "boss", "BOSS直聘": "boss", "猎聘": "liepin", "liepin": "liepin",
    "智联": "zhaopin", "智联招聘": "zhaopin", "zhaopin": "zhaopin",
    "前程无忧": "51job", "51job": "51job",
    "拉勾": "lagou", "lagou": "lagou",
}


@dataclass
class DeliveryStrategy:
    daily_quota: int = 30                 # 免费版 30；专业版 80-100（HLD §2.2）
    min_band: MatchBand = MatchBand.MEDIUM   # 仅 >= medium 进入候选
    require_confirmation: bool = True    # 半自动：默认需用户确认


class DeliveryOrchestrator:
    """本机 Agent 投递编排核心。

    adapter: AdapterPort（默认 MockAdapter，可注入真实 Playwright 适配器）
    bus:     可选事件总线（实现 .publish(event)->(bool,str)），用于发 domain-events
    """

    def __init__(self, adapter: AdapterPort, *, bus=None, user_id: str = "anonymous", now=None):
        self.adapter = adapter
        self.bus = bus
        self.user_id = user_id
        self._applied_today: set[str] = set()
        self._now = now if now is not None else time.time

    # ---- 规划 / 过滤 ----
    def plan(self, jobs: Iterable[JobCandidate], strategy: DeliveryStrategy) -> list[JobCandidate]:
        """过滤出候选投递岗位（匹配度 rank >= min_band），按匹配度降序。"""
        out = [j for j in jobs if j.match_band.rank >= strategy.min_band.rank]
        out.sort(key=lambda j: (j.match_band.rank, j.match_score), reverse=True)
        return out

    def require_confirmation(self, candidates: Iterable[JobCandidate]) -> list[JobCandidate]:
        """半自动闸门：返回需用户显式确认的候选清单（展示用）。"""
        return list(candidates)

    # ---- 执行（仅 confirmed_ids 内）----
    def execute(self, candidates: Iterable[JobCandidate], confirmed_ids: set[str],
                strategy: DeliveryStrategy, *, cookie_ref: str | None = None) -> list[ApplyOutcome]:
        outcomes: list[ApplyOutcome] = []
        for j in candidates:
            # 幂等优先：已投过的岗位不再消耗限额、直接去重（避免「已投」被限额误判）
            if j.job_id in self._applied_today:
                outcomes.append(ApplyOutcome(j.job_id, "skipped_duplicate", "已投过（幂等去重）"))
                continue
            if len(self._applied_today) >= strategy.daily_quota:
                outcomes.append(ApplyOutcome(j.job_id, "skipped_quota", "已达当日限额"))
                continue
            if strategy.require_confirmation and j.job_id not in confirmed_ids:
                outcomes.append(ApplyOutcome(j.job_id, "skipped_unconfirmed", "未获用户确认（半自动闸门）"))
                continue

            res = self.adapter.apply(j, cookie_ref=cookie_ref)
            status = res.get("status")
            if status == "applied":
                self._applied_today.add(j.job_id)
                outcomes.append(ApplyOutcome(j.job_id, "applied", res.get("detail", "")))
                self._emit(j, "submitted", res.get("detail"))
            elif status == "captcha_required":
                outcomes.append(ApplyOutcome(j.job_id, "pending_captcha", res.get("detail", "")))
            else:
                outcomes.append(ApplyOutcome(j.job_id, "failed", res.get("detail", "")))
        return outcomes

    def _emit(self, job: JobCandidate, to_state: str, reason: str | None):
        if self.bus is None:
            return
        event = {
            "eventType": "apply.status.changed",
            "traceId": f"trace-{job.job_id}",
            "ts": int(self._now() * 1000),
            "producer": "local-agent",
            "payload": {
                "taskId": f"task-{job.job_id}",
                "userId": self.user_id,
                "platformId": PLATFORM_MAP.get(job.platform, "boss"),
                "jobId": job.job_id,
                "fromState": "created",
                "toState": to_state,
                "reason": reason,
            },
        }
        # 复用 domain-events 契约校验（EventBus 内部 fail-closed）；失败不抛、仅不发布
        self.bus.publish(event)


if __name__ == "__main__":
    jobs = [
        JobCandidate("J1", "Java后端", "A厂", MatchBand.HIGH, 0.92, "BOSS"),
        JobCandidate("J2", "Java开发", "B厂", MatchBand.MEDIUM, 0.71, "猎聘"),
        JobCandidate("J3", "前端", "C厂", MatchBand.LOW, 0.30, "智联"),
    ]
    orch = DeliveryOrchestrator(MockAdapter(captcha_jobs={"J2"}))
    strat = DeliveryStrategy(daily_quota=30, min_band=MatchBand.MEDIUM, require_confirmation=True)
    cands = orch.plan(jobs, strat)
    print(f"候选数（排除 low）: {len(cands)}")
    outs = orch.execute(cands, confirmed_ids={"J1", "J2"}, strategy=strat)
    for o in outs:
        print(f"  {o.job_id} -> {o.status} ({o.detail})")
