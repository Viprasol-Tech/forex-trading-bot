"""Render backtest results as rich tables and a plain-text summary.

Keeps presentation out of the engine so results can be consumed by the CLI, a
notebook, or a test. All numbers are printed in ASCII-safe form.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

from rich.console import Console
from rich.table import Table

from forex_trading_bot.backtest import BacktestResult


def _fmt_pf(value: float) -> str:
    return "inf" if math.isinf(value) else f"{value:.2f}"


def metrics_table(result: BacktestResult) -> Table:
    """A rich table of headline performance metrics."""
    table = Table(title=f"Backtest report -- {result.pair}", title_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Start balance", f"${result.starting_balance:,.2f}")
    table.add_row("Final balance", f"${result.final_balance:,.2f}")
    table.add_row("Total return", f"{result.total_return_pct:+.2f}%")
    table.add_row("Total pips", f"{result.total_pips:+.1f}")
    table.add_row("Trades", str(result.num_trades))
    table.add_row("Win rate", f"{result.win_rate * 100:.1f}%")
    table.add_row("Profit factor", _fmt_pf(result.profit_factor))
    table.add_row("Max drawdown", f"{result.max_drawdown_pct:.2f}%")
    table.add_row("Sharpe", f"{result.sharpe:.2f}")
    return table


def render_report(result: BacktestResult, console: Console | None = None) -> None:
    """Print the metrics table to the console."""
    con = console or Console()
    con.print(metrics_table(result))


def text_summary(result: BacktestResult) -> str:
    """A compact, ASCII-only one-paragraph summary (useful for logs/tests)."""
    return (
        f"{result.pair}: return {result.total_return_pct:+.2f}% "
        f"({result.total_pips:+.1f} pips) over {result.num_trades} trades, "
        f"win rate {result.win_rate * 100:.0f}%, "
        f"PF {_fmt_pf(result.profit_factor)}, "
        f"max DD {result.max_drawdown_pct:.1f}%, "
        f"Sharpe {result.sharpe:.2f}"
    )
