"""A simple moving-average trend strategy for FX.

Goes long when the fast SMA crosses above the slow SMA and flat when it crosses
back below. Entries carry a pip-based stop-loss and take-profit, sized by the
risk module — the structure most retail FX bots use.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class Signal(str, Enum):
    """Strategy decision."""

    LONG = "long"
    FLAT = "flat"


@dataclass(slots=True)
class TrendStrategy:
    """Fast/slow SMA trend follower."""

    fast: int = 10
    slow: int = 30

    def __post_init__(self) -> None:
        if self.fast >= self.slow:
            raise ValueError("fast must be shorter than slow")

    def signal(self, closes: Sequence[float]) -> Signal:
        """Return LONG when fast SMA > slow SMA, else FLAT."""
        if len(closes) < self.slow:
            return Signal.FLAT
        fast = sum(closes[-self.fast :]) / self.fast
        slow = sum(closes[-self.slow :]) / self.slow
        return Signal.LONG if fast > slow else Signal.FLAT
