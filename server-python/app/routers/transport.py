"""agent/transport.py — 服务端→本机 Agent 传输接缝（B10/B11 实际下发通道）

真实环境：服务端经 RPC/gRPC（或本地 socket）把采集命令推送给「本机 Agent 进程」
（ADR-003：浏览器自动化下沉本机，服务端不承载）。本实现为本地接缝：记录命令并返回
受理回执，真实传输是文档化扩展点（不在此环境连接真实 Agent，避免越权触发真实投递）。
"""
from __future__ import annotations

import time


class AgentTransport:
    def dispatch(self, action: str, command: dict) -> dict:  # pragma: no cover
        raise NotImplementedError


class LocalAgentTransport(AgentTransport):
    """默认实现：记录命令、返回受理回执（dispatched=False 表示尚未真正下发）。"""

    def __init__(self) -> None:
        self.commands: list[dict] = []

    def dispatch(self, action: str, command: dict) -> dict:
        record = {
            "action": action,
            **command,
            "acceptedAt": int(time.time() * 1000),
            "dispatched": False,
        }
        self.commands.append(record)
        return {
            "taskId": command.get("taskId"),
            "accepted": True,
            "dispatched": False,
        }
