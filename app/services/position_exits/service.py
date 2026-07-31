import hashlib
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings, get_settings
from app.services.order_intents import OrderIntent
from app.services.position_exits.engine import PositionExitEngine
from app.services.position_exits.models import (
    PositionExitContext,
    PositionExitRules,
    PositionExitSignal,
)
from app.services.position_exits.store import PositionExitSignalNotFoundError, PositionExitStore


class PositionExitSafetyError(PermissionError):
    """Raised when monitoring is attempted outside paper mode."""


class PositionExitMonitoringService:
    def __init__(self, store: PositionExitStore, settings: Settings | None = None) -> None:
        self.store = store
        self.settings = settings or get_settings()

    def rules(self) -> PositionExitRules:
        s = self.settings
        return PositionExitRules(
            Decimal(str(s.position_stop_loss_pct)),
            Decimal(str(s.position_first_target_pct)),
            Decimal(str(s.position_second_target_pct)),
            Decimal(str(s.position_first_target_exit_pct)),
            s.position_trailing_stop_enabled,
            Decimal(str(s.position_trailing_activation_pct)),
            Decimal(str(s.position_trailing_distance_pct)),
            s.position_max_holding_hours,
            s.position_expiration_exit_days,
            s.position_stale_mark_seconds,
        )

    async def monitor(self, context: PositionExitContext) -> PositionExitSignal | None:
        if self.settings.trading_mode != "paper":
            raise PositionExitSafetyError("Exit monitoring is restricted to paper mode.")
        evaluation = PositionExitEngine.evaluate(context, self.rules())
        if not evaluation.triggered:
            return None
        key = f"{context.position_id}|{evaluation.reason}|{evaluation.exit_quantity}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        signal_id = f"exit_{digest[:24]}"
        await self.store.reserve(digest, signal_id)
        now = datetime.now(UTC)
        signal = PositionExitSignal(
            signal_id,
            digest,
            context.position_id,
            context.account_id,
            context.symbol,
            context.option_symbol,
            evaluation.reason,
            evaluation.urgency,
            "APPROVED",
            evaluation.exit_quantity,
            evaluation.mark_price,
            evaluation.trigger_price,
            now,
            now,
            evaluation.explanations,
            evaluation.rejection_reasons,
        )
        await self.store.save(signal)
        return signal

    async def get(self, signal_id: str) -> PositionExitSignal:
        signal = await self.store.get(signal_id)
        if signal is None:
            raise PositionExitSignalNotFoundError(f"Exit signal {signal_id!r} was not found.")
        return signal

    async def list_for_position(self, position_id: str) -> list[PositionExitSignal]:
        return await self.store.list_for_position(position_id)

    def to_order_intent(self, signal: PositionExitSignal) -> OrderIntent:
        now = datetime.now(UTC)
        return OrderIntent(
            intent_id=f"exit_intent_{signal.idempotency_key[:24]}",
            idempotency_key=signal.idempotency_key,
            symbol=signal.symbol,
            option_symbol=signal.option_symbol,
            side="SELL",
            order_type="LIMIT",
            quantity=signal.requested_quantity,
            limit_price=signal.mark_price,
            estimated_debit=Decimal(0),
            maximum_loss=Decimal(0),
            stop_price=signal.mark_price,
            first_target_price=signal.mark_price,
            second_target_price=signal.mark_price,
            status="APPROVED",
            created_at=now,
            reasons=signal.explanations,
            rejection_reasons=(),
        )
