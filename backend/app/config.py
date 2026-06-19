from __future__ import annotations

import os
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DATA_ROOT = BACKEND_ROOT / "data" if (BACKEND_ROOT / "data").exists() else REPO_ROOT / "data"
KNOWLEDGE_ROOT = DATA_ROOT / "knowledge_base"
MOCK_DATA_ROOT = DATA_ROOT / "mock"


class Settings:
    """Runtime settings read from environment variables."""

    app_name: str = os.getenv("APP_NAME", "HDFC Smart Banking Assistant POC")
    default_customer_id: str = os.getenv("DEFAULT_CUSTOMER_ID", "cust_001")

    gcp_project_id: str | None = os.getenv("GCP_PROJECT_ID")
    gcp_location: str = os.getenv("GCP_LOCATION", "us-central1")
    vertex_model: str = os.getenv("VERTEX_MODEL", "gemini-1.5-flash")
    use_vertex: bool = os.getenv("USE_VERTEX", "false").lower() == "true"

    knowledge_backend: str = os.getenv("KNOWLEDGE_BACKEND", "local")
    vertex_search_data_store_id: str | None = os.getenv("VERTEX_SEARCH_DATA_STORE_ID")
    session_backend: str = os.getenv("SESSION_BACKEND", "memory")
    session_firestore_collection: str = os.getenv(
        "SESSION_FIRESTORE_COLLECTION", "chat_sessions"
    )

    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
