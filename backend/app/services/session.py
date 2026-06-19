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
        self.save(session)
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
        self.save(session)

    def save(self, session: ChatSession) -> None:
        self._sessions[session.session_id] = session


class FirestoreSessionManager(SessionManager):
    """Firestore-backed POC session store for Cloud Run deployments."""

    def __init__(self, collection_name: str) -> None:
        super().__init__()
        self.collection_name = collection_name
        self._firestore_enabled = False
        self.collection = None

        try:
            from google.cloud import firestore

            client_kwargs: dict[str, str] = {}
            if settings.gcp_project_id:
                client_kwargs["project"] = settings.gcp_project_id

            client = firestore.Client(**client_kwargs)
            self.collection = client.collection(collection_name)
            self._firestore_enabled = True
            logger.info(
                "Firestore session backend enabled collection=%s project=%s",
                collection_name,
                settings.gcp_project_id or "default",
            )
        except Exception as exc:
            logger.warning(
                "Firestore session store unavailable; using in-memory sessions only: %s",
                exc,
            )

    def get(self, session_id: str) -> ChatSession:
        if not self._firestore_enabled or self.collection is None:
            return super().get(session_id)

        try:
            snapshot = self.collection.document(session_id).get()
            if not snapshot.exists:
                session = ChatSession(session_id=session_id)
                self.save(session)
                return session

            data = snapshot.to_dict() or {"session_id": session_id}
            data["session_id"] = data.get("session_id") or session_id
            session = ChatSession.from_dict(data)
            super().save(session)
            return session
        except Exception as exc:
            logger.warning(
                "Firestore session read failed for session_id=%s; using in-memory fallback: %s",
                session_id,
                exc,
            )
            return super().get(session_id)

    def save(self, session: ChatSession) -> None:
        super().save(session)
        if not self._firestore_enabled or self.collection is None:
            return

        try:
            self.collection.document(session.session_id).set(session.to_dict())
        except Exception as exc:
            logger.warning(
                "Firestore session write failed for session_id=%s; keeping in-memory copy: %s",
                session.session_id,
                exc,
            )


def build_session_manager() -> SessionManager:
    if settings.session_backend.lower() != "firestore":
        return SessionManager()

    return FirestoreSessionManager(settings.session_firestore_collection)


session_manager = build_session_manager()
