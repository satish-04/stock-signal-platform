import threading
import time

from ibapi.client import EClient
from ibapi.wrapper import EWrapper


class IBKRTestApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected to IBKR TWS. nextValidId={orderId}")
        self.connected_event.set()

    def managedAccounts(self, accountsList: str) -> None:
        print(f"Managed accounts: {accountsList}")

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson="") -> None:
        print(
            f"IBKR message: reqId={reqId}, "
            f"code={errorCode}, message={errorString}"
        )


app = IBKRTestApp()

print("Connecting to TWS paper API at 127.0.0.1:7497...")
app.connect("127.0.0.1", 7497, clientId=41)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection failed or timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)
app.disconnect()
print("Disconnected cleanly.")
