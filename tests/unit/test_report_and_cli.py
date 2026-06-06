"""Tests for the report renderer, data helpers, and CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from forex_trading_bot import __version__
from forex_trading_bot.backtest import run_backtest_config
from forex_trading_bot.cli import app
from forex_trading_bot.config import BacktestConfig
from forex_trading_bot.data import synthetic_closes, synthetic_pairs
from forex_trading_bot.report import metrics_table, text_summary

runner = CliRunner()


def test_synthetic_closes_deterministic() -> None:
    assert synthetic_closes(50, seed=7) == synthetic_closes(50, seed=7)


def test_synthetic_pairs_keys() -> None:
    pairs = synthetic_pairs(100)
    assert set(pairs) == {"EURUSD", "GBPUSD", "USDJPY"}
    assert all(len(v) == 100 for v in pairs.values())


def test_text_summary_is_ascii() -> None:
    result = run_backtest_config(synthetic_closes(150), BacktestConfig())
    summary = text_summary(result)
    summary.encode("ascii")  # raises if non-ASCII
    assert "EURUSD" in summary


def test_metrics_table_has_rows() -> None:
    result = run_backtest_config(synthetic_closes(150), BacktestConfig())
    table = metrics_table(result)
    assert table.row_count >= 8


def test_cli_version() -> None:
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert __version__ in res.stdout


def test_cli_size() -> None:
    res = runner.invoke(app, ["size", "--balance", "10000", "--stop-loss-pips", "50"])
    assert res.exit_code == 0
    assert "lots" in res.stdout


def test_cli_backtest_trend() -> None:
    res = runner.invoke(app, ["backtest", "--strategy", "trend", "--bars", "150"])
    assert res.exit_code == 0
    assert "Backtest report" in res.stdout


def test_cli_backtest_atr_mode() -> None:
    res = runner.invoke(app, ["backtest", "--stop-mode", "atr", "--bars", "150"])
    assert res.exit_code == 0


def test_cli_portfolio() -> None:
    res = runner.invoke(app, ["portfolio", "--bars", "150"])
    assert res.exit_code == 0
    assert "Portfolio decisions" in res.stdout


def test_cli_demo() -> None:
    res = runner.invoke(app, ["demo"])
    assert res.exit_code == 0
