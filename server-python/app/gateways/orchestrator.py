"""ai/orchestrator.py — 统一 AI 网关门面（AIOrchestrator，LLD §1）

五个方法 b01-b05，每个遵循「主 LLM → 备用 LLM → 规则兜底 → LLM_DEGRADED」三级降级链：
- 仅当 LLM_API_KEY 配置且调用成功才走主/备链路（model=deepseek/backup）；
- 任何失败/超时/内容安全命中 → 走规则兜底（model=rule / status=degraded）；
- 全部成功响应在返回前必过机器 schema 校验（fail-closed，偏离即 500 暴露）；
- 异步方法（b02/b04/b05）在返回契约最终结果的同时，额外发布 ai.task.result 事件
  （经 ResultPublisher 接缝；当前默认本地记录器，RabbitMQ 为文档化扩展）。

设计张力（已登记，非静默）：LLD §1 称 b02/b04/b05 异步返回 taskId 后经 MQ 回写，
但机器可读 response schema（b02/b04/b05）规定返回最终结果。本实现以「契约是真相源」
为准：HTTP 同步返回最终结果（契约合规），并额外发出事件供 Java 侧按 taskId 落库/对账。
完整 taskId-first 异步化是后续迭代的文档化接缝。
"""
from __future__ import annotations

import json
import time
import uuid

from app.gateways.content_safety import ContentSafety
from app.gateways.llm_client import LLMClient
from app.gateways.rule_engine import (
    advise,
    question_bank,
    rule_match,
    score_skip_ats,
    template_optimize,
)
from app.contracts import validate_event, validate_payload
from app.errors import AppError

# —— 系统提示（主/备 LLM 调用；要求严格 JSON 输出）——
_B01_SYS = "你是招聘匹配引擎。基于 JD 与简历输出 JSON：{score:0~1, matchedSkills:[], explanation:string}。"
_B02_SYS = "你是面试官。基于 JD 与简历生成面试题，输出 JSON：{questionSetId:string, questions:[{id,text,type(behavior|tech|case)}]}。"
_B03_SYS = "你是面试评估官。基于作答输出 JSON：{score:0~1, rubric:[{dim,score}], feedback:string}。"
_B04_SYS = "你是简历优化师。输出 JSON：{optimized:string, changes:[{field,from,to}]}。"
_B05_SYS = "你是 ATS 评分器。输出 JSON：{atsScore:0~100, suggestions:[{section,hint}]}。"


class ResultPublisher:
    """ai.task.result 事件发布接缝（LLD §7）。"""

    def publish(self, event: dict) -> None:  # pragma: no cover - 由子类实现
        raise NotImplementedError


class LocalResultRecorder(ResultPublisher):
    """默认实现：校验事件契约后落内存记录（生产可换 RabbitMqPublisher）。"""

    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish(self, event: dict) -> None:
        ok, err = validate_event("ai-result.event.schema.json", event)
        if not ok:
            # 实现偏离事件契约 → 暴露而非静默发出脏事件
            raise AppError("CONTRACT_BREACH", f"ai.task.result event violates schema: {err}",
                           trace_id=event.get("traceId", ""), http=500, retryable=False)
        self.events.append(event)


