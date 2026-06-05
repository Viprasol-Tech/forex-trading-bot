"""Backtest the FX trend strategy with risk-based sizing and pip PnL.

Each bar, the strategy emits LONG/FLAT. Going long opens a risk-sized position;
PnL is accrued in the quote currency from pip moves until the strategy goes flat.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from forex_trading_bot.fx import pip_value_per_lot, pips_between, position_size_lots
from forex_trading_bot.strategy import Signal, TrendStrategy


@dataclass(slots=True)
class BacktestResult:
    """Summary of an FX backtest."""

    starting_balance: float
    final_balance: float
    trades: int = 0
    equity_curve: list[float] = field(default_factory=list)

    @property
    def total_return_pct(self) -> float:
        if self.starting_balance == 0:
            return 0.0
        return (self.final_balance / self.starting_balance - 1.0) * 100.0


def run_backtest(
    closes: Sequence[float],
    pair: str = "EURUSD",
    risk_percent: float = 1.0,
    stop_loss_pips: float = 30.0,
    strategy: TrendStrategy | None = None,
    starting_balance: float = 10_000.0,
) -> BacktestResult:
    """Run the trend strategy with risk-based sizing; PnL accrues from pip moves."""
    strat = strategy or TrendStrategy()
    balance = starting_balance
    result = BacktestResult(starting_balance=starting_balance, final_balance=starting_balance)

    lots = 0.0
    entry_price = 0.0
    for i, price in enumerate(closes):
        signal = strat.signal(closes[: i + 1])
        if lots == 0.0 and signal is Signal.LONG:
            lots = position_size_lots(balance, risk_percent, stop_loss_pips, pair)
            entry_price = price
        elif lots > 0.0 and signal is Signal.FLAT:
            pips = pips_between(pair, price, entry_price) * (1 if price >= entry_price else -1)
            balance += pips * pip_value_per_lot(pair) * lots
            lots = 0.0
            result.trades += 1
        # Mark-to-market equity for the curve.
        if lots > 0.0:
            open_pips = pips_between(pair, price, entry_price) * (1 if price >= entry_price else -1)
            result.equity_curve.append(balance + open_pips * pip_value_per_lot(pair) * lots)
        else:
            result.equity_curve.append(balance)

    result.final_balance = result.equity_curve[-1] if result.equity_curve else starting_balance
    return result
