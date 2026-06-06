"""Technical indicators for FX strategies.

Pure-Python, dependency-light implementations of the building blocks the
strategies and risk layer need: simple/exponential moving averages, the
Average True Range (ATR) used for volatility-scaled stops, rolling standard
deviation, and a rolling Pearson correlation used by the portfolio's
correlation filter.

All functions take plain sequences of floats and return plain floats or lists
so they compose cleanly with the rest of the toolkit.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


def sma(values: Sequence[float], window: int) -> float:
    """Simple moving average of the last ``window`` values.

    Returns the mean of whatever is available when fewer than ``window``
    samples exist (never raises on short input).
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        return 0.0
    sample = values[-window:]
    return sum(sample) / len(sample)


def ema(values: Sequence[float], window: int) -> float:
    """Exponential moving average with the standard 2/(n+1) smoothing factor."""
    if window <= 0:
        raise ValueError("window must be positive")
    if not values:
        return 0.0
    alpha = 2.0 / (window + 1.0)
    result = values[0]
    for value in values[1:]:
        result = alpha * value + (1.0 - alpha) * result
    return result


def stdev(values: Sequence[float], window: int) -> float:
    """Population standard deviation of the last ``window`` values."""
    if window <= 0:
        raise ValueError("window must be positive")
    sample = values[-window:]
    if len(sample) < 2:
        return 0.0
    mean = sum(sample) / len(sample)
    var = sum((v - mean) ** 2 for v in sample) / len(sample)
    return math.sqrt(var)


@dataclass(slots=True, frozen=True)
class Bar:
    """A single OHLC price bar."""

    high: float
    low: float
    close: float

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError("high must be >= low")


def true_range(bar: Bar, prev_close: float | None) -> float:
    """True Range for one bar given the previous close.

    TR = max(high-low, |high-prev_close|, |low-prev_close|).
    """
    hl = bar.high - bar.low
    if prev_close is None:
        return hl
    return max(hl, abs(bar.high - prev_close), abs(bar.low - prev_close))


def atr(bars: Sequence[Bar], window: int = 14) -> float:
    """Average True Range over the last ``window`` bars (Wilder-style mean).

    Returns 0.0 when there is not enough data to form a single true range.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    if len(bars) < 2:
        return 0.0
    trs: list[float] = []
    prev_close: float | None = None
    for bar in bars:
        trs.append(true_range(bar, prev_close))
        prev_close = bar.close
    sample = trs[-window:]
    return sum(sample) / len(sample)


def bars_from_closes(closes: Sequence[float], spread_frac: float = 0.0) -> list[Bar]:
    """Synthesize OHLC bars from a close-only series.

    ``spread_frac`` widens each bar's high/low around the close by a fraction of
    the bar-to-bar move, which is handy for demos and tests that only have a
    close series but still want a non-degenerate ATR.
    """
    bars: list[Bar] = []
    prev = closes[0] if closes else 0.0
    for close in closes:
        move = abs(close - prev)
        pad = move * spread_frac
        high = max(close, prev) + pad
        low = min(close, prev) - pad
        bars.append(Bar(high=high, low=low, close=close))
        prev = close
    return bars


def correlation(series_a: Sequence[float], series_b: Sequence[float], window: int) -> float:
    """Rolling Pearson correlation of the last ``window`` returns.

    The inputs are price series; returns are computed internally as simple
    bar-to-bar differences. Returns 0.0 when variance is zero or data is short.
    """
    if window <= 1:
        raise ValueError("window must be > 1")
    n = min(len(series_a), len(series_b))
    if n < 2:
        return 0.0
    a = series_a[-(window + 1) :]
    b = series_b[-(window + 1) :]
    ra = [a[i] - a[i - 1] for i in range(1, len(a))]
    rb = [b[i] - b[i - 1] for i in range(1, len(b))]
    m = min(len(ra), len(rb))
    if m < 2:
        return 0.0
    ra, rb = ra[-m:], rb[-m:]
    mean_a = sum(ra) / m
    mean_b = sum(rb) / m
    cov = sum((ra[i] - mean_a) * (rb[i] - mean_b) for i in range(m))
    var_a = sum((x - mean_a) ** 2 for x in ra)
    var_b = sum((x - mean_b) ** 2 for x in rb)
    denom = math.sqrt(var_a * var_b)
    if denom == 0.0:
        return 0.0
    return cov / denom
