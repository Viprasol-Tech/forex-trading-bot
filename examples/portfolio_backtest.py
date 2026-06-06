"""End-to-end example: backtest strategies and run a correlation-filtered book.

Run from the repo root with::

    PYTHONPATH=src python examples/portfolio_backtest.py

It demonstrates the three strategies, ATR-scaled stops, trailing stops, and the
multi-pair portfolio with a correlation filter -- all on deterministic synthetic
data so the output is reproducible.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from forex_trading_bot.backtest import run_backtest_config
from forex_trading_bot.config import BacktestConfig, StopMode, StrategyKind
from forex_trading_bot.data import synthetic_closes, synthetic_pairs
from forex_trading_bot.portfolio import CorrelationPortfolio, run_portfolio_backtest
from forex_trading_bot.report import text_summary


def compare_strategies() -> None:
    """Backtest trend, breakout and carry on the same series."""
    closes = synthetic_closes(300)
    print("== Strategy comparison (fixed 30-pip stop) ==")
    for kind in (StrategyKind.TREND, StrategyKind.BREAKOUT, StrategyKind.CARRY):
        cfg = BacktestConfig(strategy=kind, rate_differential=2.5)
        result = run_backtest_config(closes, cfg)
        print(f"  {kind.value:9s} -> {text_summary(result)}")


def atr_vs_trailing() -> None:
    """Compare ATR-scaled stops against a trailing stop."""
    closes = synthetic_closes(300)
    print("\n== Stop styles (trend strategy) ==")

    atr_cfg = BacktestConfig(stop_mode=StopMode.ATR, atr_multiplier=2.0)
    print(f"  ATR(2.0)  -> {text_summary(run_backtest_config(closes, atr_cfg))}")

    trail_cfg = BacktestConfig(trail_pips=20.0)
    print(f"  trail(20) -> {text_summary(run_backtest_config(closes, trail_cfg))}")


def correlation_portfolio() -> None:
    """Run a 3-pair book; the correlation filter drops the redundant pair."""
    prices = synthetic_pairs(300)
    pf = CorrelationPortfolio(max_correlation=0.8, max_positions=3)
    out = run_portfolio_backtest(prices, portfolio=pf)
    print("\n== Correlation-filtered portfolio ==")
    for d in out.decisions:
        flag = "HELD" if d.accepted else "skip"
        print(f"  [{flag}] {d.pair}: {d.reason}")
    print(f"  Held: {', '.join(out.held)}")
    print(f"  Aggregate return: {out.aggregate_return_pct:+.2f}%")


if __name__ == "__main__":
    compare_strategies()
    atr_vs_trailing()
    correlation_portfolio()
