from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.services.brokers.ibkr_historical import (
    IBKRHistoricalClient,
    IBKRRequestError,
)


def test_parse_timestamp_with_us_eastern_timezone() -> None:
    result = IBKRHistoricalClient._parse_timestamp(
        "20260731 09:30:00 US/Eastern"
    )

    assert result == datetime(
        2026,
        7,
        31,
        9,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )


def test_parse_timestamp_without_timezone() -> None:
    result = IBKRHistoricalClient._parse_timestamp(
        "20260731 09:30:00"
    )

    assert result == datetime(
        2026,
        7,
        31,
        9,
        30,
    )


def test_parse_daily_timestamp() -> None:
    result = IBKRHistoricalClient._parse_timestamp("20260731")

    assert result == datetime(
        2026,
        7,
        31,
    )


def test_parse_timestamp_rejects_unknown_format() -> None:
    with pytest.raises(
        IBKRRequestError,
        match="Unsupported IBKR historical timestamp",
    ):
        IBKRHistoricalClient._parse_timestamp(
            "07/31/2026 09:30"
        )


def test_ibkr_historical_bar_values_remain_decimal() -> None:
    from app.services.brokers.ibkr_historical import IBKRHistoricalBar

    bar = IBKRHistoricalBar(
        timestamp=datetime(
            2026,
            7,
            31,
            9,
            30,
            tzinfo=ZoneInfo("America/New_York"),
        ),
        open=Decimal("304.70"),
        high=Decimal("306.90"),
        low=Decimal("300.55"),
        close=Decimal("302.11"),
        volume=7_758_542,
    )

    assert bar.open == Decimal("304.70")
    assert bar.high == Decimal("306.90")
    assert bar.low == Decimal("300.55")
    assert bar.close == Decimal("302.11")
    assert bar.volume == 7_758_542
