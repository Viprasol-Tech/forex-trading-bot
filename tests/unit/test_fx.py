"""Tests for FX pip/lot math, sizing, strategy, and backtest."""

from __future__ import annotations

import math

import pytest

from forex_trading_bot.backtest import run_backtest
from forex_trading_bot.fx import (
    pip_size,
    pip_value_per_lot,
    pips_between,
    position_size_lots,
)
from forex_trading_bot.strategy import Signal, TrendStrategy


def test_pip_size_jpy_vs_normal() -> None:
    assert pip_size("USDJPY") == 0.01
    assert pip_size("EURUSD") == 0.0001


def test_pips_between() -> None:
    assert math.isclose(pips_between("EURUSD", 1.1050, 1.1000), 50.0)


def test_pip_value_per_lot() -> None:
    assert math.isclose(pip_value_per_lot("EURUSD"), 10.0)  # 0.0001 * 100,000


def test_position_size_risks_exact_amount() -> None:
    # Risk 1% of $10,000 = $100; SL 50 pips; pip value $10/lot -> $500 risk/lot.
    lots = position_size_lots(10_000, 1.0, 50, "EURUSD")
    assert math.isclose(lots, 0.2)  # $100 / $500 = 0.2 lots
    # Verify the round-trip: lots * SL pips * pip value == risk amount.
    assert math.isclose(lots * 50 * pip_value_per_lot("EURUSD"), 100.0)


def test_position_size_zero_on_bad_input() -> None:
    assert position_size_lots(10_000, 1.0, 0, "EURUSD") == 0.0


def test_strategy_validates_windows() -> None:
    with pytest.raises(ValueError):
        TrendStrategy(fast=30, slow=10)


def test_strategy_long_on_uptrend() -> None:
    closes = [1.0 + 0.01 * i for i in range(40)]
    assert TrendStrategy(5, 20).signal(closes) is Signal.LONG


def test_backtest_runs() -> None:
    closes = [1.10 + 0.0002 * i for i in range(120)]
    result = run_backtest(closes)
    assert len(result.equity_curve) == len(closes)
    assert isinstance(result.total_return_pct, float)
