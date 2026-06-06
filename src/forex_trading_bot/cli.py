"""CLI for Forex Trading Bot.

Subcommands:
- ``size``      -- risk-based lot size for one trade.
- ``backtest``  -- run a strategy (trend/breakout/carry) with fixed or ATR stops
                   and print a full pip-PnL report.
- ``portfolio`` -- run a multi-pair backtest with a correlation filter.
- ``demo``      -- quick end-to-end run on synthetic data.
- ``version``   -- print the version.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from forex_trading_bot import __version__
from forex_trading_bot.backtest import run_backtest_config
from forex_trading_bot.config import BacktestConfig, StopMode, StrategyKind
from forex_trading_bot.data import synthetic_closes, synthetic_pairs
from forex_trading_bot.fx import position_size_lots
from forex_trading_bot.portfolio import CorrelationPortfolio, run_portfolio_backtest
from forex_trading_bot.report import render_report, text_summary

app = typer.Typer(add_completion=False, help="Forex Trading Bot -- by Viprasol Tech.")
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"forex-trading-bot [bold cyan]{__version__}[/] -- by Viprasol Tech")


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
def backtest(
    strategy: StrategyKind = StrategyKind.TREND,
    pair: str = "EURUSD",
    bars: int = 300,
    risk_percent: float = 1.0,
    stop_mode: StopMode = StopMode.FIXED,
    stop_loss_pips: float = 30.0,
    atr_multiplier: float = 2.0,
    trail_pips: float = 0.0,
    rate_differential: float = 2.0,
) -> None:
    """Backtest a strategy on synthetic data and print a pip-PnL report."""
    config = BacktestConfig(
        pair=pair,
        risk_percent=risk_percent,
        strategy=strategy,
        stop_mode=stop_mode,
        stop_loss_pips=stop_loss_pips,
        atr_multiplier=atr_multiplier,
        trail_pips=trail_pips if trail_pips > 0 else None,
        rate_differential=rate_differential,
    )
    closes = synthetic_closes(bars)
    result = run_backtest_config(closes, config)
    render_report(result, console)


@app.command()
def portfolio(
    bars: int = 300,
    max_correlation: float = 0.8,
    max_positions: int = 5,
) -> None:
    """Run a multi-pair backtest with a correlation filter."""
    prices = synthetic_pairs(bars)
    pf = CorrelationPortfolio(max_correlation=max_correlation, max_positions=max_positions)
    out = run_portfolio_backtest(prices, portfolio=pf)

    table = Table(title="Portfolio decisions", title_style="bold cyan")
    table.add_column("Pair", style="bold")
    table.add_column("Accepted", justify="center")
    table.add_column("Reason")
    for d in out.decisions:
        mark = "[green]yes[/]" if d.accepted else "[red]no[/]"
        table.add_row(d.pair, mark, d.reason)
    console.print(table)
    console.print(f"Held: [bold]{', '.join(out.held) or 'none'}[/]")
    console.print(f"Aggregate return: [bold green]{out.aggregate_return_pct:+.2f}%[/]")


@app.command()
def demo() -> None:
    """Run the trend strategy on synthetic EURUSD data."""
    config = BacktestConfig(strategy=StrategyKind.TREND)
    closes = synthetic_closes(300)
    result = run_backtest_config(closes, config)
    console.print(text_summary(result))
    render_report(result, console)


if __name__ == "__main__":
    app()
