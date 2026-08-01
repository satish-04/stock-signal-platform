from __future__ import annotations

import threading
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


class IBKROptionsError(RuntimeError):
    pass


@dataclass(frozen=True)
class IBKROptionSnapshot:
    conid: int
    symbol: str
    expiry: str
    strike: Decimal
    right: str
    bid: Decimal
    ask: Decimal
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float


class IBKROptionsClient:
    STATUS_CODES = {
        2104,
        2106,
        2107,
        2108,
        2158,
        10167,
    }

    def __init__(
        self,
        host: str,
        port: int,
        client_id: int,
        connection_timeout: float = 10.0,
        request_timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connection_timeout = connection_timeout
        self.request_timeout = request_timeout

    @staticmethod
    def _load_ibkr_api() -> tuple[Any, Any, Any]:
        from ibapi.client import EClient
        from ibapi.contract import Contract
        from ibapi.wrapper import EWrapper

        return EClient, EWrapper, Contract

    def fetch_chain(
        self,
        symbol: str,
    ) -> list[IBKROptionSnapshot]:
        EClient, EWrapper, Contract = self._load_ibkr_api()

        connection_ready = threading.Event()
        underlying_done = threading.Event()
        chain_done = threading.Event()

        errors: list[str] = []

        underlying_conid: int | None = None
        expirations: set[str] = set()
        strikes: set[float] = set()

        outer = self

        class OptionApp(EWrapper, EClient):
            def __init__(self) -> None:
                EClient.__init__(self, self)

            def nextValidId(self, orderId: int) -> None:
                del orderId
                connection_ready.set()

            def contractDetails(self, reqId: int, details: Any) -> None:
                nonlocal underlying_conid

                if reqId == 1001:
                    contract = details.contract

                    if (
                        contract.secType == "STK"
                        and contract.symbol.upper() == symbol.upper()
                    ):
                        underlying_conid = contract.conId

            def contractDetailsEnd(self, reqId: int) -> None:
                if reqId == 1001:
                    underlying_done.set()

            def securityDefinitionOptionParameter(
                self,
                reqId: int,
                exchange: str,
                underlyingConId: int,
                tradingClass: str,
                multiplier: str,
                expiration_values: set[str],
                strike_values: set[float],
            ) -> None:
                del reqId, underlyingConId, tradingClass, multiplier

                if exchange == "SMART":
                    expirations.update(expiration_values)
                    strikes.update(strike_values)

            def securityDefinitionOptionParameterEnd(
                self,
                reqId: int,
            ) -> None:
                del reqId
                chain_done.set()

            def error(self, *args: Any) -> None:
                if len(args) >= 4 and isinstance(args[2], int):
                    error_code = args[2]
                    error_message = str(args[3])
                elif len(args) >= 3:
                    error_code = args[1]
                    error_message = str(args[2])
                else:
                    errors.append(
                        f"Unrecognized IBKR error callback: {args!r}"
                    )
                    return

                if error_code in outer.STATUS_CODES:
                    return

                errors.append(
                    f"IBKR error {error_code}: {error_message}"
                )

        app = OptionApp()

        try:
            app.connect(
                self.host,
                self.port,
                clientId=self.client_id,
            )

            thread = threading.Thread(
                target=app.run,
                daemon=True,
                name=f"ibkr-options-{self.client_id}",
            )
            thread.start()

            if not connection_ready.wait(self.connection_timeout):
                raise IBKROptionsError(
                    "IBKR connection timed out."
                )

            underlying = Contract()
            underlying.symbol = symbol.upper()
            underlying.secType = "STK"
            underlying.exchange = "SMART"
            underlying.currency = "USD"

            app.reqContractDetails(
                1001,
                underlying,
            )

            if not underlying_done.wait(self.request_timeout):
                raise IBKROptionsError(
                    "Underlying contract qualification timed out."
                )

            if underlying_conid is None:
                raise IBKROptionsError(
                    f"Unable to qualify underlying {symbol.upper()}."
                )

            app.reqSecDefOptParams(
                reqId=1002,
                underlyingSymbol=symbol.upper(),
                futFopExchange="",
                underlyingSecType="STK",
                underlyingConId=underlying_conid,
            )

            if not chain_done.wait(self.request_timeout):
                raise IBKROptionsError(
                    "Option-chain discovery timed out."
                )

            if errors:
                raise IBKROptionsError("; ".join(errors))

            if not expirations or not strikes:
                raise IBKROptionsError(
                    f"No option-chain parameters returned for "
                    f"{symbol.upper()}."
                )

            nearest_expiry = sorted(expirations)[0]

            qualification_done = threading.Event()
            qualified_snapshots: list[IBKROptionSnapshot] = []

            original_contract_details = app.contractDetails
            original_contract_details_end = app.contractDetailsEnd

            def qualified_contract_details(
                reqId: int,
                details: Any,
            ) -> None:
                if reqId != 2000:
                    original_contract_details(reqId, details)
                    return

                contract = details.contract

                if contract.secType != "OPT":
                    return

                if contract.lastTradeDateOrContractMonth != nearest_expiry:
                    return

                if not (250.0 <= float(contract.strike) <= 350.0):
                    return

                qualified_snapshots.append(
                    IBKROptionSnapshot(
                        conid=contract.conId,
                        symbol=contract.symbol,
                        expiry=contract.lastTradeDateOrContractMonth,
                        strike=Decimal(str(contract.strike)),
                        right=contract.right,
                        bid=Decimal("0"),
                        ask=Decimal("0"),
                        volume=0,
                        open_interest=0,
                        implied_volatility=0.0,
                        delta=0.0,
                        gamma=0.0,
                        theta=0.0,
                        vega=0.0,
                    )
                )

            def qualified_contract_details_end(
                reqId: int,
            ) -> None:
                if reqId == 2000:
                    qualification_done.set()
                    return

                original_contract_details_end(reqId)

            app.contractDetails = qualified_contract_details
            app.contractDetailsEnd = qualified_contract_details_end

            option = Contract()
            option.symbol = symbol.upper()
            option.secType = "OPT"
            option.exchange = "SMART"
            option.currency = "USD"
            option.lastTradeDateOrContractMonth = nearest_expiry
            option.multiplier = "100"

            app.reqContractDetails(
                2000,
                option,
            )

            if not qualification_done.wait(self.request_timeout):
                raise IBKROptionsError(
                    f"Option qualification timed out for "
                    f"{symbol.upper()} {nearest_expiry}."
                )

            snapshots = sorted(
                qualified_snapshots,
                key=lambda item: (
                    item.strike,
                    item.right,
                ),
            )

            if not snapshots:
                raise IBKROptionsError(
                    f"No qualified option contracts returned for "
                    f"{symbol.upper()} {nearest_expiry}."
                )

            return snapshots

        finally:
            if app.isConnected():
                app.disconnect()
