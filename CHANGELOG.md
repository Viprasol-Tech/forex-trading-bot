# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- **Indicators module** (`indicators.py`): SMA, EMA, rolling std-dev, True Range,
  Average True Range (ATR), OHLC `Bar` synthesis from closes, and a rolling
  Pearson return-correlation.
- **Risk module** (`risk.py`): ATR-scaled stop sizing (`atr_stop_pips`) and a
  ratcheting long-only `TrailingStop`.
- **New strategies**: `BreakoutStrategy` (Donchian channel) and `CarryStrategy`
  (interest-rate carry with a trend filter), plus a shared `Strategy` protocol
  so strategies are interchangeable.
- **Multi-pair portfolio** (`portfolio.py`): `CorrelationPortfolio` with a
  correlation filter and position cap, and `run_portfolio_backtest` for an
  aggregated multi-pair backtest.
- **Richer backtester**: configurable fixed/ATR/trailing stops, closed-trade
  records, and metrics — total return, total pips, win rate, profit factor,
  max drawdown and Sharpe.
- **Typed config** (`config.py`): a validated `BacktestConfig` (pydantic) with
  strategy/stop enums.
- **Deterministic data** (`data.py`): seeded synthetic close series and a
  correlated multi-pair basket for demos and tests.
- **Report module** (`report.py`): rich metrics table and an ASCII text summary.
- **CLI subcommands**: `backtest` and `portfolio` join `size`, `demo`, and
  `version`.
- **Example script** (`examples/portfolio_backtest.py`).
- Test suite expanded from 8 to 77 tests covering all new and existing behaviour.

### Changed
- `run_backtest` is retained for backward compatibility and now delegates to the
  new config-driven engine.
- Flagship README with architecture diagram, feature table, roadmap and FAQ.

## [0.1.0] - 2025

### Added
- Initial release of forex-trading-bot: pip/lot math, risk-based position
  sizing, trend strategy, and a pip-PnL backtest.
