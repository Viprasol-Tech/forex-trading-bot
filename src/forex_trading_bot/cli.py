"""CLI for Forex Trading Bot.

``forex-trading-bot size`` computes a risk-based lot size; ``forex-trading-bot
demo`` runs the trend strategy on synthetic EURUSD data.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console

from forex_trading_bot import __version__
from forex_trading_bot.backtest import run_backtest
from forex_trading_bot.fx import position_size_lots

app = typer.Typer(add_completion=False, help="Forex Trading Bot — by Viprasol Tech.")
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"forex-trading-bot [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def size(
    balance: float = 10_000.0,
    risk_percent: float = 1.0,
    stop_loss_pips: float = 30.0,
    pair: str = "EURUSD",
) -> None:
    """Compute the risk-based position size in lots."""
    lots = position_size_lots(balance, risk_percent, stop_loss_pips, pair)
    console.print(
        f"Pair {pair} | balance ${balance:,.0f} | "
        f"risk {risk_percent:.1f}% | SL {stop_loss_pips:.0f} pips"
    )
    console.print(f"Position size: [bold green]{lots:.2f} lots[/] ({lots * 100_000:,.0f} units)")


@app.command()
def demo() -> None:
    """Run the trend strategy on synthetic EURUSD data."""
    closes = [1.1000 + 0.0005 * math.sin(i / 12.0) + 0.0002 * i for i in range(300)]
    result = run_backtest(closes)
    console.print(f"Trades:        {result.trades}")
    console.print(f"Start balance: [bold]${result.starting_balance:,.2f}[/]")
    console.print(f"Final balance: [bold]${result.final_balance:,.2f}[/]")
    console.print(f"Total return:  [bold green]{result.total_return_pct:+.2f}%[/]")


if __name__ == "__main__":
    app()
