import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import EWrapper


class IBKRQuoteStreamApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.received_tick = threading.Event()
        self.tick_count = 0

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def marketDataType(self, reqId: int, marketDataType: int) -> None:
        print(
            f"Market data type: reqId={reqId}, "
            f"type={marketDataType}"
        )

    def tickReqParams(
        self,
        tickerId: int,
        minTick: float,
        bboExchange: str,
        snapshotPermissions: int,
    ) -> None:
        print(
            f"Tick parameters: tickerId={tickerId}, "
            f"minTick={minTick}, exchange={bboExchange}, "
            f"snapshotPermissions={snapshotPermissions}"
        )

    def tickPrice(self, reqId, tickType, price, attrib) -> None:
        self.tick_count += 1
        self.received_tick.set()
        print(
            f"tickPrice: reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"price={price}"
        )

    def tickSize(self, reqId, tickType, size) -> None:
        self.tick_count += 1
        self.received_tick.set()
        print(
            f"tickSize: reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"size={size}"
        )

    def tickString(self, reqId, tickType, value) -> None:
        self.tick_count += 1
        self.received_tick.set()
        print(
            f"tickString: reqId={reqId}, "
            f"type={tickType} ({TickTypeEnum.toStr(tickType)}), "
            f"value={value}"
        )

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


app = IBKRQuoteStreamApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=48)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

# 3 = delayed streaming market data
app.reqMarketDataType(3)

contract = Contract()
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"
contract.primaryExchange = "NASDAQ"

print("Requesting delayed streaming AAPL data for 30 seconds...")

app.reqMktData(
    reqId=9401,
    contract=contract,
    genericTickList="",
    snapshot=False,
    regulatorySnapshot=False,
    mktDataOptions=[],
)

app.received_tick.wait(timeout=30)

time.sleep(5)

app.cancelMktData(9401)

print(f"Total ticks received: {app.tick_count}")

app.disconnect()
print("Disconnected cleanly.")
