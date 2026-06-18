from __future__ import annotations

import re
from typing import Any

from app.mcp.tools import tool_service
from app.models import AgentResponse, ToolTrace
from app.services.knowledge import KnowledgeService
from app.services.vertex_client import VertexTextClient


class BankingOrchestrator:
    def __init__(self) -> None:
        self.knowledge = KnowledgeService()
        self.vertex = VertexTextClient()

    def handle(self, message: str, user_id: str) -> AgentResponse:
        intent = self._classify(message)

        if intent == "small_talk":
            return self._small_talk(message, user_id)
        if intent == "customer_service":
            return self._customer_service(message, user_id)
        if intent == "payments":
            return self._payments(message, user_id)
        if intent == "account_service":
            return self._account_service(message, user_id)
        if intent == "goal":
            return self._goal(message, user_id)
        if intent == "rm_appointment":
            return self._rm_appointment(message, user_id)

        return self._fallback(message, user_id)

    def _classify(self, message: str) -> str:
        text = message.lower()
        normalized = re.sub(r"[^a-z0-9\s]", "", text).strip()
        if normalized in {
            "hi",
            "hello",
            "hey",
            "hii",
            "good morning",
            "good afternoon",
            "good evening",
            "thanks",
            "thank you",
        } or any(
            phrase in normalized
            for phrase in [
                "who are you",
                "what can you do",
                "how can you help",
                "help me",
            ]
        ):
            return "small_talk"
        if any(term in text for term in ["rm", "relationship manager", "appointment", "meeting"]):
            return "rm_appointment"
        if any(term in text for term in ["goal", "save", "saving", "vacation", "wedding", "education", "retirement", "emergency fund", "down payment"]):
            return "goal"
        if any(term in text for term in ["pay", "bill", "split", "rent", "recurring", "due date", "upi", "imps", "neft", "rtgs"]):
            return "payments"
        if any(term in text for term in ["balance", "statement", "transaction", "charge", "card", "limit", "fd", "rd", "beneficiary"]):
            return "account_service"
        return "customer_service"

    def _customer_service(self, message: str, user_id: str) -> AgentResponse:
        search_result = self.knowledge.search(message)
        traces = [
            ToolTrace(
                name="search_knowledge_base",
                input={"query": message},
                output=search_result,
            )
        ]
        hits = search_result.get("hits", [])
        if hits:
            answer_lines = [
                "Here is what I found:",
                "",
                *[
                    f"- {hit['title']}: {hit['snippet']} (source: {hit['source']})"
                    for hit in hits[:2]
                ],
            ]
        else:
            answer_lines = [
                "I can help with account questions, payments, card controls, savings goals, and RM appointments.",
                "Please tell me what you want to do in simple language, for example: check balance, explain a charge, pay a bill, create a goal, or book an RM appointment.",
            ]
        draft = "\n".join(answer_lines)
        return AgentResponse(
            response=self.vertex.polish("Answer customer service questions politely and stay within banking scope.", draft),
            agent="Customer Service Information Agent",
            user_id=user_id,
            traces=traces,
        )

    def _payments(self, message: str, user_id: str) -> AgentResponse:
        traces: list[ToolTrace] = []
        bills = tool_service.list_due_bills(user_id)
        traces.append(ToolTrace("list_due_bills", {"user_id": user_id}, bills))

        due_bills = bills["bills"]
        selected_bill = self._select_bill(message, due_bills)

        if "split" in message.lower() or "rent" in message.lower():
            amount = self._extract_amount(message) or 45000
            participants = self._extract_participants(message) or 3
            split = tool_service.split_rent(user_id, amount, participants)
            traces.append(
                ToolTrace(
                    "split_rent",
                    {"user_id": user_id, "total_amount": amount, "participants": participants},
                    split,
                )
            )
            draft = (
                f"Rent split preview: total Rs. {amount:,.2f}, {participants} people, "
                f"Rs. {split['share_per_person']:,.2f} per person. This is a mock split request."
            )
            return AgentResponse(
                response=self.vertex.polish("Help user split rent safely.", draft),
                agent="Smart Payments Agent",
                user_id=user_id,
                traces=traces,
            )

        if not selected_bill:
            draft = "I do not see a matching due bill in the mock data. You can ask about electricity, credit card, or broadband bills."
            return AgentResponse(
                response=draft,
                agent="Smart Payments Agent",
                user_id=user_id,
                traces=traces,
            )

        rail = tool_service.recommend_payment_rail(selected_bill["amount"])
        traces.append(
            ToolTrace(
                "recommend_payment_rail",
                {"amount": selected_bill["amount"], "urgency": "normal"},
                rail,
            )
        )

        if any(term in message.lower() for term in ["schedule", "pay", "set"]):
            payment = tool_service.schedule_payment(
                user_id=user_id,
                biller=selected_bill["biller"],
                amount=selected_bill["amount"],
                payment_date=selected_bill["recommended_pay_date"],
                rail=rail["recommended_rail"],
            )
            traces.append(
                ToolTrace(
                    "schedule_payment",
                    {
                        "user_id": user_id,
                        "biller": selected_bill["biller"],
                        "amount": selected_bill["amount"],
                    },
                    payment,
                )
            )
            action_text = f"I scheduled a mock payment for {selected_bill['recommended_pay_date']}."
        else:
            action_text = "I can schedule it after your confirmation."

        draft = (
            f"{selected_bill['biller']} bill is Rs. {selected_bill['amount']:,.2f}, "
            f"due on {selected_bill['due_date']}. Recommended pay date: "
            f"{selected_bill['recommended_pay_date']} to avoid last-day risk. "
            f"Suggested rail: {rail['recommended_rail']} because {rail['reason']}. "
            f"{action_text}"
        )
        return AgentResponse(
            response=self.vertex.polish("Help user with safe mock bill payment.", draft),
            agent="Smart Payments Agent",
            user_id=user_id,
            traces=traces,
            next_steps=["For real banking, add OTP/2FA and maker-checker confirmation."],
        )

    def _account_service(self, message: str, user_id: str) -> AgentResponse:
        text = message.lower()
        traces: list[ToolTrace] = []

        if "balance" in text:
            balance = tool_service.get_balance(user_id)
            traces.append(ToolTrace("get_account_balance", {"user_id": user_id}, balance))
            draft = (
                f"Your available {balance['account_type']} balance is "
                f"Rs. {balance['available_balance']:,.2f} "
                f"({balance['account_number_masked']}) as of {balance['as_of']}."
            )
            return AgentResponse(
                response=self.vertex.polish("Answer balance queries using tool data.", draft),
                agent="Account Service Agent",
                user_id=user_id,
                traces=traces,
            )

        if "statement" in text or "summary" in text:
            summary = tool_service.get_statement_summary(user_id)
            traces.append(ToolTrace("get_statement_summary", {"user_id": user_id}, summary))
            top_categories = ", ".join(
                f"{item['category']} Rs. {item['amount']:,.2f}"
                for item in summary["top_spend_categories"]
            )
            draft = (
                f"Last 30 days: credits Rs. {summary['credits']:,.2f}, "
                f"debits Rs. {summary['debits']:,.2f}, net Rs. {summary['net']:,.2f}. "
                f"Top spends: {top_categories}."
            )
            return AgentResponse(
                response=self.vertex.polish("Summarize statement tool output.", draft),
                agent="Account Service Agent",
                user_id=user_id,
                traces=traces,
            )

        if "card" in text or "limit" in text or "block" in text:
            value: str | int | bool = "blocked" if "block" in text else self._extract_amount(message) or 100000
            control = "status" if "block" in text else "daily_limit"
            update = tool_service.update_card_control(user_id, control, value)
            traces.append(
                ToolTrace(
                    "update_card_control",
                    {"user_id": user_id, "control": control, "value": value},
                    update,
                )
            )
            draft = f"Mock card control updated: {control} is now {value} for card {update['card_id']}."
            return AgentResponse(
                response=self.vertex.polish("Confirm mock card control update.", draft),
                agent="Account Service Agent",
                user_id=user_id,
                traces=traces,
            )

        explanation = tool_service.explain_transaction(user_id, message)
        traces.append(ToolTrace("explain_transaction", {"user_id": user_id, "query": message}, explanation))
        return AgentResponse(
            response=self.vertex.polish("Explain transaction charges clearly.", explanation["explanation"]),
            agent="Account Service Agent",
            user_id=user_id,
            traces=traces,
        )

    def _goal(self, message: str, user_id: str) -> AgentResponse:
        amount = self._extract_amount(message) or 500000
        months = self._extract_months(message) or 18
        goal_name = self._extract_goal_name(message)
        plan = tool_service.create_goal_plan(user_id, goal_name, amount, months)
        traces = [
            ToolTrace(
                "create_goal_plan",
                {
                    "user_id": user_id,
                    "goal_name": goal_name,
                    "target_amount": amount,
                    "months": months,
                },
                plan,
            )
        ]
        draft = (
            f"For your {goal_name} goal of Rs. {amount:,.2f} in {months} months, "
            f"you need about Rs. {plan['monthly_required']:,.2f}/month. "
            f"Your estimated monthly surplus is Rs. {plan['estimated_monthly_surplus']:,.2f}, "
            f"so feasibility is {plan['feasibility']}. "
            f"Actions: {' '.join(plan['recommended_actions'])} "
            f"{plan['disclaimer']}"
        )
        return AgentResponse(
            response=self.vertex.polish("Create responsible savings goal plan.", draft),
            agent="Goal Agent",
            user_id=user_id,
            traces=traces,
            next_steps=["Connect real spending analytics after core banking APIs are available."],
        )

    def _rm_appointment(self, message: str, user_id: str) -> AgentResponse:
        slots = tool_service.list_rm_slots(user_id)
        traces = [ToolTrace("list_rm_slots", {"user_id": user_id}, slots)]

        if any(term in message.lower() for term in ["book", "schedule", "confirm"]):
            appointment = tool_service.book_rm_appointment(user_id)
            traces.append(ToolTrace("book_rm_appointment", {"user_id": user_id}, appointment))
            draft = (
                f"Your mock RM appointment is confirmed with {appointment['rm_name']} "
                f"at {appointment['starts_at']} via {appointment['mode']}."
            )
        else:
            slot_lines = [
                f"{slot['slot_id']}: {slot['starts_at']} via {slot['mode']}"
                for slot in slots["slots"]
                if slot["status"] == "available"
            ]
            draft = "Available RM slots:\n" + "\n".join(slot_lines)

        return AgentResponse(
            response=self.vertex.polish("Help user book relationship manager appointment.", draft),
            agent="RM Appointment Agent",
            user_id=user_id,
            traces=traces,
        )

    def _small_talk(self, message: str, user_id: str) -> AgentResponse:
        text = message.lower()
        if "thank" in text or "thanks" in text:
            draft = "You're welcome. Tell me whenever you want help with your account, payments, goals, cards, or RM appointment."
        else:
            draft = (
                "Hi, I am your Smart Banking Assistant. Tell me what you want to do, "
                "and I will choose the right banking agent and tools in the background. "
                "You can ask things like checking balance, explaining a charge, paying a bill, "
                "planning a savings goal, or booking an RM appointment."
            )
        return AgentResponse(
            response=self.vertex.polish("Handle simple greetings and capability questions.", draft),
            agent="Orchestrator Agent",
            user_id=user_id,
        )

    def _fallback(self, message: str, user_id: str) -> AgentResponse:
        draft = (
            "I can help with banking tasks such as account questions, bill payments, "
            "card controls, savings goals, and RM appointments. Please describe what "
            "you need, and I will route it to the right agent."
        )
        return AgentResponse(response=draft, agent="Orchestrator Agent", user_id=user_id)

    @staticmethod
    def _extract_amount(message: str) -> float | None:
        normalized = message.lower().replace(",", "")
        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac)", normalized)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000
        match = re.search(r"(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)", normalized)
        return float(match.group(1)) if match else None

    @staticmethod
    def _extract_months(message: str) -> int | None:
        text = message.lower()
        match = re.search(r"(\d+)\s*months?", text)
        if match:
            return int(match.group(1))
        years = re.search(r"(\d+)\s*years?", text)
        if years:
            return int(years.group(1)) * 12
        return None

    @staticmethod
    def _extract_participants(message: str) -> int | None:
        match = re.search(r"(\d+)\s*(people|friends|roommates|persons)", message.lower())
        return int(match.group(1)) if match else None

    @staticmethod
    def _extract_goal_name(message: str) -> str:
        text = message.lower()
        for goal in ["emergency fund", "vacation", "education", "wedding", "home down payment", "retirement"]:
            if goal in text:
                return goal
        return "savings"

    @staticmethod
    def _select_bill(message: str, bills: list[dict[str, Any]]) -> dict[str, Any] | None:
        text = message.lower()
        for bill in bills:
            if bill["biller"].lower() in text or bill["category"].lower() in text:
                return bill
        return bills[0] if bills else None
