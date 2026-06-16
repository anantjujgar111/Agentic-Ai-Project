from app.agents.orchestrator import BankingOrchestrator


def test_balance_query_routes_to_account_agent():
    result = BankingOrchestrator().handle("Show my balance", "cust_001")

    assert result.agent == "Account Service Agent"
    assert "Rs." in result.response
    assert result.traces[0].name == "get_account_balance"


def test_payment_query_uses_payment_tools():
    result = BankingOrchestrator().handle("Schedule my electricity bill", "cust_001")

    assert result.agent == "Smart Payments Agent"
    assert any(trace.name == "recommend_payment_rail" for trace in result.traces)
    assert any(trace.name == "schedule_payment" for trace in result.traces)


def test_goal_query_includes_disclaimer():
    result = BankingOrchestrator().handle(
        "Create wedding goal for 5 lakh in 18 months", "cust_001"
    )

    assert result.agent == "Goal Agent"
    assert "not financial advice" in result.response


def test_rm_query_books_appointment():
    result = BankingOrchestrator().handle("Book RM appointment", "cust_001")

    assert result.agent == "RM Appointment Agent"
    assert any(trace.name == "book_rm_appointment" for trace in result.traces)
