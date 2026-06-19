from __future__ import annotations

import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import BankingOrchestrator
from app.config import settings
from app.mcp.tools import tool_service
from app.services.session import session_manager


class ChatApiRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default="demo-session")


class ChatApiResponse(BaseModel):
    response: str
    agent: str
    user_id: str
    session_id: str
    session_verified: bool
    traces: list[dict]
    next_steps: list[str]


app = FastAPI(title=settings.app_name)
orchestrator = BankingOrchestrator()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/chat", response_model=ChatApiResponse)
def chat(request: ChatApiRequest) -> dict:
    session = session_manager.get(request.session_id)
    session_manager.remember(request.session_id, "user", request.message)

    account_number = _extract_account_number(request.message)
    if not session.is_verified and account_number:
        verification = tool_service.verify_account_number(account_number)
        if not verification["verified"]:
            return _session_response(
                response=(
                    "I could not verify that account number. Please check it and enter the "
                    "full account number again. For this demo, use one of the synthetic test accounts."
                ),
                agent="Session Verification",
                session_id=request.session_id,
                user_id="unverified",
                verified=False,
            )

        session = session_manager.mark_verified(
            session_id=request.session_id,
            customer_id=verification["customer_id"],
            customer_name=verification["customer_name"],
            account_number_masked=verification["account_number_masked"],
        )
        if session.pending_message:
            pending_message = session.pending_message
            session.pending_message = None
            result = orchestrator.handle(
                message=pending_message,
                user_id=session.customer_id,
                session_id=request.session_id,
            )
            payload = result.to_dict()
            payload["response"] = (
                f"Thanks {session.customer_name}, your session is verified for "
                f"{session.account_number_masked}.\n\n{payload['response']}"
            )
            payload["session_id"] = request.session_id
            payload["session_verified"] = True
            session_manager.remember(request.session_id, "assistant", payload["response"])
            return payload

        return _session_response(
            response=(
                f"Thanks {session.customer_name}, your session is verified for "
                f"{session.account_number_masked}. How can I help you?"
            ),
            agent="Session Verification",
            session_id=request.session_id,
            user_id=session.customer_id,
            verified=True,
        )

    if not session.is_verified and _requires_verified_session(request.message):
        session.pending_message = request.message
        return _session_response(
            response=(
                "For privacy, I need to verify your session before showing account-specific "
                "details or creating banking requests. Please enter your full account number. "
                "Demo accounts: 5010004321 or 5010007788."
            ),
            agent="Session Verification",
            session_id=request.session_id,
            user_id="unverified",
            verified=False,
        )

    user_id = session.customer_id or settings.default_customer_id
    result = orchestrator.handle(
        message=request.message,
        user_id=user_id,
        session_id=request.session_id,
    )
    payload = result.to_dict()
    payload["session_id"] = request.session_id
    payload["session_verified"] = session.is_verified
    if not session.is_verified:
        payload["user_id"] = "unverified"
    session_manager.remember(request.session_id, "assistant", payload["response"])
    return payload


def _session_response(
    response: str,
    agent: str,
    session_id: str,
    user_id: str,
    verified: bool,
) -> dict:
    session_manager.remember(session_id, "assistant", response)
    return {
        "response": response,
        "agent": agent,
        "user_id": user_id,
        "session_id": session_id,
        "session_verified": verified,
        "traces": [],
        "next_steps": [],
    }


def _extract_account_number(message: str) -> str | None:
    digits = "".join(ch for ch in message if ch.isdigit())
    return digits if 10 <= len(digits) <= 18 else None


def _requires_verified_session(message: str) -> bool:
    text = message.lower()
    public_info_phrases = [
        "annual fee",
        "minimum balance",
        "what is",
        "tell me about",
        "charges and fees",
        "payment method",
        "fd and rd",
    ]
    if any(phrase in text for phrase in public_info_phrases):
        return False

    sensitive_terms = [
        "my account",
        "my balance",
        "show balance",
        "appointment",
        "beneficiary",
        "bill",
        "book rm",
        "card",
        "charge",
        "create goal",
        "debit",
        "due",
        "email",
        "goal",
        "limit",
        "mobile",
        "pay",
        "payment",
        "phone",
        "profile",
        "rm",
        "save",
        "statement",
        "transaction",
    ]
    return any(term in text for term in sensitive_terms)
