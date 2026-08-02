import threading
import time

from ibapi.client import EClient
from ibapi.wrapper import EWrapper


class IBKRPositionsApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.positions_done = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def managedAccounts(self, accountsList: str) -> None:
        print(f"Managed accounts: {accountsList}")

    def position(self, account, contract, position, avgCost) -> None:
        print(
            f"Position: account={account}, "
            f"symbol={contract.symbol}, "
            f"secType={contract.secType}, "
            f"position={position}, "
            f"avgCost={avgCost}"
        )

    def positionEnd(self) -> None:
        print("Position download complete.")
        self.positions_done.set()

    def currentTime(self, time_value: int) -> None:
        print(f"IBKR server time: {time_value}")

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


app = IBKRPositionsApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=44)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

print("Requesting IBKR server time...")
app.reqCurrentTime()

print("Requesting positions...")
app.reqPositions()

if not app.positions_done.wait(timeout=20):
    print("Positions request timed out.")

app.cancelPositions()
time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
