import threading
import time

from ibapi.client import EClient
from ibapi.wrapper import EWrapper


class IBKRAccountSummaryApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.summary_done = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def managedAccounts(self, accountsList: str) -> None:
        print(f"Managed accounts: {accountsList}")

    def accountSummary(
        self,
        reqId: int,
        account: str,
        tag: str,
        value: str,
        currency: str,
    ) -> None:
        print(
            f"Account={account} | Tag={tag} | "
            f"Value={value} | Currency={currency}"
        )

    def accountSummaryEnd(self, reqId: int) -> None:
        print(f"Account summary complete. reqId={reqId}")
        self.summary_done.set()

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


app = IBKRAccountSummaryApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=46)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

tags = ",".join(
    [
        "AccountType",
        "NetLiquidation",
        "TotalCashValue",
        "BuyingPower",
        "AvailableFunds",
        "ExcessLiquidity",
        "GrossPositionValue",
        "MaintMarginReq",
        "InitMarginReq",
        "Cushion",
    ]
)

print("Requesting account summary...")
app.reqAccountSummary(
    reqId=9201,
    groupName="All",
    tags=tags,
)

if not app.summary_done.wait(timeout=20):
    print("Account summary request timed out.")

app.cancelAccountSummary(9201)
time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
