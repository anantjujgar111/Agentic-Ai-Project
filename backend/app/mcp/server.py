from __future__ import annotations

from app.mcp.tools import tool_service
from app.services.knowledge import KnowledgeService


knowledge_service = KnowledgeService()


def build_mcp_server():
    """Create an MCP server if the optional MCP SDK is installed.

    Install requirements and run this module when you want to expose the same
    tools to MCP-capable clients. The main FastAPI chatbot uses the same tool
    service directly so the POC remains runnable in simple environments.
    """

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "MCP SDK is not installed. Run `pip install -r backend/requirements.txt`."
        ) from exc

    mcp = FastMCP("hdfc-banking-poc-tools")

    @mcp.tool()
    def search_knowledge_base(query: str) -> dict:
        return knowledge_service.search(query)

    @mcp.tool()
    def get_account_balance(user_id: str) -> dict:
        return tool_service.get_balance(user_id)

    @mcp.tool()
    def get_statement_summary(user_id: str) -> dict:
        return tool_service.get_statement_summary(user_id)

    @mcp.tool()
    def list_due_bills(user_id: str) -> dict:
        return tool_service.list_due_bills(user_id)

    @mcp.tool()
    def recommend_payment_rail(amount: float, urgency: str = "normal") -> dict:
        return tool_service.recommend_payment_rail(amount=amount, urgency=urgency)

    @mcp.tool()
    def create_goal_plan(
        user_id: str, goal_name: str, target_amount: float, months: int
    ) -> dict:
        return tool_service.create_goal_plan(
            user_id=user_id,
            goal_name=goal_name,
            target_amount=target_amount,
            months=months,
        )

    @mcp.tool()
    def book_rm_appointment(user_id: str, preferred_slot_id: str | None = None) -> dict:
        return tool_service.book_rm_appointment(
            user_id=user_id,
            preferred_slot_id=preferred_slot_id,
        )

    return mcp


if __name__ == "__main__":
    server = build_mcp_server()
    server.run()
