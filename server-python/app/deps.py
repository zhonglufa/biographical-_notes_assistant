"""deps.py — FastAPI 依赖注入入口（便于测试 override）"""
from __future__ import annotations

from app.gateways.orchestrator import AIOrchestrator
from app.routers.service import AgentTriggerService


def get_orchestrator() -> AIOrchestrator:
    from app.main import app
    return app.state.orchestrator


def get_agent_service() -> AgentTriggerService:
    from app.main import app
    return app.state.agent_service
