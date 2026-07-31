from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings, get_settings
from app.services.brokers.base import BrokerAdapter
from app.services.order_intents.models import OrderIntent, OrderSubmissionResult
from app.services.order_intents.store import InMemoryOrderIntentStore
from app.services.trade_risk.models import TradePlan

ZERO = Decimal(0)


class OrderIntentRejectedError(RuntimeError):
    """Raised when a trade plan cannot become an order intent."""


class OrderSubmissionDisabledError(PermissionError):
    """Raised when broker submission is disabled by configuration."""


class LiveTradingBlockedError(PermissionError):
    """Raised when execution is attempted outside paper mode."""


class PaperOrderApprovalService:
    def __init__(
        self,
        broker: BrokerAdapter,
        store: InMemoryOrderIntentStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.broker = broker
        self.store = store or InMemoryOrderIntentStore()
        self.settings = settings or get_settings()

    @staticmethod
    def _idempotency_key(trade_plan: TradePlan) -> str:
        payload = "|".join(
            [
                trade_plan.symbol,
                trade_plan.option_symbol,
                trade_plan.side,
                trade_plan.order_type,
                str(trade_plan.quantity),
                str(trade_plan.limit_price),
                str(trade_plan.maximum_loss),
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _intent_id(idempotency_key: str) -> str:
        return f"intent_{idempotency_key[:24]}"

    @staticmethod
    def _validate_trade_plan(trade_plan: TradePlan) -> None:
        if trade_plan.decision != "APPROVED":
            raise OrderIntentRejectedError(
                "Only APPROVED trade plans may become order intents."
            )
        if trade_plan.rejection_reasons:
            raise OrderIntentRejectedError(
                "Approved trade plan contains rejection reasons."
            )
        if trade_plan.quantity <= 0:
            raise OrderIntentRejectedError(
                "Trade plan quantity must be greater than zero."
            )
        if trade_plan.limit_price <= ZERO:
            raise OrderIntentRejectedError(
                "Trade plan limit price must be greater than zero."
            )
        if trade_plan.maximum_loss <= ZERO:
            raise OrderIntentRejectedError(
                "Trade plan maximum loss must be greater than zero."
            )

    def create_intent(self, trade_plan: TradePlan) -> OrderIntent:
        self._validate_trade_plan(trade_plan)
        idempotency_key = self._idempotency_key(trade_plan)
        self.store.register(idempotency_key)
        return OrderIntent(
            intent_id=self._intent_id(idempotency_key),
            idempotency_key=idempotency_key,
            symbol=trade_plan.symbol,
            option_symbol=trade_plan.option_symbol,
            side=trade_plan.side,
            order_type=trade_plan.order_type,
            quantity=trade_plan.quantity,
            limit_price=trade_plan.limit_price,
            estimated_debit=trade_plan.estimated_debit,
            maximum_loss=trade_plan.maximum_loss,
            stop_price=trade_plan.stop_price,
            first_target_price=trade_plan.first_target_price,
            second_target_price=trade_plan.second_target_price,
            status="APPROVED",
            created_at=datetime.now(UTC),
            reasons=trade_plan.reasons,
            rejection_reasons=trade_plan.rejection_reasons,
        )

    async def submit(self, trade_plan: TradePlan) -> OrderSubmissionResult:
        if self.settings.trading_mode != "paper":
            raise LiveTradingBlockedError(
                "Order-intent submission is restricted to paper mode."
            )
        if not self.settings.enable_order_submission:
            raise OrderSubmissionDisabledError("Order submission is disabled.")

        intent = self.create_intent(trade_plan)
        order_payload = {
            "intent_id": intent.intent_id,
            "idempotency_key": intent.idempotency_key,
            "symbol": intent.symbol,
            "option_symbol": intent.option_symbol,
            "side": intent.side,
            "order_type": intent.order_type,
            "quantity": intent.quantity,
            "limit_price": str(intent.limit_price),
            "transmit": False,
            "trading_mode": "paper",
        }
        try:
            response = await self.broker.submit_order(order_payload)
        except RuntimeError as exc:
            return OrderSubmissionResult(
                intent=replace(intent, status="FAILED"),
                broker_response={"error": str(exc)},
            )
        return OrderSubmissionResult(
            intent=replace(intent, status="SUBMITTED"),
            broker_response=response,
        )
