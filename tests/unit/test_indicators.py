"""Tests for technical indicators."""

from __future__ import annotations

import math

import pytest

from forex_trading_bot.indicators import (
    Bar,
    atr,
    bars_from_closes,
    correlation,
    ema,
    sma,
    stdev,
    true_range,
)


def test_sma_basic() -> None:
    assert math.isclose(sma([1, 2, 3, 4], 2), 3.5)


def test_sma_short_input_uses_available() -> None:
    assert math.isclose(sma([5.0], 10), 5.0)


def test_sma_rejects_nonpositive_window() -> None:
    with pytest.raises(ValueError):
        sma([1, 2, 3], 0)


def test_ema_between_min_and_max() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = ema(values, 3)
    assert min(values) < result < max(values)


def test_stdev_zero_for_flat_series() -> None:
    assert stdev([2.0, 2.0, 2.0, 2.0], 4) == 0.0


def test_true_range_first_bar_is_hl() -> None:
    bar = Bar(high=1.2, low=1.0, close=1.1)
    assert math.isclose(true_range(bar, None), 0.2)


def test_true_range_uses_prev_close_gap() -> None:
    bar = Bar(high=1.05, low=1.02, close=1.04)
    # Gap up: prev close 1.00, so |high - prev| = 0.05 dominates.
    assert math.isclose(true_range(bar, 1.00), 0.05)


def test_bar_rejects_inverted_range() -> None:
    with pytest.raises(ValueError):
        Bar(high=1.0, low=1.5, close=1.2)


def test_atr_positive_for_volatile_bars() -> None:
    bars = [Bar(high=1.0 + 0.01 * i, low=0.99 + 0.01 * i, close=1.0 + 0.01 * i) for i in range(20)]
    assert atr(bars, 14) > 0.0


def test_atr_insufficient_data() -> None:
    assert atr([Bar(1.0, 0.9, 0.95)], 14) == 0.0


def test_bars_from_closes_length_and_validity() -> None:
    bars = bars_from_closes([1.0, 1.1, 1.05, 1.2], spread_frac=0.5)
    assert len(bars) == 4
    assert all(b.high >= b.low for b in bars)


def test_correlation_perfectly_correlated() -> None:
    # Varying returns moving in lockstep -> correlation 1.
    a = [1.0, 1.1, 1.05, 1.2, 1.15, 1.3]
    b = [2.0, 2.2, 2.1, 2.4, 2.3, 2.6]  # exactly 2x the moves of a
    assert math.isclose(correlation(a, b, 5), 1.0, abs_tol=1e-9)


def test_correlation_anti_correlated() -> None:
    a = [1.0, 1.1, 1.05, 1.2, 1.15, 1.3]
    b = [2.0, 1.8, 1.9, 1.6, 1.7, 1.4]  # mirror image of a's moves
    assert math.isclose(correlation(a, b, 5), -1.0, abs_tol=1e-9)


def test_correlation_flat_series_zero() -> None:
    a = [1.0, 1.0, 1.0, 1.0, 1.0]
    b = [2.0, 3.0, 4.0, 5.0, 6.0]
    assert correlation(a, b, 4) == 0.0


def test_correlation_rejects_small_window() -> None:
    with pytest.raises(ValueError):
        correlation([1, 2, 3], [1, 2, 3], 1)
