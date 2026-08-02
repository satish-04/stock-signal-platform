import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


class IBKROptionChainApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.contract_done = threading.Event()
        self.chain_done = threading.Event()
        self.underlying_conid = None

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def contractDetails(self, reqId, details) -> None:
        contract = details.contract
        if contract.secType == "STK" and contract.symbol == "AAPL":
            self.underlying_conid = contract.conId
            print(
                f"Qualified underlying: symbol={contract.symbol}, "
                f"conId={contract.conId}, "
                f"primaryExchange={contract.primaryExchange}"
            )

    def contractDetailsEnd(self, reqId: int) -> None:
        print(f"Underlying qualification complete. reqId={reqId}")
        self.contract_done.set()

    def securityDefinitionOptionParameter(
        self,
        reqId,
        exchange,
        underlyingConId,
        tradingClass,
        multiplier,
        expirations,
        strikes,
    ) -> None:
        print(
            f"Option chain: exchange={exchange}, "
            f"underlyingConId={underlyingConId}, "
            f"tradingClass={tradingClass}, "
            f"multiplier={multiplier}, "
            f"expiration_count={len(expirations)}, "
            f"strike_count={len(strikes)}"
        )

        sample_expirations = sorted(expirations)[:10]
        sample_strikes = sorted(strikes)[:20]

        print(f"Sample expirations: {sample_expirations}")
        print(f"Sample strikes: {sample_strikes}")

    def securityDefinitionOptionParameterEnd(self, reqId: int) -> None:
        print(f"Option-chain discovery complete. reqId={reqId}")
        self.chain_done.set()

    def error(
        self,
        reqId,
        errorTime,
        errorCode,
        errorString,
        advancedOrderRejectJson="",
    ) -> None:
        if errorCode in {2104, 2106, 2158}:
            print(f"IBKR status: code={errorCode}, message={errorString}")
            return

        print(
            f"IBKR message: reqId={reqId}, time={errorTime}, "
            f"code={errorCode}, message={errorString}"
        )


app = IBKROptionChainApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=51)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

contract = Contract()
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"

print("Qualifying AAPL underlying...")
app.reqContractDetails(9701, contract)

if not app.contract_done.wait(timeout=20):
    print("Underlying qualification timed out.")
    app.disconnect()
    raise SystemExit(1)

if not app.underlying_conid:
    print("No underlying conId found.")
    app.disconnect()
    raise SystemExit(1)

print("Requesting AAPL option-chain parameters...")

app.reqSecDefOptParams(
    reqId=9702,
    underlyingSymbol="AAPL",
    futFopExchange="",
    underlyingSecType="STK",
    underlyingConId=app.underlying_conid,
)

if not app.chain_done.wait(timeout=30):
    print("Option-chain request timed out.")

time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
