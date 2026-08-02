import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


class IBKROptionContractApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.contract_done = threading.Event()
        self.contract_count = 0

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def contractDetails(self, reqId, details) -> None:
        self.contract_count += 1
        contract = details.contract

        print(
            "Option contract found: "
            f"conId={contract.conId}, "
            f"symbol={contract.symbol}, "
            f"localSymbol={contract.localSymbol}, "
            f"right={contract.right}, "
            f"strike={contract.strike}, "
            f"expiry={contract.lastTradeDateOrContractMonth}, "
            f"exchange={contract.exchange}, "
            f"tradingClass={contract.tradingClass}, "
            f"multiplier={contract.multiplier}, "
            f"currency={contract.currency}, "
            f"minTick={details.minTick}"
        )

    def contractDetailsEnd(self, reqId: int) -> None:
        print(
            f"Option qualification complete. "
            f"reqId={reqId}, contracts={self.contract_count}"
        )
        self.contract_done.set()

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


app = IBKROptionContractApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=52)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

option = Contract()
option.symbol = "AAPL"
option.secType = "OPT"
option.exchange = "SMART"
option.currency = "USD"
option.lastTradeDateOrContractMonth = "20260821"
option.strike = 300
option.right = "C"
option.multiplier = "100"
option.tradingClass = "AAPL"

print("Qualifying AAPL 2026-08-21 $300 call...")
app.reqContractDetails(9801, option)

if not app.contract_done.wait(timeout=20):
    print("Option contract request timed out.")

time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
