from __future__ import annotations

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from app.services.trade_risk.models import (
    RiskLimits,
    TradeConstructionRequest,
    TradePlan,
)

ZERO = Decimal(0)
ONE_HUNDRED = Decimal(100)
PRICE_TICK = Decimal("0.01")
PERCENT_TICK = Decimal("0.01")
MONEY_TICK = Decimal("0.01")


class TradeRiskEngine:
    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(MONEY_TICK, rounding=ROUND_HALF_UP)

    @staticmethod
    def _price(value: Decimal) -> Decimal:
        return value.quantize(PRICE_TICK, rounding=ROUND_HALF_UP)

    @staticmethod
    def _percent(value: Decimal) -> Decimal:
        return value.quantize(PERCENT_TICK, rounding=ROUND_HALF_UP)

    @staticmethod
    def _validate_limits(limits: RiskLimits) -> None:
        if limits.account_equity <= ZERO:
            raise ValueError("account_equity must be greater than zero.")
        if limits.available_funds < ZERO:
            raise ValueError("available_funds must not be negative.")
        if not ZERO < limits.max_risk_per_trade_pct <= ONE_HUNDRED:
            raise ValueError("max_risk_per_trade_pct must be between 0 and 100.")
        if not ZERO < limits.max_position_value_pct <= ONE_HUNDRED:
            raise ValueError("max_position_value_pct must be between 0 and 100.")
        if limits.max_contracts <= 0:
            raise ValueError("max_contracts must be greater than zero.")
        if limits.max_bid_ask_spread_pct < ZERO:
            raise ValueError("max_bid_ask_spread_pct must not be negative.")
        if limits.minimum_open_interest < 0:
            raise ValueError("minimum_open_interest must not be negative.")
        if limits.minimum_volume < 0:
            raise ValueError("minimum_volume must not be negative.")
        if limits.minimum_reward_risk_ratio <= ZERO:
            raise ValueError("minimum_reward_risk_ratio must be greater than zero.")

    @staticmethod
    def _validate_request(request: TradeConstructionRequest) -> None:
        if not request.symbol.strip():
            raise ValueError("symbol must not be empty.")
        if not request.option_symbol.strip():
            raise ValueError("option_symbol must not be empty.")
        if request.multiplier <= 0:
            raise ValueError("multiplier must be greater than zero.")
        if request.bid < ZERO:
            raise ValueError("bid must not be negative.")
        if request.ask <= ZERO:
            raise ValueError("ask must be greater than zero.")
        if request.ask < request.bid:
            raise ValueError("ask must be greater than or equal to bid.")
        if request.last < ZERO:
            raise ValueError("last must not be negative.")
        if request.volume < 0:
            raise ValueError("volume must not be negative.")
        if request.open_interest < 0:
            raise ValueError("open_interest must not be negative.")
        if not ZERO <= request.confidence <= ONE_HUNDRED:
            raise ValueError("confidence must be between 0 and 100.")
        if not ZERO < request.stop_loss_pct < ONE_HUNDRED:
            raise ValueError("stop_loss_pct must be between 0 and 100.")
        if request.first_target_pct <= ZERO:
            raise ValueError("first_target_pct must be greater than zero.")
        if request.second_target_pct <= request.first_target_pct:
            raise ValueError("second_target_pct must be greater than first_target_pct.")

    @staticmethod
    def _expected_option_type(action: str) -> str | None:
        if action == "BUY_CALL":
            return "CALL"
        if action == "BUY_PUT":
            return "PUT"
        return None

    @classmethod
    def construct(
        cls,
        request: TradeConstructionRequest,
        limits: RiskLimits,
    ) -> TradePlan:
        cls._validate_request(request)
        cls._validate_limits(limits)

        reasons: list[str] = []
        rejection_reasons: list[str] = []
        symbol = request.symbol.strip().upper()
        option_symbol = request.option_symbol.strip()
        midpoint = (request.bid + request.ask) / Decimal(2)
        limit_price = cls._price(midpoint)
        spread = request.ask - request.bid
        bid_ask_spread_pct = (
            cls._percent((spread / midpoint) * ONE_HUNDRED)
            if midpoint > ZERO
            else Decimal("100.00")
        )
        stop_price = cls._price(
            limit_price * (Decimal(1) - request.stop_loss_pct / ONE_HUNDRED)
        )
        first_target_price = cls._price(
            limit_price * (Decimal(1) + request.first_target_pct / ONE_HUNDRED)
        )
        second_target_price = cls._price(
            limit_price * (Decimal(1) + request.second_target_pct / ONE_HUNDRED)
        )
        stop_risk_per_share = limit_price - stop_price
        first_target_reward_per_share = first_target_price - limit_price
        reward_risk_ratio = (
            cls._percent(first_target_reward_per_share / stop_risk_per_share)
            if stop_risk_per_share > ZERO
            else ZERO
        )
        contract_cost = cls._money(limit_price * Decimal(request.multiplier))
        risk_budget = cls._money(
            limits.account_equity * limits.max_risk_per_trade_pct / ONE_HUNDRED
        )
        position_value_budget = cls._money(
            limits.account_equity * limits.max_position_value_pct / ONE_HUNDRED
        )
        capital_budget = min(risk_budget, position_value_budget, limits.available_funds)
        affordable_contracts = (
            int((capital_budget / contract_cost).to_integral_value(rounding=ROUND_DOWN))
            if contract_cost > ZERO
            else 0
        )
        quantity = min(affordable_contracts, limits.max_contracts)
        estimated_debit = cls._money(contract_cost * Decimal(quantity))
        maximum_loss = estimated_debit
        account_risk_pct = cls._percent(
            maximum_loss / limits.account_equity * ONE_HUNDRED
        )
        expected_option_type = cls._expected_option_type(request.action)

        if request.action == "HOLD":
            rejection_reasons.append("HOLD recommendations cannot create an order.")
        if expected_option_type is not None and request.option_type != expected_option_type:
            rejection_reasons.append(
                "Selected option type does not match the recommended action."
            )
        if bid_ask_spread_pct > limits.max_bid_ask_spread_pct:
            rejection_reasons.append("Bid/ask spread exceeds the configured limit.")
        else:
            reasons.append("Bid/ask spread is within the configured limit.")
        if request.open_interest < limits.minimum_open_interest:
            rejection_reasons.append("Open interest is below the configured minimum.")
        else:
            reasons.append("Open interest meets the liquidity requirement.")
        if request.volume < limits.minimum_volume:
            rejection_reasons.append("Volume is below the configured minimum.")
        else:
            reasons.append("Volume meets the liquidity requirement.")
        if reward_risk_ratio < limits.minimum_reward_risk_ratio:
            rejection_reasons.append(
                "Reward-to-risk ratio is below the configured minimum."
            )
        else:
            reasons.append("Reward-to-risk ratio meets the configured minimum.")
        if quantity <= 0:
            rejection_reasons.append("Available risk capital cannot fund one contract.")
        else:
            reasons.append("Position size is within capital and contract limits.")
        if maximum_loss > risk_budget:
            rejection_reasons.append("Maximum loss exceeds the per-trade risk budget.")
        if estimated_debit > position_value_budget:
            rejection_reasons.append("Position value exceeds the configured limit.")
        if estimated_debit > limits.available_funds:
            rejection_reasons.append("Estimated debit exceeds available funds.")

        decision = "REJECTED" if rejection_reasons else "APPROVED"
        if decision == "APPROVED":
            reasons.append("Trade plan passed all deterministic risk checks.")

        return TradePlan(
            symbol=symbol,
            option_symbol=option_symbol,
            decision=decision,
            side="BUY",
            order_type="LIMIT",
            quantity=quantity,
            limit_price=limit_price,
            estimated_debit=estimated_debit,
            maximum_loss=maximum_loss,
            stop_price=stop_price,
            first_target_price=first_target_price,
            second_target_price=second_target_price,
            reward_risk_ratio=reward_risk_ratio,
            account_risk_pct=account_risk_pct,
            bid_ask_spread_pct=bid_ask_spread_pct,
            reasons=tuple(reasons),
            rejection_reasons=tuple(rejection_reasons),
        )
