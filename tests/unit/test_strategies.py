"""Tests for the trend, breakout, and carry strategies."""

from __future__ import annotations

import pytest

from forex_trading_bot.strategy import (
    BreakoutStrategy,
    CarryStrategy,
    Signal,
    Strategy,
    TrendStrategy,
)


def test_strategies_satisfy_protocol() -> None:
    for strat in (TrendStrategy(), BreakoutStrategy(), CarryStrategy()):
        assert isinstance(strat, Strategy)


def test_trend_flat_on_short_input() -> None:
    assert TrendStrategy(5, 20).signal([1.0] * 5) is Signal.FLAT


def test_trend_long_on_uptrend() -> None:
    closes = [1.0 + 0.01 * i for i in range(40)]
    assert TrendStrategy(5, 20).signal(closes) is Signal.LONG


def test_trend_flat_on_downtrend() -> None:
    closes = [2.0 - 0.01 * i for i in range(40)]
    assert TrendStrategy(5, 20).signal(closes) is Signal.FLAT


def test_breakout_long_on_new_high() -> None:
    closes = [1.0] * 20 + [1.5]  # breaks above the channel
    assert BreakoutStrategy(20).signal(closes) is Signal.LONG


def test_breakout_flat_on_new_low() -> None:
    closes = [1.0] * 20 + [0.5]
    assert BreakoutStrategy(20).signal(closes) is Signal.FLAT


def test_breakout_flat_inside_channel() -> None:
    closes = [1.0 + 0.001 * (i % 3) for i in range(25)]
    assert BreakoutStrategy(20).signal(closes) is Signal.FLAT


def test_breakout_rejects_tiny_lookback() -> None:
    with pytest.raises(ValueError):
        BreakoutStrategy(1)


def test_carry_flat_when_differential_nonpositive() -> None:
    closes = [1.0 + 0.01 * i for i in range(40)]
    assert CarryStrategy(rate_differential=0.0).signal(closes) is Signal.FLAT
    assert CarryStrategy(rate_differential=-1.0).signal(closes) is Signal.FLAT


def test_carry_long_on_positive_carry_and_uptrend() -> None:
    closes = [1.0 + 0.01 * i for i in range(40)]
    assert CarryStrategy(rate_differential=3.0, trend_window=20).signal(closes) is Signal.LONG


def test_carry_flat_on_positive_carry_but_downtrend() -> None:
    closes = [2.0 - 0.01 * i for i in range(40)]
    assert CarryStrategy(rate_differential=3.0, trend_window=20).signal(closes) is Signal.FLAT


def test_trend_validates_windows() -> None:
    with pytest.raises(ValueError):
        TrendStrategy(fast=30, slow=10)
