from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


class IBKRDependencyError(RuntimeError):
    """Raised when the official IBKR Python API is unavailable."""


class IBKRConnectionError(RuntimeError):
    """Raised when a connection to TWS or IB Gateway cannot be established."""


class IBKRRequestError(RuntimeError):
    """Raised when IBKR rejects or fails a historical-data request."""


@dataclass(frozen=True)
class IBKRHistoricalBar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class IBKRHistoricalClient:
    STATUS_CODES = {
        2104,
        2106,
        2107,
        2108,
        2158,
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
        try:
            from ibapi.client import EClient
            from ibapi.contract import Contract
            from ibapi.wrapper import EWrapper
        except ImportError as exc:
            raise IBKRDependencyError(
                "The official IBKR Python API is not installed. "
                "Install it from the official TWS API package."
            ) from exc

        return EClient, EWrapper, Contract

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        from zoneinfo import ZoneInfo

        normalized = value.strip()

        if normalized.endswith(" US/Eastern"):
            raw_timestamp = normalized.removesuffix(" US/Eastern")
            parsed = datetime.strptime(
                raw_timestamp,
                "%Y%m%d %H:%M:%S",
            )
            return parsed.replace(
                tzinfo=ZoneInfo("America/New_York"),
            )

        supported_formats = (
            "%Y%m%d %H:%M:%S",
            "%Y%m%d",
        )

        for timestamp_format in supported_formats:
            try:
                return datetime.strptime(
                    normalized,
                    timestamp_format,
                )
            except ValueError:
                continue

        raise IBKRRequestError(
            f"Unsupported IBKR historical timestamp: {value!r}"
        )

    def fetch(
        self,
        symbol: str,
        duration: str,
        bar_size: str,
        use_rth: bool,
    ) -> list[IBKRHistoricalBar]:
        EClient, EWrapper, Contract = self._load_ibkr_api()

        connection_ready = threading.Event()
        request_done = threading.Event()
        bars: list[IBKRHistoricalBar] = []
        request_errors: list[str] = []

        outer = self

        class HistoricalApp(EWrapper, EClient):
            def __init__(self) -> None:
                EClient.__init__(self, self)

            def nextValidId(self, orderId: int) -> None:
                del orderId
                connection_ready.set()

            def historicalData(self, reqId: int, bar: Any) -> None:
                del reqId

                try:
                    volume = int(float(bar.volume))
                    timestamp = outer._parse_timestamp(str(bar.date))

                    bars.append(
                        IBKRHistoricalBar(
                            timestamp=timestamp,
                            open=Decimal(str(bar.open)),
                            high=Decimal(str(bar.high)),
                            low=Decimal(str(bar.low)),
                            close=Decimal(str(bar.close)),
                            volume=volume,
                        )
                    )
                except (TypeError, ValueError) as exc:
                    request_errors.append(
                        f"Unable to parse historical bar: {exc}"
                    )
                    request_done.set()

            def historicalDataEnd(
                self,
                reqId: int,
                start: str,
                end: str,
            ) -> None:
                del reqId, start, end
                request_done.set()

            def error(self, *args: Any) -> None:
                # Current IBKR API:
                # reqId, errorTime, errorCode, errorString,
                # advancedOrderRejectJson
                #
                # Older IBKR API:
                # reqId, errorCode, errorString,
                # advancedOrderRejectJson
                if len(args) >= 4 and isinstance(args[2], int):
                    error_code = args[2]
                    error_message = str(args[3])
                elif len(args) >= 3:
                    error_code = args[1]
                    error_message = str(args[2])
                else:
                    request_errors.append(
                        f"Unrecognized IBKR error callback: {args!r}"
                    )
                    request_done.set()
                    return

                if error_code in outer.STATUS_CODES:
                    return

                request_errors.append(
                    f"IBKR error {error_code}: {error_message}"
                )
                request_done.set()

        app = HistoricalApp()

        try:
            app.connect(
                self.host,
                self.port,
                clientId=self.client_id,
            )

            event_thread = threading.Thread(
                target=app.run,
                daemon=True,
                name=f"ibkr-client-{self.client_id}",
            )
            event_thread.start()

            if not connection_ready.wait(self.connection_timeout):
                raise IBKRConnectionError(
                    f"IBKR connection timed out after "
                    f"{self.connection_timeout} seconds."
                )

            contract = Contract()
            contract.symbol = symbol.upper()
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            app.reqHistoricalData(
                reqId=1,
                contract=contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=1 if use_rth else 0,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[],
            )

            if not request_done.wait(self.request_timeout):
                app.cancelHistoricalData(1)
                raise IBKRRequestError(
                    f"Historical-data request timed out after "
                    f"{self.request_timeout} seconds."
                )

            if request_errors:
                raise IBKRRequestError("; ".join(request_errors))

            if not bars:
                raise IBKRRequestError(
                    f"IBKR returned no historical bars for "
                    f"{symbol.upper()}."
                )

            return bars

        finally:
            if app.isConnected():
                app.disconnect()
