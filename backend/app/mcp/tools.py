from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from app.data_loader import load_mock_data


class BankingToolService:
    """Controlled banking tools used by the agents and exposed to MCP later."""

    def __init__(self) -> None:
        self.data = load_mock_data()
        self.scheduled_payments: list[dict[str, Any]] = []
        self.appointments: list[dict[str, Any]] = []

    def get_customer(self, user_id: str) -> dict[str, Any]:
        return self._find_one("customers", "customer_id", user_id)

    def get_balance(self, user_id: str) -> dict[str, Any]:
        account = self._find_one("accounts", "customer_id", user_id)
        return {
            "customer_id": user_id,
            "account_number_masked": account["account_number_masked"],
            "account_type": account["account_type"],
            "available_balance": account["available_balance"],
            "currency": account["currency"],
            "as_of": datetime.now(UTC).isoformat(timespec="seconds"),
        }

    def get_statement_summary(self, user_id: str) -> dict[str, Any]:
        transactions = self._filter("transactions", "customer_id", user_id)
        credits = sum(txn["amount"] for txn in transactions if txn["type"] == "credit")
        debits = sum(txn["amount"] for txn in transactions if txn["type"] == "debit")
        by_category: dict[str, float] = defaultdict(float)
        for txn in transactions:
            if txn["type"] == "debit":
                by_category[txn["category"]] += txn["amount"]

        top_categories = sorted(
            by_category.items(), key=lambda item: item[1], reverse=True
        )[:3]
        return {
            "period": "last_30_days",
            "credits": round(credits, 2),
            "debits": round(debits, 2),
            "net": round(credits - debits, 2),
            "top_spend_categories": [
                {"category": category, "amount": round(amount, 2)}
                for category, amount in top_categories
            ],
            "transaction_count": len(transactions),
        }

    def explain_transaction(self, user_id: str, query: str) -> dict[str, Any]:
        transactions = self._filter("transactions", "customer_id", user_id)
        query_lower = query.lower()
        candidates = [
            txn
            for txn in transactions
            if txn["merchant"].lower() in query_lower
            or txn["category"].lower() in query_lower
            or txn["transaction_id"].lower() in query_lower
        ]
        transaction = candidates[0] if candidates else transactions[-1]
        explanation = (
            f"{transaction['merchant']} was a {transaction['type']} transaction "
            f"of Rs. {transaction['amount']:,.2f} on {transaction['date']} under "
            f"{transaction['category']}. Narration: {transaction['narration']}."
        )
        return {"transaction": transaction, "explanation": explanation}

    def list_due_bills(self, user_id: str) -> dict[str, Any]:
        bills = [
            bill
            for bill in self._filter("bills", "customer_id", user_id)
            if bill["status"] == "due"
        ]
        return {"bills": bills}

    def recommend_payment_rail(self, amount: float, urgency: str = "normal") -> dict[str, Any]:
        if amount <= 100000 and urgency in {"instant", "normal"}:
            rail = "UPI"
            reason = "instant settlement and no beneficiary cooling period for small bill payments"
        elif amount <= 500000:
            rail = "IMPS"
            reason = "near real-time transfer for medium-value payments"
        elif urgency == "same_day":
            rail = "RTGS"
            reason = "same-day high-value settlement"
        else:
            rail = "NEFT"
            reason = "cost-effective scheduled transfer for non-urgent payments"

        return {"recommended_rail": rail, "reason": reason}

    def schedule_payment(
        self,
        user_id: str,
        biller: str,
        amount: float,
        payment_date: str,
        rail: str,
    ) -> dict[str, Any]:
        payment = {
            "payment_id": f"pay_{len(self.scheduled_payments) + 1:03d}",
            "customer_id": user_id,
            "biller": biller,
            "amount": amount,
            "payment_date": payment_date,
            "rail": rail,
            "status": "scheduled",
        }
        self.scheduled_payments.append(payment)
        return payment

    def create_recurring_payment(
        self, user_id: str, biller: str, amount: float, day_of_month: int
    ) -> dict[str, Any]:
        return {
            "mandate_id": "rec_001",
            "customer_id": user_id,
            "biller": biller,
            "amount": amount,
            "day_of_month": day_of_month,
            "status": "active_mock",
        }

    def split_rent(self, user_id: str, total_amount: float, participants: int) -> dict[str, Any]:
        share = round(total_amount / participants, 2)
        return {
            "customer_id": user_id,
            "total_amount": total_amount,
            "participants": participants,
            "share_per_person": share,
            "status": "split_request_preview",
        }

    def get_cards(self, user_id: str) -> dict[str, Any]:
        return {"cards": self._filter("cards", "customer_id", user_id)}

    def update_card_control(
        self, user_id: str, control: str, value: str | int | bool
    ) -> dict[str, Any]:
        card = self._filter("cards", "customer_id", user_id)[0]
        return {
            "card_id": card["card_id"],
            "control": control,
            "new_value": value,
            "status": "updated_in_mock",
        }

    def create_goal_plan(
        self, user_id: str, goal_name: str, target_amount: float, months: int
    ) -> dict[str, Any]:
        customer = self.get_customer(user_id)
        monthly_required = round(target_amount / months, 2)
        surplus = customer["monthly_income"] - customer["average_monthly_spend"]
        feasibility = "comfortable" if monthly_required <= surplus * 0.6 else "needs_adjustment"
        return {
            "goal_name": goal_name,
            "target_amount": target_amount,
            "months": months,
            "monthly_required": monthly_required,
            "estimated_monthly_surplus": surplus,
            "feasibility": feasibility,
            "recommended_actions": [
                f"Move Rs. {monthly_required:,.2f} on salary day into a separate goal bucket.",
                "Review dining, shopping, and subscription spends every month.",
                "Keep emergency savings separate from investment-oriented goals.",
            ],
            "disclaimer": "This is an illustrative plan for a POC and not financial advice.",
        }

    def list_rm_slots(self, user_id: str) -> dict[str, Any]:
        customer = self.get_customer(user_id)
        rm_id = customer["relationship_manager_id"]
        slots = [slot for slot in self.data["rm_slots"] if slot["rm_id"] == rm_id]
        return {"rm_id": rm_id, "slots": slots}

    def book_rm_appointment(self, user_id: str, preferred_slot_id: str | None = None) -> dict[str, Any]:
        slots = self.list_rm_slots(user_id)["slots"]
        available = [slot for slot in slots if slot["status"] == "available"]
        if not available:
            return {"status": "no_slots_available"}

        slot = (
            next((item for item in available if item["slot_id"] == preferred_slot_id), None)
            if preferred_slot_id
            else None
        ) or available[0]

        appointment = {
            "appointment_id": f"apt_{len(self.appointments) + 1:03d}",
            "customer_id": user_id,
            "rm_id": slot["rm_id"],
            "rm_name": slot["rm_name"],
            "slot_id": slot["slot_id"],
            "starts_at": slot["starts_at"],
            "mode": slot["mode"],
            "status": "confirmed_mock",
        }
        self.appointments.append(appointment)
        return appointment

    def _find_one(self, collection: str, field: str, value: str) -> dict[str, Any]:
        for item in self.data[collection]:
            if item[field] == value:
                return item
        raise ValueError(f"No {collection} item found for {field}={value}")

    def _filter(self, collection: str, field: str, value: str) -> list[dict[str, Any]]:
        return [item for item in self.data[collection] if item[field] == value]


tool_service = BankingToolService()
