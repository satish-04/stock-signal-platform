import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import EWrapper


class IBKROptionQuoteApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.snapshot_done = threading.Event()
        self.tick_count = 0

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def marketDataType(self, reqId: int, marketDataType: int) -> None:
        print(
            f"Market data type confirmed: "
            f"reqId={reqId}, type={marketDataType}"
        )

    def tickPrice(self, reqId, tickType, price, attrib) -> None:
        self.tick_count += 1
        print(
            f"tickPrice: reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"price={price}"
        )

    def tickSize(self, reqId, tickType, size) -> None:
        self.tick_count += 1
        print(
            f"tickSize: reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"size={size}"
        )

    def tickOptionComputation(
        self,
        reqId,
        tickType,
        tickAttrib,
        impliedVol,
        delta,
        optPrice,
        pvDividend,
        gamma,
        vega,
        theta,
        undPrice,
    ) -> None:
        self.tick_count += 1
        print(
            "Option computation: "
            f"reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"iv={impliedVol}, "
            f"delta={delta}, "
            f"gamma={gamma}, "
            f"vega={vega}, "
            f"theta={theta}, "
            f"optionPrice={optPrice}, "
            f"underlyingPrice={undPrice}"
        )

    def tickSnapshotEnd(self, reqId: int) -> None:
        print(
            f"Snapshot complete. reqId={reqId}, "
            f"received_ticks={self.tick_count}"
        )
        self.snapshot_done.set()

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


app = IBKROptionQuoteApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=53)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

# Request delayed data where available.
app.reqMarketDataType(3)

option = Contract()
option.conId = 805712094
option.symbol = "AAPL"
option.secType = "OPT"
option.exchange = "SMART"
option.currency = "USD"
option.lastTradeDateOrContractMonth = "20260821"
option.strike = 300
option.right = "C"
option.multiplier = "100"
option.tradingClass = "AAPL"

print("Requesting delayed option snapshot and Greeks...")

app.reqMktData(
    reqId=9901,
    contract=option,
    genericTickList="100,101,104,106",
    snapshot=False,
    regulatorySnapshot=False,
    mktDataOptions=[],
)

time.sleep(30)
app.cancelMktData(9901)
print(f"Streaming complete. received_ticks={app.tick_count}")
time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
