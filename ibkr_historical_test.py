import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


class IBKRHistoricalApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.historical_done = threading.Event()
        self.bar_count = 0

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def historicalData(self, reqId, bar) -> None:
        self.bar_count += 1
        print(
            f"Bar {self.bar_count}: "
            f"date={bar.date}, "
            f"open={bar.open}, "
            f"high={bar.high}, "
            f"low={bar.low}, "
            f"close={bar.close}, "
            f"volume={bar.volume}"
        )

    def historicalDataEnd(self, reqId, start, end) -> None:
        print(
            f"Historical data complete. reqId={reqId}, "
            f"start={start}, end={end}, bars={self.bar_count}"
        )
        self.historical_done.set()

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


app = IBKRHistoricalApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=50)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

contract = Contract()
contract.conId = 265598
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"
contract.primaryExchange = "NASDAQ"

print("Requesting one day of 5-minute AAPL historical bars...")

app.reqHistoricalData(
    reqId=9601,
    contract=contract,
    endDateTime="",
    durationStr="1 D",
    barSizeSetting="5 mins",
    whatToShow="TRADES",
    useRTH=1,
    formatDate=1,
    keepUpToDate=False,
    chartOptions=[],
)

if not app.historical_done.wait(timeout=30):
    print("Historical data request timed out.")

time.sleep(1)
app.disconnect()
print("Disconnected cleanly.")
