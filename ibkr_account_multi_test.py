import threading
import time

from ibapi.client import EClient
from ibapi.message import OUT
from ibapi.wrapper import EWrapper


ACCOUNT_ID = "DUR500987"


class IBKRAccountMultiApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.account_done = threading.Event()

    def useProtoBuf(self, msgId: int) -> bool:
        if msgId == OUT.REQ_ACCOUNT_UPDATES_MULTI:
            return False
        return super().useProtoBuf(msgId)

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def managedAccounts(self, accountsList: str) -> None:
        print(f"Managed accounts: {accountsList}")

    def accountUpdateMulti(
        self,
        reqId: int,
        account: str,
        modelCode: str,
        key: str,
        value: str,
        currency: str,
    ) -> None:
        allowed_keys = {
            "AccountType",
            "NetLiquidation",
            "TotalCashValue",
            "BuyingPower",
            "AvailableFunds",
            "ExcessLiquidity",
            "GrossPositionValue",
            "MaintMarginReq",
            "InitMarginReq",
        }

        if key in allowed_keys:
            print(
                f"Account={account} | Key={key} | "
                f"Value={value} | Currency={currency}"
            )

    def accountUpdateMultiEnd(self, reqId: int) -> None:
        print(f"Account multi-update complete. reqId={reqId}")
        self.account_done.set()

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


app = IBKRAccountMultiApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=45)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

print(f"Requesting account data for {ACCOUNT_ID}...")
app.reqAccountUpdatesMulti(
    reqId=9101,
    account=ACCOUNT_ID,
    modelCode="",
    ledgerAndNLV=True,
)

if not app.account_done.wait(timeout=20):
    print("Account multi-update request timed out.")

app.cancelAccountUpdatesMulti(9101)
time.sleep(1)
app.disconnect()

print("Disconnected cleanly.")
