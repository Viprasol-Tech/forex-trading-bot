"""Typed, validated configuration via pydantic.

A single :class:`BacktestConfig` captures every knob the engine exposes so runs
are reproducible and CLI flags map onto one validated object. Validation catches
nonsensical inputs (negative risk, fast >= slow, etc.) before a backtest starts.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class StrategyKind(str, Enum):
    """Which strategy to run."""

    TREND = "trend"
    BREAKOUT = "breakout"
    CARRY = "carry"


class StopMode(str, Enum):
    """How the stop distance is determined."""

    FIXED = "fixed"
    ATR = "atr"


class BacktestConfig(BaseModel):
    """Validated parameters for a single-pair backtest."""

    model_config = {"frozen": True, "extra": "forbid"}

    pair: str = Field(default="EURUSD", min_length=6, max_length=7)
    starting_balance: float = Field(default=10_000.0, gt=0)
    risk_percent: float = Field(default=1.0, gt=0, le=100)

    strategy: StrategyKind = StrategyKind.TREND
    fast: int = Field(default=10, ge=1)
    slow: int = Field(default=30, ge=2)
    lookback: int = Field(default=20, ge=2)
    rate_differential: float = 0.0
    trend_window: int = Field(default=20, ge=2)

    stop_mode: StopMode = StopMode.FIXED
    stop_loss_pips: float = Field(default=30.0, gt=0)
    atr_window: int = Field(default=14, ge=1)
    atr_multiplier: float = Field(default=2.0, gt=0)
    trail_pips: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_windows(self) -> BacktestConfig:
        if self.strategy is StrategyKind.TREND and self.fast >= self.slow:
            raise ValueError("fast must be shorter than slow")
        return self

    @property
    def pair_upper(self) -> str:
        """The pair symbol, normalised to upper case."""
        return self.pair.upper()
