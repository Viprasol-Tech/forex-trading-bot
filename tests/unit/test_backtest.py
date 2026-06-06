"""Tests for the backtest engine and metrics."""

from __future__ import annotations

from forex_trading_bot.backtest import BacktestResult, Trade, run_backtest, run_backtest_config
from forex_trading_bot.config import BacktestConfig, StopMode, StrategyKind
from forex_trading_bot.data import synthetic_closes


def test_legacy_run_backtest_compatible() -> None:
    closes = [1.10 + 0.0002 * i for i in range(120)]
    result = run_backtest(closes)
    assert len(result.equity_curve) == len(closes)
    assert isinstance(result.total_return_pct, float)


def test_uptrend_makes_money() -> None:
    # A steady uptrend keeps the position open; mark-to-market equity rises.
    closes = [1.1000 + 0.0005 * i for i in range(200)]
    cfg = BacktestConfig(strategy=StrategyKind.TREND)
    result = run_backtest_config(closes, cfg)
    assert result.final_balance > result.starting_balance


def test_round_trip_records_trade() -> None:
    # Up then down forces an entry and a signal exit -> at least one closed trade.
    closes = [1.1000 + 0.0010 * i for i in range(40)] + [1.1400 - 0.0010 * i for i in range(40)]
    cfg = BacktestConfig(strategy=StrategyKind.TREND, fast=3, slow=10)
    result = run_backtest_config(closes, cfg)
    assert result.num_trades >= 1
    assert any(t.reason == "signal" for t in result.trades)


def test_atr_stop_mode_runs() -> None:
    closes = synthetic_closes(200)
    cfg = BacktestConfig(stop_mode=StopMode.ATR, atr_multiplier=2.0)
    result = run_backtest_config(closes, cfg)
    assert len(result.equity_curve) == len(closes)


def test_trailing_stop_produces_stop_exits() -> None:
    # Rise then sharp fall should trigger a trailing-stop exit.
    closes = [1.1000 + 0.0010 * i for i in range(50)] + [1.1000 for _ in range(20)]
    cfg = BacktestConfig(strategy=StrategyKind.TREND, fast=3, slow=10, trail_pips=15.0)
    result = run_backtest_config(closes, cfg)
    assert any(t.reason == "stop" for t in result.trades)


def test_breakout_strategy_backtest() -> None:
    closes = synthetic_closes(250)
    cfg = BacktestConfig(strategy=StrategyKind.BREAKOUT, lookback=20)
    result = run_backtest_config(closes, cfg)
    assert isinstance(result.total_pips, float)


def test_metrics_on_known_trades() -> None:
    res = BacktestResult(starting_balance=1000.0, final_balance=1100.0, pair="EURUSD")
    res.trades = [
        Trade(1.0, 1.1, 0.1, 100.0, 60.0, "signal"),
        Trade(1.1, 1.05, 0.1, -50.0, -20.0, "stop"),
        Trade(1.05, 1.2, 0.1, 150.0, 40.0, "signal"),
    ]
    res.equity_curve = [1000.0, 1060.0, 1040.0, 1100.0]
    assert res.num_trades == 3
    assert res.wins == 2
    assert abs(res.win_rate - 2 / 3) < 1e-9
    # PF = (60+40) / 20 = 5.0
    assert abs(res.profit_factor - 5.0) < 1e-9
    assert res.max_drawdown_pct > 0.0


def test_profit_factor_infinite_without_losses() -> None:
    res = BacktestResult(starting_balance=1000.0, final_balance=1100.0)
    res.trades = [Trade(1.0, 1.1, 0.1, 100.0, 50.0, "signal")]
    assert res.profit_factor == float("inf")


def test_total_return_zero_on_zero_start() -> None:
    res = BacktestResult(starting_balance=0.0, final_balance=0.0)
    assert res.total_return_pct == 0.0
