"""llm_match.py — LLM 岗位匹配服务 + 成本护栏（guardrail 2 核心 · B2-3）

岗位匹配判断是产品核心 AI 能力（HLD §4.5 AI 编排）。本模块：
- LLMGateway(Protocol)：可注入真实 LLM 适配（生产用 OpenAI/通义等）；默认 MockLLM 不触网/不持凭据。
- CostGuard：LLM 成本「硬上限 + 熔断」—— 护栏 2 的可度量实现。
  ⚠️ DEFAULT_DAILY_CAP_CENTS 仅为 DEMO 默认值；**生产硬上限金额由部署方/用户按预算配置**
     （循环不代设真实金额、不花钱、不订阅）。
- MatchService.match()：预扣成本 → 调网关 → 解析 band/score → 成功记账；
  任何护栏触发（超帽 / 熔断）即抛 CostGuardOpen，阻断成本失控。

防生产事故：不读取真实 API Key（网关由部署方注入）；不发起真实网络调用（MockLLM）；
成本硬上限与熔断阈值均为可配置常量，最终生产值由用户/运维在部署时确定。
"""
from __future__ import annotations

import json
import time
from typing import Protocol, runtime_checkable


# DEMO 默认日硬上限（¥500/天 = 50000 分）。生产值由部署方/用户配置，循环不代设真实金额。
DEFAULT_DAILY_CAP_CENTS = 50_000


class CostGuardOpen(Exception):
    """LLM 成本护栏触发：日硬上限已超或熔断已开，拒绝本次调用。"""


@runtime_checkable
class LLMGateway(Protocol):
    """LLM 调用网关端口；生产注入真实适配，本机仅用 MockLLM 可测。"""

    def complete(self, prompt: str) -> str:
        """返回模型原始文本（期望 JSON：{"band": "high|medium|low", "score": 0..1}）。"""
        ...


class MockLLM:
    """可测 LLM：确定性返回，不触网/不持凭据。"""

    def complete(self, prompt: str) -> str:
        if "高级" in prompt:
            return json.dumps({"band": "high", "score": 0.91})
        if "实习" in prompt:
            return json.dumps({"band": "low", "score": 0.28})
        return json.dumps({"band": "medium", "score": 0.72})


class CostGuard:
    """LLM 成本护栏：日硬上限 + 失败熔断（护栏 2 落地）。

    触顶或连续失败达阈值即「开闸（OPEN）」，拒绝后续调用，防止成本失控 /
    故障放大；冷却窗口结束后进入「半开」，允许一次探测恢复。
    """

    def __init__(self, daily_cap_cents: int = DEFAULT_DAILY_CAP_CENTS, *,
                 failure_threshold: int = 5, cooldown_s: int = 60, now=None) -> None:
        self.daily_cap_cents = daily_cap_cents
        self.failure_threshold = failure_threshold
        self.cooldown_s = cooldown_s
        self._spent = 0
        self._failures = 0
        self._opened_at = None
        self._now = now or time.time

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if (self._now() - self._opened_at) >= self.cooldown_s:
            return False  # 冷却结束，半开：允许一次探测（charge 成功则闭合）
        return True

    def charge(self, cents: int) -> bool:
        """预扣成本；超日硬上限或熔断开启则拒绝（返回 False，并触发熔断）。"""
        if self.is_open:
            return False
        if self._spent + cents > self.daily_cap_cents:
            self._open()
            return False
        self._spent += cents
        return True

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._open()

    def record_success(self) -> None:
        self._failures = 0

    def _open(self) -> None:
        self._opened_at = self._now()

    def reset(self) -> None:
        self._spent = 0
        self._failures = 0
        self._opened_at = None

    def remaining_cents(self) -> int:
        return max(0, self.daily_cap_cents - self._spent)


class MatchService:
    """岗位匹配服务：守成本护栏，调用 LLM 网关判定匹配度。"""

    def __init__(self, gateway: LLMGateway, cost_guard: CostGuard, *,
                 cost_per_call_cents: int = 10, monitor=None) -> None:
        self.gateway = gateway
        self.guard = cost_guard
        self.cost_per_call_cents = cost_per_call_cents
        self.monitor = monitor

    def match(self, resume_text: str, job_text: str):
        """返回 (band, score, cost_cents)；护栏触发则抛 CostGuardOpen。"""
        if not self.guard.charge(self.cost_per_call_cents):
            raise CostGuardOpen("LLM 成本护栏触发：日硬上限或熔断已开，拒绝本次调用")
        try:
            raw = self.gateway.complete(self._prompt(resume_text, job_text))
            band, score = self._parse(raw)
            self.guard.record_success()
            if self.monitor is not None:
                self.monitor.record_llm_cost(self.cost_per_call_cents)
            return band, score, self.cost_per_call_cents
        except Exception:
            self.guard.record_failure()
            raise

    def _prompt(self, resume_text: str, job_text: str) -> str:
        return f"简历：{resume_text}\n岗位：{job_text}\n请判断匹配度(high/medium/low)与置信分(0-1)。"

    @staticmethod
    def _parse(raw: str):
        data = json.loads(raw)
        return data["band"], float(data["score"])