class AIOrchestrator:
    def __init__(self, llm: LLMClient, safety: ContentSafety, publisher: ResultPublisher, sla: dict):
        self.llm = llm
        self.safety = safety
        self.publisher = publisher
        self.sla = sla  # method_id -> MethodSla

    # ---- 内部工具 ----
    def _trace(self) -> str:
        return uuid.uuid4().hex

    def _validate_response(self, schema_name: str, resp: dict, trace_id: str) -> None:
        """fail-closed：响应偏离机器 schema → 抛 CONTRACT_BREACH（500 暴露）。"""
        ok, err = validate_payload(schema_name, resp)
        if not ok:
            raise AppError("CONTRACT_BREACH", f"response violates {schema_name}: {err}",
                           trace_id=trace_id, http=500, retryable=False)

    def _safe(self, *texts: str) -> bool:
        """内容安全：任一文本不通过 → False（调用方据此降级/拒答）。"""
        for t in texts:
            passed, _ = self.safety.check(t or "")
            if not passed:
                return False
        return True

    def _publish(self, trace_id: str, task_id: str, method: str, status: str,
                 result: dict, degrade_to: str | None = None) -> None:
        event = {
            "eventType": "ai.task.result",
            "traceId": trace_id,
            "taskId": task_id,
            "method": method,
            "status": status,
            "result": result,
            "degradeTo": degrade_to,
            "producedAt": int(time.time() * 1000),
        }
        self.publisher.publish(event)

    def _llm_json(self, system: str, user_obj: dict, method_id: str) -> dict | None:
        """调主/备 LLM 并解析 JSON；不可用/失败/解析错 → None（触发降级）。"""
        if not self.llm.available():
            return None
        timeout = (self.sla.get(method_id).timeout_ms if self.sla.get(method_id) else 5000)
        raw = self.llm.complete(system=system, user=json.dumps(user_obj, ensure_ascii=False),
                                timeout_ms=timeout)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except (json.JSONDecodeError, ValueError):
            return None

    # ---- b01 match（同步）----
    def match(self, jd: str, resume: str, weights: dict | None = None) -> dict:
        trace = self._trace()
        parsed = self._llm_json(_B01_SYS, {"jd": jd, "resume": resume, "weights": weights}, "b01")
        if parsed is not None and self._safe(parsed.get("explanation", "")):
            try:
                resp = {
                    "score": max(0.0, min(1.0, float(parsed["score"]))),
                    "matchedSkills": list(parsed.get("matchedSkills", [])),
                    "explanation": str(parsed.get("explanation", "")),
                    "model": "deepseek",
                    "elapsedMs": 0,
                }
                self._validate_response("b01-match.response.schema.json", resp, trace)
                return resp
            except (KeyError, TypeError, ValueError):
                pass
        # 降级：规则引擎
        resp = rule_match(jd, resume, weights)
        self._validate_response("b01-match.response.schema.json", resp, trace)
        return resp

    # ---- b02 questions（异步，返回最终结果 + 发事件）----
    def questions(self, jd: str, resume: str, count: int, lang: str) -> dict:
        trace = self._trace()
        task_id = uuid.uuid4().hex
        parsed = self._llm_json(_B02_SYS, {"jd": jd, "resume": resume, "count": count, "lang": lang}, "b02")
        if parsed is not None:
            try:
                qs = parsed["questions"]
                texts = " ".join(q.get("text", "") for q in qs if isinstance(q, dict))
                if self._safe(texts):
                    resp = {
                        "questionSetId": str(parsed.get("questionSetId", uuid.uuid4().hex)),
                        "questions": qs,
                    }
                    self._validate_response("b02-questions.response.schema.json", resp, trace)
                    self._publish(trace, task_id, "b02", "ok", resp)
                    return resp
            except (KeyError, TypeError):
                pass
        resp = question_bank(jd, resume, count, lang)
        self._validate_response("b02-questions.response.schema.json", resp, trace)
        self._publish(trace, task_id, "b02", "degraded", resp, degrade_to="question_bank")
        return resp

    # ---- b03 evaluate（同步）----
    def evaluate(self, question_id: str, answer: str, rubric_dims: list[str] | None = None) -> dict:
        trace = self._trace()
        parsed = self._llm_json(_B03_SYS, {"questionId": question_id, "answer": answer,
                                           "rubricDims": rubric_dims}, "b03")
        if parsed is not None and self._safe(parsed.get("feedback", "")):
            try:
                resp = {
                    "score": max(0.0, min(1.0, float(parsed["score"]))),
                    "rubric": list(parsed.get("rubric", [])),
                    "feedback": str(parsed.get("feedback", "")),
                }
                self._validate_response("b03-evaluate.response.schema.json", resp, trace)
                return resp
            except (KeyError, TypeError, ValueError):
                pass
        resp = advise(question_id, answer, rubric_dims)
        self._validate_response("b03-evaluate.response.schema.json", resp, trace)
        return resp

    # ---- b04 optimize（异步）----
    def optimize(self, resume: str, target: str) -> dict:
        trace = self._trace()
        task_id = uuid.uuid4().hex
        parsed = self._llm_json(_B04_SYS, {"resume": resume, "target": target}, "b04")
        if parsed is not None and self._safe(parsed.get("optimized", "")):
            try:
                resp = {
                    "optimized": str(parsed["optimized"]),
                    "changes": list(parsed.get("changes", [])),
                }
                self._validate_response("b04-optimize.response.schema.json", resp, trace)
                self._publish(trace, task_id, "b04", "ok", resp)
                return resp
            except (KeyError, TypeError):
                pass
        resp = template_optimize(resume, target)
        self._validate_response("b04-optimize.response.schema.json", resp, trace)
        self._publish(trace, task_id, "b04", "degraded", resp, degrade_to="template")
        return resp

    # ---- b05 ats（异步）----
    def ats(self, resume: str) -> dict:
        trace = self._trace()
        task_id = uuid.uuid4().hex
        parsed = self._llm_json(_B05_SYS, {"resume": resume}, "b05")
        if parsed is not None:
            try:
                resp = {
                    "atsScore": max(0.0, min(100.0, float(parsed["atsScore"]))),
                    "suggestions": list(parsed.get("suggestions", [])),
                }
                self._validate_response("b05-ats.response.schema.json", resp, trace)
                self._publish(trace, task_id, "b05", "ok", resp)
                return resp
            except (KeyError, TypeError, ValueError):
                pass
        resp = score_skip_ats(resume)
        self._validate_response("b05-ats.response.schema.json", resp, trace)
        self._publish(trace, task_id, "b05", "degraded", resp, degrade_to="score_skip")
        return resp
