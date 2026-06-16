from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import BankingOrchestrator
from app.config import settings


class ChatApiRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = Field(default=settings.default_customer_id)


class ChatApiResponse(BaseModel):
    response: str
    agent: str
    user_id: str
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
    result = orchestrator.handle(message=request.message, user_id=request.user_id)
    return result.to_dict()
