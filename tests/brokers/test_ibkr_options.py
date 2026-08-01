from decimal import Decimal

from app.services.brokers.ibkr_options import IBKROptionSnapshot


def test_option_snapshot_preserves_contract_identity() -> None:
    snapshot = IBKROptionSnapshot(
        conid=903730167,
        symbol="AAPL",
        expiry="20260803",
        strike=Decimal("250"),
        right="C",
        bid=Decimal("0"),
        ask=Decimal("0"),
        volume=0,
        open_interest=0,
        implied_volatility=0.0,
        delta=0.0,
        gamma=0.0,
        theta=0.0,
        vega=0.0,
    )

    assert snapshot.conid == 903730167
    assert snapshot.symbol == "AAPL"
    assert snapshot.expiry == "20260803"
    assert snapshot.strike == Decimal("250")
    assert snapshot.right == "C"


def test_option_snapshot_allows_zero_market_data_before_subscription() -> None:
    snapshot = IBKROptionSnapshot(
        conid=1,
        symbol="AAPL",
        expiry="20260803",
        strike=Decimal("300"),
        right="P",
        bid=Decimal("0"),
        ask=Decimal("0"),
        volume=0,
        open_interest=0,
        implied_volatility=0.0,
        delta=0.0,
        gamma=0.0,
        theta=0.0,
        vega=0.0,
    )

    assert snapshot.bid == Decimal("0")
    assert snapshot.ask == Decimal("0")
    assert snapshot.delta == 0.0
