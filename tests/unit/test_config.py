"""Tests for the pydantic configuration model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from forex_trading_bot.config import BacktestConfig, StopMode, StrategyKind


def test_defaults_are_valid() -> None:
    cfg = BacktestConfig()
    assert cfg.strategy is StrategyKind.TREND
    assert cfg.stop_mode is StopMode.FIXED
    assert cfg.pair_upper == "EURUSD"


def test_pair_upper_normalises() -> None:
    assert BacktestConfig(pair="eurusd").pair_upper == "EURUSD"


def test_rejects_negative_risk() -> None:
    with pytest.raises(ValidationError):
        BacktestConfig(risk_percent=-1.0)


def test_rejects_risk_over_100() -> None:
    with pytest.raises(ValidationError):
        BacktestConfig(risk_percent=150.0)


def test_trend_requires_fast_lt_slow() -> None:
    with pytest.raises(ValidationError):
        BacktestConfig(strategy=StrategyKind.TREND, fast=30, slow=10)


def test_breakout_ignores_trend_window_check() -> None:
    # fast >= slow is irrelevant for non-trend strategies.
    cfg = BacktestConfig(strategy=StrategyKind.BREAKOUT, fast=30, slow=10)
    assert cfg.strategy is StrategyKind.BREAKOUT


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        BacktestConfig(bogus=1)  # type: ignore[call-arg]


def test_frozen_is_immutable() -> None:
    cfg = BacktestConfig()
    with pytest.raises(ValidationError):
        cfg.risk_percent = 2.0  # type: ignore[misc]
