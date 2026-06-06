"""Trading strategies for FX.

Every strategy implements a single method, ``signal(closes) -> Signal``, so the
backtester and portfolio can treat them interchangeably:

- :class:`TrendStrategy`   — fast/slow SMA trend follower (the classic).
- :class:`BreakoutStrategy` — Donchian-channel breakout (long above the
  N-bar high, flat below the N-bar low) — momentum capture.
- :class:`CarryStrategy`    — goes long when the pair's interest-rate
  differential (carry) is positive and the price is trending up, modelling the
  most-traded real-money FX style.

Entries are designed to be sized by the risk module and protected by pip- or
ATR-based stops handled in the backtester.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from forex_trading_bot.indicators import sma


class Signal(str, Enum):
    """Strategy decision."""

    LONG = "long"
    FLAT = "flat"


@runtime_checkable
class Strategy(Protocol):
    """Anything that turns a close series into a :class:`Signal`."""

    def signal(self, closes: Sequence[float]) -> Signal: ...


@dataclass(slots=True)
class TrendStrategy:
    """Fast/slow SMA trend follower: LONG when fast SMA > slow SMA."""

    fast: int = 10
    slow: int = 30

    def __post_init__(self) -> None:
        if self.fast >= self.slow:
            raise ValueError("fast must be shorter than slow")

    def signal(self, closes: Sequence[float]) -> Signal:
        """Return LONG when fast SMA > slow SMA, else FLAT."""
        if len(closes) < self.slow:
            return Signal.FLAT
        if sma(closes, self.fast) > sma(closes, self.slow):
            return Signal.LONG
        return Signal.FLAT


@dataclass(slots=True)
class BreakoutStrategy:
    """Donchian-channel breakout.

    Goes LONG when the latest close makes a new ``lookback``-bar high and stays
    long until it makes a new ``lookback``-bar low, at which point it goes FLAT.
    The channel is measured over the bars *prior* to the current one so the
    signal reacts to genuine breakouts rather than to itself.
    """

    lookback: int = 20

    def __post_init__(self) -> None:
        if self.lookback < 2:
            raise ValueError("lookback must be >= 2")

    def signal(self, closes: Sequence[float]) -> Signal:
        if len(closes) <= self.lookback:
            return Signal.FLAT
        window = closes[-(self.lookback + 1) : -1]
        last = closes[-1]
        if last >= max(window):
            return Signal.LONG
        if last <= min(window):
            return Signal.FLAT
        return Signal.FLAT


@dataclass(slots=True)
class CarryStrategy:
    """Interest-rate carry overlay with a trend confirmation.

    Real-money FX flows chase positive carry: holding the higher-yielding
    currency against the lower-yielding one. This strategy goes LONG only when
    the supplied annual rate differential is positive *and* a short trend filter
    confirms the price isn't falling, avoiding the classic "picking up pennies
    in front of a steamroller" carry blow-up.

    Args:
        rate_differential: Annual carry of the long leg minus the short leg,
            in percentage points (e.g. 3.5 means +3.5%/yr).
        trend_window: SMA window used as the trend confirmation filter.
    """

    rate_differential: float = 0.0
    trend_window: int = 20

    def __post_init__(self) -> None:
        if self.trend_window < 2:
            raise ValueError("trend_window must be >= 2")

    def signal(self, closes: Sequence[float]) -> Signal:
        if self.rate_differential <= 0.0:
            return Signal.FLAT
        if len(closes) < self.trend_window:
            return Signal.FLAT
        if closes[-1] >= sma(closes, self.trend_window):
            return Signal.LONG
        return Signal.FLAT
