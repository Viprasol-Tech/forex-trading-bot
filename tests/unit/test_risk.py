"""Tests for ATR stops and trailing stops."""

from __future__ import annotations

import math

import pytest

from forex_trading_bot.indicators import Bar
from forex_trading_bot.risk import TrailingStop, atr_stop_pips


def _vol_bars(n: int = 20) -> list[Bar]:
    return [
        Bar(high=1.005 + 0.001 * i, low=0.995 + 0.001 * i, close=1.0 + 0.001 * i) for i in range(n)
    ]


def test_atr_stop_scales_with_multiplier() -> None:
    bars = _vol_bars()
    one_x = atr_stop_pips(bars, "EURUSD", multiplier=1.0)
    two_x = atr_stop_pips(bars, "EURUSD", multiplier=2.0)
    assert math.isclose(two_x, one_x * 2.0, rel_tol=1e-9)


def test_atr_stop_respects_floor() -> None:
    flat = [Bar(1.0, 1.0, 1.0) for _ in range(20)]
    assert atr_stop_pips(flat, "EURUSD", floor_pips=5.0) == 5.0


def test_atr_stop_rejects_bad_multiplier() -> None:
    with pytest.raises(ValueError):
        atr_stop_pips(_vol_bars(), "EURUSD", multiplier=0.0)


def test_trailing_stop_starts_below_entry() -> None:
    ts = TrailingStop.from_pips("EURUSD", entry=1.1000, trail_pips=20)
    assert math.isclose(ts.stop_price, 1.1000 - 0.0020, abs_tol=1e-9)


def test_trailing_stop_ratchets_up_only() -> None:
    ts = TrailingStop.from_pips("EURUSD", entry=1.1000, trail_pips=20)
    ts.update(1.1050)
    high_stop = ts.stop_price
    assert math.isclose(high_stop, 1.1030, abs_tol=1e-9)
    ts.update(1.1010)  # price falls back; stop must not drop
    assert ts.stop_price == high_stop


def test_trailing_stop_hit_detection() -> None:
    ts = TrailingStop.from_pips("EURUSD", entry=1.1000, trail_pips=20)
    ts.update(1.1050)  # stop now at 1.1030
    assert ts.is_hit(1.1029) is True
    assert ts.is_hit(1.1031) is False


def test_trailing_stop_rejects_nonpositive_pips() -> None:
    with pytest.raises(ValueError):
        TrailingStop.from_pips("EURUSD", entry=1.1, trail_pips=0)
