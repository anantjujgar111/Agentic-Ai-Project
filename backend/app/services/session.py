from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ChatSession:
    session_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    account_number_masked: str | None = None
    verified_at: str | None = None
    pending_message: str | None = None
    memory: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_verified(self) -> bool:
        return self.customer_id is not None


class SessionManager:
    """In-memory POC session store.

    Production should replace this with Redis, Firestore, or another durable
    session store with TTL, encryption, and audit controls.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}

    def get(self, session_id: str) -> ChatSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id)
        return self._sessions[session_id]

    def mark_verified(
        self,
        session_id: str,
        customer_id: str,
        customer_name: str,
        account_number_masked: str,
    ) -> ChatSession:
        session = self.get(session_id)
        session.customer_id = customer_id
        session.customer_name = customer_name
        session.account_number_masked = account_number_masked
        session.verified_at = datetime.now(UTC).isoformat(timespec="seconds")
        return session

    def remember(self, session_id: str, role: str, content: str) -> None:
        session = self.get(session_id)
        session.memory.append(
            {
                "role": role,
                "content": content,
                "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
        )
        session.memory = session.memory[-12:]


session_manager = SessionManager()
