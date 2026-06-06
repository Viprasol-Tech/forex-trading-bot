"""Tests for the multi-pair correlation portfolio."""

from __future__ import annotations

import math

import pytest

from forex_trading_bot.data import synthetic_pairs
from forex_trading_bot.portfolio import CorrelationPortfolio, run_portfolio_backtest
from forex_trading_bot.strategy import Signal, Strategy


class AlwaysLong:
    """Test double that always signals LONG."""

    def signal(self, closes: object) -> Signal:
        return Signal.LONG


def test_always_long_satisfies_protocol() -> None:
    assert isinstance(AlwaysLong(), Strategy)


def _wavy(offset: float = 0.0, scale: float = 1.0, n: int = 60) -> list[float]:
    """A series with genuinely varying bar-to-bar returns."""
    return [1.0 + offset + scale * math.sin((i + offset) / 3.0) + 0.005 * i for i in range(n)]


def test_correlation_filter_rejects_correlated_pair() -> None:
    base = _wavy(scale=0.02)
    corr = [v * 2.0 for v in base]  # identical return shape -> correlation 1
    pf = CorrelationPortfolio(strategy=AlwaysLong(), max_correlation=0.8, corr_window=30)
    result = pf.evaluate({"AAAUSD": base, "BBBUSD": corr})
    # Only one of the two correlated pairs is held.
    assert len(result.held) == 1


def test_uncorrelated_pairs_both_held() -> None:
    up = _wavy(scale=0.02)
    zig = [1.0 + (0.01 if i % 2 else -0.01) for i in range(60)]
    pf = CorrelationPortfolio(strategy=AlwaysLong(), max_correlation=0.9, corr_window=30)
    result = pf.evaluate({"AAAUSD": up, "BBBUSD": zig})
    assert set(result.held) == {"AAAUSD", "BBBUSD"}


def test_max_positions_cap() -> None:
    # Five pairs with distinct phase offsets so none are highly correlated.
    pairs = {f"P{i}USD": _wavy(offset=float(i * 7), scale=0.02) for i in range(5)}
    pf = CorrelationPortfolio(strategy=AlwaysLong(), max_correlation=0.99, max_positions=2)
    result = pf.evaluate(pairs)
    assert len(result.held) == 2


def test_no_signal_not_held() -> None:
    class NeverLong:
        def signal(self, closes: object) -> Signal:
            return Signal.FLAT

    pf = CorrelationPortfolio(strategy=NeverLong())
    result = pf.evaluate({"AAAUSD": [1.0] * 40})
    assert result.held == []


def test_rejects_bad_correlation_threshold() -> None:
    with pytest.raises(ValueError):
        CorrelationPortfolio(max_correlation=2.0)


def test_rejects_bad_max_positions() -> None:
    with pytest.raises(ValueError):
        CorrelationPortfolio(max_positions=0)


def test_run_portfolio_backtest_aggregates() -> None:
    prices = synthetic_pairs(200)
    out = run_portfolio_backtest(prices)
    assert isinstance(out.aggregate_return_pct, float)
    assert isinstance(out.held, list)
    assert isinstance(out.per_pair, dict)
    # Every held pair has a backtest result.
    assert set(out.per_pair) == set(out.held)
