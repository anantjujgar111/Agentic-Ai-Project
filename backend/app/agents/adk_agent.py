from __future__ import annotations


def build_adk_agent():
    """Build an ADK agent when Google ADK is installed.

    The deterministic orchestrator in orchestrator.py is used for local tests.
    This factory documents the ADK integration point for the same tool boundary.
    """

    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError(
            "Google ADK is not installed. Run `pip install -r backend/requirements.txt` "
            "after confirming your Python environment."
        ) from exc

    return Agent(
        name="hdfc_smart_banking_orchestrator",
        model="gemini-1.5-flash",
        instruction=(
            "Route banking chatbot requests to customer service, smart payments, "
            "account service, goals, or RM appointment tools. Never claim that mock "
            "payments move real money. Ask for confirmation before irreversible actions."
        ),
    )
