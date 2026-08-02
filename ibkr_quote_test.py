import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import EWrapper


class IBKRQuoteApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.quote_done = threading.Event()
        self.received_ticks = 0

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def marketDataType(self, reqId: int, marketDataType: int) -> None:
        print(
            f"Market data type confirmed: reqId={reqId}, "
            f"type={marketDataType}"
        )

    def tickPrice(self, reqId, tickType, price, attrib) -> None:
        tick_name = TickTypeEnum.toStr(tickType)
        self.received_ticks += 1
        print(
            f"tickPrice: reqId={reqId}, "
            f"tickType={tickType} ({tick_name}), price={price}"
        )

    def tickSize(self, reqId, tickType, size) -> None:
        tick_name = TickTypeEnum.toStr(tickType)
        self.received_ticks += 1
        print(
            f"tickSize: reqId={reqId}, "
            f"tickType={tickType} ({tick_name}), size={size}"
        )

    def tickString(self, reqId, tickType, value) -> None:
        tick_name = TickTypeEnum.toStr(tickType)
        self.received_ticks += 1
        print(
            f"tickString: reqId={reqId}, "
            f"tickType={tickType} ({tick_name}), value={value}"
        )

    def tickSnapshotEnd(self, reqId: int) -> None:
        print(
            f"Snapshot complete. reqId={reqId}, "
            f"received_ticks={self.received_ticks}"
        )
        self.quote_done.set()

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


app = IBKRQuoteApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=47)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

app.reqMarketDataType(3)

contract = Contract()
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"
contract.primaryExchange = "NASDAQ"

print("Requesting delayed AAPL market-data snapshot...")
app.reqMktData(
    reqId=9301,
    contract=contract,
    genericTickList="",
    snapshot=True,
    regulatorySnapshot=False,
    mktDataOptions=[],
)

if not app.quote_done.wait(timeout=30):
    print("Quote request timed out.")

time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
