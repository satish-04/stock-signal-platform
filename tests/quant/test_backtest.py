import math

import pytest

from app.services.quant.backtest import (
    PriceHistory,
    metrics,
    positions,
    rsi,
    run_backtest,
    strategy_returns,
)


def series(bars: int, drift: float = 0.0005, wobble: float = 0.02) -> list[float]:
    return [100 * (1 + drift) ** i * (1 + wobble * math.sin(i / 7)) for i in range(bars)]


def history(bars: int = 1300) -> PriceHistory:
    return PriceHistory("TEST", [f"d{i:04d}" for i in range(bars)], series(bars))


@pytest.mark.parametrize(
    "strategy, params",
    [("ema_cross", {"fast": 10, "slow": 50}), ("rsi_reversion", {"period": 14, "entry": 35, "exit": 60})],
)
def test_positions_never_depend_on_later_prices(strategy, params):
    closes = series(400)
    full = positions(strategy, closes, params)
    for cut in (120, 250, 399):
        assert positions(strategy, closes[:cut], params) == full[:cut]


def test_a_position_earns_the_next_days_return_and_pays_cost_on_entry():
    returns = strategy_returns([100, 100, 110, 99], [0, 1, 1, 0], cost_bps=10)
    assert returns == pytest.approx([0.0, 0.10 - 0.001, -0.10])


def test_metrics_for_a_known_return_series():
    result = metrics([0.10, -0.10], [1, 1, 0])
    assert result["total_return_pct"] == -1.0
    assert result["max_drawdown_pct"] == -10.0
    assert result["trades"] == 1
    assert result["win_rate_pct"] == 0.0
    assert result["exposure_pct"] == 100.0


def test_trades_and_win_rate_count_completed_round_trips():
    # Two trades: +5% then -2%.
    result = metrics([0.05, 0.0, -0.02, 0.0], [1, 0, 1, 0, 0])
    assert result["trades"] == 2
    assert result["win_rate_pct"] == 50.0


def test_metrics_of_a_flat_strategy_are_zero_not_errors():
    result = metrics([0.0, 0.0, 0.0], [0, 0, 0, 0])
    assert result["sharpe"] == 0.0
    assert result["win_rate_pct"] is None


def test_rsi_is_undefined_during_warmup_and_bounded_after():
    values = rsi(series(60), 14)
    assert values[:14] == [None] * 14
    assert all(0 <= value <= 100 for value in values[14:])
    assert rsi([1, 2, 3, 4, 5, 6], 3)[-1] == 100.0


@pytest.mark.parametrize("strategy, combinations", [("ema_cross", 16), ("rsi_reversion", 27)])
def test_sweep_covers_the_whole_grid_and_ranks_by_sharpe(strategy, combinations):
    result = run_backtest(history(), strategy)
    assert result["combinations"] == combinations
    sharpes = [run["sharpe"] for run in result["top"]]
    assert sharpes == sorted(sharpes, reverse=True)
    assert result["best"] == result["top"][0]
    assert result["equity_curve"][-1]["date"] == "d1299"


def test_benchmark_is_buy_and_hold_without_costs():
    result = run_backtest(history(), "ema_cross")
    closes = series(1300)
    assert result["benchmark"]["total_return_pct"] == pytest.approx((closes[-1] / closes[0] - 1) * 100, abs=0.01)
    assert result["benchmark"]["exposure_pct"] == 100.0


def test_walk_forward_trades_only_parameters_chosen_on_earlier_data():
    result = run_backtest(history(), "ema_cross", train_days=504, test_days=126)
    walk = result["walk_forward"]
    # 1299 daily returns, 504 to train, then 126-day test windows.
    assert len(walk["windows"]) == (1299 - 504 - 126) // 126 + 1
    for window in walk["windows"]:
        assert window["train_start"] < window["test_start"] < window["test_end"]
    starts = [window["test_start"] for window in walk["windows"]]
    assert starts == sorted(set(starts))
    assert "sharpe" in walk["out_of_sample"]


def test_walk_forward_is_skipped_when_history_is_too_short():
    assert run_backtest(history(400), "ema_cross")["walk_forward"] is None


def test_costs_reduce_returns():
    free = run_backtest(history(), "rsi_reversion", cost_bps=0)
    costly = run_backtest(history(), "rsi_reversion", cost_bps=50)
    assert costly["top"][0]["total_return_pct"] < free["top"][0]["total_return_pct"]
