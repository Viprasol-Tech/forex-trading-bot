"""Backtest FX strategies with risk-based sizing, ATR/trailing stops and pip PnL.

Each bar the strategy emits LONG/FLAT. Going long opens a risk-sized position;
PnL accrues in the quote currency from pip moves. Positions are closed when the
strategy goes flat *or* when a stop is breached. Stops can be fixed-pip,
ATR-scaled, or trailing. The result carries a rich set of metrics (return, max
drawdown, win rate, profit factor, Sharpe) and an equity curve.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

from forex_trading_bot.config import BacktestConfig, StopMode, StrategyKind
from forex_trading_bot.fx import pip_value_per_lot, pips_between, position_size_lots
from forex_trading_bot.indicators import bars_from_closes
from forex_trading_bot.risk import TrailingStop, atr_stop_pips
from forex_trading_bot.strategy import (
    BreakoutStrategy,
    CarryStrategy,
    Signal,
    Strategy,
    TrendStrategy,
)


@dataclass(slots=True)
class Trade:
    """A single closed round-trip trade."""

    entry_price: float
    exit_price: float
    lots: float
    pips: float
    pnl: float
    reason: str  # "signal" or "stop"


@dataclass(slots=True)
class BacktestResult:
    """Summary of an FX backtest with risk/return metrics."""

    starting_balance: float
    final_balance: float
    pair: str = "EURUSD"
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)

    @property
    def num_trades(self) -> int:
        return len(self.trades)

    @property
    def total_return_pct(self) -> float:
        if self.starting_balance == 0:
            return 0.0
        return (self.final_balance / self.starting_balance - 1.0) * 100.0

    @property
    def total_pips(self) -> float:
        return sum(t.pips for t in self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.pnl > 0)

    @property
    def win_rate(self) -> float:
        return self.wins / self.num_trades if self.trades else 0.0

    @property
    def profit_factor(self) -> float:
        """Gross profit / gross loss. ``inf`` when there are no losses."""
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = -sum(t.pnl for t in self.trades if t.pnl < 0)
        if gross_loss == 0:
            return math.inf if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @property
    def max_drawdown_pct(self) -> float:
        """Largest peak-to-trough drop on the equity curve, as a percentage."""
        peak = -math.inf
        max_dd = 0.0
        for equity in self.equity_curve:
            peak = max(peak, equity)
            if peak > 0:
                dd = (peak - equity) / peak
                max_dd = max(max_dd, dd)
        return max_dd * 100.0

    @property
    def sharpe(self) -> float:
        """Annualised-ish Sharpe of per-bar equity returns (rf=0)."""
        curve = self.equity_curve
        if len(curve) < 3:
            return 0.0
        rets = [curve[i] / curve[i - 1] - 1.0 for i in range(1, len(curve)) if curve[i - 1] != 0]
        if len(rets) < 2:
            return 0.0
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / len(rets)
        std = math.sqrt(var)
        if std == 0:
            return 0.0
        return (mean / std) * math.sqrt(252)


def _build_strategy(config: BacktestConfig) -> Strategy:
    if config.strategy is StrategyKind.TREND:
        return TrendStrategy(fast=config.fast, slow=config.slow)
    if config.strategy is StrategyKind.BREAKOUT:
        return BreakoutStrategy(lookback=config.lookback)
    return CarryStrategy(
        rate_differential=config.rate_differential, trend_window=config.trend_window
    )


def run_backtest_config(
    closes: Sequence[float],
    config: BacktestConfig,
    strategy: Strategy | None = None,
) -> BacktestResult:
    """Run a backtest described by a :class:`BacktestConfig`."""
    strat = strategy or _build_strategy(config)
    pair = config.pair_upper
    balance = config.starting_balance
    result = BacktestResult(
        starting_balance=config.starting_balance,
        final_balance=config.starting_balance,
        pair=pair,
    )

    bars = bars_from_closes(closes, spread_frac=0.25)
    lots = 0.0
    entry_price = 0.0
    trail: TrailingStop | None = None

    def _close(exit_price: float, reason: str) -> None:
        nonlocal balance, lots, trail
        direction = 1 if exit_price >= entry_price else -1
        pips = pips_between(pair, exit_price, entry_price) * direction
        pnl = pips * pip_value_per_lot(pair) * lots
        balance += pnl
        result.trades.append(
            Trade(
                entry_price=entry_price,
                exit_price=exit_price,
                lots=lots,
                pips=pips,
                pnl=pnl,
                reason=reason,
            )
        )
        lots = 0.0
        trail = None

    for i, price in enumerate(closes):
        signal = strat.signal(closes[: i + 1])

        # Manage an open position first: trailing stop, then signal exit.
        if lots > 0.0:
            if trail is not None:
                trail.update(price)
                if trail.is_hit(price):
                    _close(price, "stop")
            if lots > 0.0 and signal is Signal.FLAT:
                _close(price, "signal")

        # Open a new position on a fresh LONG.
        if lots == 0.0 and signal is Signal.LONG:
            if config.stop_mode is StopMode.ATR:
                stop_pips = atr_stop_pips(
                    bars[: i + 1],
                    pair,
                    multiplier=config.atr_multiplier,
                    window=config.atr_window,
                )
            else:
                stop_pips = config.stop_loss_pips
            lots = position_size_lots(balance, config.risk_percent, stop_pips, pair)
            entry_price = price
            if config.trail_pips is not None and lots > 0.0:
                trail = TrailingStop.from_pips(pair, entry_price, config.trail_pips)

        # Mark-to-market equity for the curve.
        if lots > 0.0:
            direction = 1 if price >= entry_price else -1
            open_pips = pips_between(pair, price, entry_price) * direction
            result.equity_curve.append(balance + open_pips * pip_value_per_lot(pair) * lots)
        else:
            result.equity_curve.append(balance)

    result.final_balance = result.equity_curve[-1] if result.equity_curve else balance
    return result


def run_backtest(
    closes: Sequence[float],
    pair: str = "EURUSD",
    risk_percent: float = 1.0,
    stop_loss_pips: float = 30.0,
    strategy: TrendStrategy | None = None,
    starting_balance: float = 10_000.0,
) -> BacktestResult:
    """Backward-compatible trend backtest (kept from v0.1).

    Thin wrapper over :func:`run_backtest_config` using fixed-pip stops.
    """
    config = BacktestConfig(
        pair=pair,
        risk_percent=risk_percent,
        stop_loss_pips=stop_loss_pips,
        starting_balance=starting_balance,
        strategy=StrategyKind.TREND,
        fast=strategy.fast if strategy else 10,
        slow=strategy.slow if strategy else 30,
    )
    return run_backtest_config(closes, config, strategy=strategy)
