import threading
import time

from ibapi.client import EClient
from ibapi.wrapper import EWrapper


ACCOUNT_ID = "DUR500987"


class IBKRAccountUpdatesApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.download_complete = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def managedAccounts(self, accountsList: str) -> None:
        print(f"Managed accounts: {accountsList}")

    def updateAccountValue(
        self,
        key: str,
        value: str,
        currency: str,
        accountName: str,
    ) -> None:
        allowed_keys = {
            "NetLiquidation",
            "TotalCashValue",
            "BuyingPower",
            "AvailableFunds",
            "ExcessLiquidity",
            "GrossPositionValue",
            "MaintMarginReq",
            "InitMarginReq",
            "AccountType",
        }

        if key in allowed_keys:
            print(
                f"Account={accountName} | Key={key} | "
                f"Value={value} | Currency={currency}"
            )

    def accountDownloadEnd(self, accountName: str) -> None:
        print(f"Account download complete: {accountName}")
        self.download_complete.set()

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


app = IBKRAccountUpdatesApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=43)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(1)

print(f"Requesting account updates for {ACCOUNT_ID}...")
app.reqAccountUpdates(True, ACCOUNT_ID)

if not app.download_complete.wait(timeout=20):
    print("Account update request timed out.")

app.reqAccountUpdates(False, ACCOUNT_ID)
time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
