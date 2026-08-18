"""conftest.py — pytest 配置与 fixtures

- 将 server-python 根加入 sys.path，使 `import app` 可用；
- client：默认应用（无 LLM key → 始终走三级降级链，验证「降级优先、防生产事故」）；
- primary：注入 FakeLLM 的编排器，验证主 LLM 链路（model=deepseek）与事件发布；
- auth 相关 fixture：验证 X-Internal-Token 鉴权（含未配置令牌 fail-closed）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # server-python/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from app.gateways.content_safety import ContentSafety
from app.gateways.orchestrator import AIOrchestrator, LocalResultRecorder
from app.config import settings

TOKEN = "test-internal-token"
AUTH = {"X-Internal-Token": TOKEN}

# config 默认令牌为空（生产 fail-closed）；测试期显式注入已知令牌，使 /internal 调用可达。
# no_token_config fixture 仍会临时置空以验证 fail-closed 路径（恢复值即本令牌）。
settings.internal_token = TOKEN


class FakeLLM:
    """测试用假 LLM：按系统提示返回合法 JSON（覆盖主链路，不触真实 API）。"""

    def available(self) -> bool:
        return True

    def complete(self, *, system: str, user: str, timeout_ms: int, model: str | None = None) -> str:
        if "匹配引擎" in system:
            return '{"score":0.88,"matchedSkills":["python","fastapi"],"explanation":"LLM 语义匹配"}'
        if "面试官" in system:
            return ('{"questionSetId":"qs-1","questions":['
                    '{"id":"q1","text":"讲一个技术难点","type":"tech"},'
                    '{"id":"q2","text":"讲一个协作分歧","type":"behavior"},'
                    '{"id":"q3","text":"给一个案例","type":"case"}]}')
        if "评估官" in system:
            return '{"score":0.9,"rubric":[{"dim":"完整性","score":0.9}],"feedback":"回答结构清晰"}'
        if "优化师" in system:
            return '{"optimized":"OPT","changes":[{"field":"summary","from":"a","to":"b"}]}'
        if "ATS" in system:
            return '{"atsScore":82.5,"suggestions":[{"section":"技能","hint":"补充项目量化"}]}'
        return None


def _build_orchestrator(llm) -> AIOrchestrator:
    settings.load_sla_from_contract()
    return AIOrchestrator(llm, ContentSafety(enabled=True), LocalResultRecorder(), settings.sla)


@pytest.fixture
def client():
    """默认应用：无 LLM key → 降级链兜底。"""
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def primary():
    """注入 FakeLLM 的主链路编排器，返回 (client, orchestrator)。"""
    from app.deps import get_orchestrator
    from app.main import app

    orch = _build_orchestrator(FakeLLM())
    app.dependency_overrides[get_orchestrator] = lambda: orch
    with TestClient(app) as c:
        yield c, orch
    app.dependency_overrides.clear()


@pytest.fixture
def no_token_config():
    """临时将 internal_token 置空，验证「未配置令牌 → 拒绝全部内部调用」fail-closed。"""
    from app.main import app
    saved = settings.internal_token
    settings.internal_token = ""
    yield
    settings.internal_token = saved
