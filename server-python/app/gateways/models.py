"""ai/models.py — B01–B05 请求模型（pydantic v2）

约束与 design/contracts/b0x-*.request.schema.json 对齐：
- 字段类型 / 范围 / 必填与机器 schema 一致；
- model_config extra="forbid" 镜像 additionalProperties:false（多余字段即拒）；
- 响应一律返回 dict 并由端点过机器 schema 校验（契约是真相源，不依赖 pydantic 反推响应）。
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Forbid(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatchWeights(_Forbid):
    skill: float | None = Field(default=None, ge=0, le=1)
    jobtitle: float | None = Field(default=None, ge=0, le=1)
    exp: float | None = Field(default=None, ge=0, le=1)


class MatchRequest(_Forbid):
    jd: str = Field(min_length=1)
    resume: str = Field(min_length=1)
    weights: MatchWeights | None = None


class QuestionsRequest(_Forbid):
    jd: str = Field(min_length=1)
    resume: str = Field(min_length=1)
    count: int = Field(ge=1, le=20)
    lang: Literal["zh", "en"]


class EvaluateRequest(_Forbid):
    questionId: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    rubricDims: list[str] | None = None


class OptimizeRequest(_Forbid):
    resume: str = Field(min_length=1)
    target: str = Field(min_length=1)


class AtsRequest(_Forbid):
    resume: str = Field(min_length=1)
