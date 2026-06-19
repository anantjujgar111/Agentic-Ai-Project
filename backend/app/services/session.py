from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    session_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    account_number_masked: str | None = None
    verified_at: str | None = None
    pending_message: str | None = None
    pending_context: dict[str, Any] = field(default_factory=dict)
    memory: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_verified(self) -> bool:
        return self.customer_id is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "account_number_masked": self.account_number_masked,
            "verified_at": self.verified_at,
            "pending_message": self.pending_message,
            "pending_context": self.pending_context,
            "memory": self.memory,
            "updated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatSession":
        return cls(
            session_id=data["session_id"],
            customer_id=data.get("customer_id"),
            customer_name=data.get("customer_name"),
            account_number_masked=data.get("account_number_masked"),
            verified_at=data.get("verified_at"),
            pending_message=data.get("pending_message"),
            pending_context=dict(data.get("pending_context") or {}),
            memory=list(data.get("memory") or []),
        )


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

    def save(self, session: ChatSession) -> None:
        self._sessions[session.session_id] = session


class FirestoreSessionManager(SessionManager):
    """Firestore-backed POC session store for Cloud Run deployments."""

    def __init__(self, collection_name: str) -> None:
        self.collection_name = collection_name
        try:
            from google.cloud import firestore

            self.client = firestore.Client()
            self.collection = self.client.collection(collection_name)
        except Exception as exc:
            raise RuntimeError("Firestore session store could not be initialized") from exc

    def get(self, session_id: str) -> ChatSession:
        snapshot = self.collection.document(session_id).get()
        if not snapshot.exists:
            session = ChatSession(session_id=session_id)
            self._save(session)
            return session
        data = snapshot.to_dict() or {"session_id": session_id}
        data["session_id"] = data.get("session_id") or session_id
        return ChatSession.from_dict(data)

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
        self._save(session)
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
        self._save(session)

    def save(self, session: ChatSession) -> None:
        self._save(session)

    def _save(self, session: ChatSession) -> None:
        self.collection.document(session.session_id).set(session.to_dict())


def build_session_manager() -> SessionManager:
    if settings.session_backend.lower() != "firestore":
        return SessionManager()

    try:
        logger.info(
            "Using Firestore session backend collection=%s",
            settings.session_firestore_collection,
        )
        return FirestoreSessionManager(settings.session_firestore_collection)
    except Exception as exc:
        logger.warning(
            "Falling back to in-memory sessions because Firestore is unavailable: %s",
            exc,
        )
        return SessionManager()


session_manager = build_session_manager()
