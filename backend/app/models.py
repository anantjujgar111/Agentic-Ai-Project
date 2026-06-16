from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatRequest:
    message: str
    user_id: str = "cust_001"


@dataclass
class ToolTrace:
    name: str
    input: dict[str, Any]
    output: dict[str, Any]


@dataclass
class AgentResponse:
    response: str
    agent: str
    user_id: str
    traces: list[ToolTrace] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "agent": self.agent,
            "user_id": self.user_id,
            "traces": [
                {"name": trace.name, "input": trace.input, "output": trace.output}
                for trace in self.traces
            ],
            "next_steps": self.next_steps,
        }
