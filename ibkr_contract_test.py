import threading
import time

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


class IBKRContractApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.connected_event = threading.Event()
        self.contract_done = threading.Event()

    def nextValidId(self, orderId: int) -> None:
        print(f"Connected. nextValidId={orderId}")
        self.connected_event.set()

    def contractDetails(self, reqId, details) -> None:
        contract = details.contract
        print(
            "Contract found: "
            f"conId={contract.conId}, "
            f"symbol={contract.symbol}, "
            f"localSymbol={contract.localSymbol}, "
            f"secType={contract.secType}, "
            f"exchange={contract.exchange}, "
            f"primaryExchange={contract.primaryExchange}, "
            f"currency={contract.currency}, "
            f"marketName={details.marketName}, "
            f"minTick={details.minTick}"
        )

    def contractDetailsEnd(self, reqId: int) -> None:
        print(f"Contract qualification complete. reqId={reqId}")
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


app = IBKRContractApp()

print("Connecting to TWS paper API...")
app.connect("127.0.0.1", 7497, clientId=49)

thread = threading.Thread(target=app.run, daemon=True)
thread.start()

if not app.connected_event.wait(timeout=10):
    print("Connection timed out.")
    app.disconnect()
    raise SystemExit(1)

time.sleep(2)

contract = Contract()
contract.symbol = "AAPL"
contract.secType = "STK"
contract.exchange = "SMART"
contract.currency = "USD"

print("Qualifying AAPL contract...")
app.reqContractDetails(9501, contract)

if not app.contract_done.wait(timeout=20):
    print("Contract request timed out.")

time.sleep(1)
app.disconnect()
print("Disconnected cleanly.")
