"""Risk management: ATR-based stops and trailing stops.

The backtester opens risk-sized positions; this module decides *where* the stop
goes and trails it as the trade moves in your favour. Stops are expressed in
pips so they plug straight into :func:`forex_trading_bot.fx.position_size_lots`.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from forex_trading_bot.fx import pip_size
from forex_trading_bot.indicators import Bar, atr


def atr_stop_pips(
    bars: Sequence[Bar],
    pair: str,
    multiplier: float = 2.0,
    window: int = 14,
    floor_pips: float = 5.0,
) -> float:
    """Stop distance in pips, sized to ``multiplier`` x ATR.

    Volatility-scaled stops give wide markets room to breathe and tighten in
    quiet ones. Never returns less than ``floor_pips`` so a flat patch of data
    can't produce a zero stop (which would make sizing blow up).
    """
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    atr_price = atr(bars, window)
    stop_pips = (atr_price / pip_size(pair)) * multiplier
    return max(stop_pips, floor_pips)


@dataclass(slots=True)
class TrailingStop:
    """A long-only trailing stop tracked in price terms.

    Initialise with the entry price and a trail distance in pips. Feed each new
    price to :meth:`update`; the stop ratchets up as price rises and never
    moves down. :meth:`is_hit` reports whether a price has breached the stop.

    Example:
        >>> ts = TrailingStop.from_pips("EURUSD", entry=1.1000, trail_pips=20)
        >>> ts.update(1.1050)            # price rises
        >>> round(ts.stop_price, 4)
        1.103
        >>> ts.is_hit(1.1025)
        False
        >>> ts.is_hit(1.1029)
        True
    """

    pair: str
    trail_distance: float  # in price units, not pips
    stop_price: float

    @classmethod
    def from_pips(cls, pair: str, entry: float, trail_pips: float) -> TrailingStop:
        """Build a trailing stop ``trail_pips`` below ``entry``."""
        if trail_pips <= 0:
            raise ValueError("trail_pips must be positive")
        distance = trail_pips * pip_size(pair)
        return cls(pair=pair, trail_distance=distance, stop_price=entry - distance)

    def update(self, price: float) -> float:
        """Ratchet the stop up to ``price - trail_distance`` if that is higher."""
        candidate = price - self.trail_distance
        if candidate > self.stop_price:
            self.stop_price = candidate
        return self.stop_price

    def is_hit(self, price: float) -> bool:
        """True when ``price`` has fallen to or below the current stop."""
        return price <= self.stop_price
