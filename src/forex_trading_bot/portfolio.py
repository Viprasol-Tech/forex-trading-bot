"""Multi-pair portfolio with a correlation filter.

Trading several FX pairs at once concentrates risk when those pairs move
together (think EURUSD and GBPUSD). This module runs a strategy across many
pairs and applies a *correlation filter*: a candidate long is rejected if the
pair is too highly correlated with a pair already held, so the book stays
diversified.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from forex_trading_bot.config import BacktestConfig
from forex_trading_bot.indicators import correlation
from forex_trading_bot.strategy import Signal, Strategy, TrendStrategy

if TYPE_CHECKING:
    from forex_trading_bot.backtest import BacktestResult


@dataclass(slots=True)
class PairDecision:
    """The portfolio's decision for one pair on the latest bar."""

    pair: str
    raw_signal: Signal
    accepted: bool
    reason: str


@dataclass(slots=True)
class PortfolioResult:
    """Outcome of one portfolio evaluation step."""

    decisions: list[PairDecision] = field(default_factory=list)

    @property
    def held(self) -> list[str]:
        return [d.pair for d in self.decisions if d.accepted]


@dataclass(slots=True)
class CorrelationPortfolio:
    """Run a strategy across pairs, rejecting correlated overlaps.

    Args:
        strategy: Strategy applied to every pair (defaults to a trend follower).
        max_correlation: A candidate long is rejected when its return
            correlation with any already-held pair exceeds this threshold.
        corr_window: Window (in returns) for the rolling correlation.
        max_positions: Hard cap on simultaneous open positions.
    """

    strategy: Strategy = field(default_factory=TrendStrategy)
    max_correlation: float = 0.8
    corr_window: int = 30
    max_positions: int = 5

    def __post_init__(self) -> None:
        if not -1.0 <= self.max_correlation <= 1.0:
            raise ValueError("max_correlation must be in [-1, 1]")
        if self.max_positions < 1:
            raise ValueError("max_positions must be >= 1")

    def evaluate(self, prices: Mapping[str, Sequence[float]]) -> PortfolioResult:
        """Decide which pairs to hold given each pair's close history.

        Pairs are considered in descending order of recent momentum (last close
        over first close) so the strongest trends claim the diversification
        budget first.
        """
        result = PortfolioResult()
        ranked = sorted(
            prices.items(),
            key=lambda kv: (kv[1][-1] / kv[1][0]) if kv[1] and kv[1][0] else 0.0,
            reverse=True,
        )
        held: list[str] = []
        for pair, closes in ranked:
            raw = self.strategy.signal(closes)
            if raw is not Signal.LONG:
                result.decisions.append(PairDecision(pair, raw, False, "no signal"))
                continue
            if len(held) >= self.max_positions:
                result.decisions.append(PairDecision(pair, raw, False, "max positions"))
                continue
            blocked_by = self._too_correlated(pair, held, prices)
            if blocked_by is not None:
                result.decisions.append(
                    PairDecision(pair, raw, False, f"correlated with {blocked_by}")
                )
                continue
            held.append(pair)
            result.decisions.append(PairDecision(pair, raw, True, "accepted"))
        return result

    def _too_correlated(
        self, pair: str, held: Sequence[str], prices: Mapping[str, Sequence[float]]
    ) -> str | None:
        for other in held:
            corr = correlation(prices[pair], prices[other], self.corr_window)
            if abs(corr) > self.max_correlation:
                return other
        return None


@dataclass(slots=True)
class PortfolioBacktest:
    """Aggregate outcome of a multi-pair portfolio backtest."""

    held: list[str]
    decisions: list[PairDecision]
    per_pair: dict[str, BacktestResult]
    aggregate_return_pct: float


def run_portfolio_backtest(
    prices: Mapping[str, Sequence[float]],
    portfolio: CorrelationPortfolio | None = None,
    config: BacktestConfig | None = None,
) -> PortfolioBacktest:
    """Backtest each accepted pair independently and aggregate the results.

    Runs the portfolio's accept/reject logic to decide which pairs would be
    traded, backtests those pairs, and sums their PnL into one summary.
    """
    from forex_trading_bot.backtest import run_backtest_config

    pf = portfolio or CorrelationPortfolio()
    cfg = config or BacktestConfig()

    decision = pf.evaluate(prices)
    held = decision.held

    per_pair: dict[str, BacktestResult] = {}
    total_start = 0.0
    total_final = 0.0
    for pair in held:
        pair_cfg = cfg.model_copy(update={"pair": pair})
        res = run_backtest_config(prices[pair], pair_cfg, strategy=pf.strategy)
        per_pair[pair] = res
        total_start += res.starting_balance
        total_final += res.final_balance

    agg_return = (total_final / total_start - 1.0) * 100.0 if total_start else 0.0
    return PortfolioBacktest(
        held=held,
        decisions=decision.decisions,
        per_pair=per_pair,
        aggregate_return_pct=agg_return,
    )
