"""Forex pip / lot math and risk-based position sizing.

The single most important discipline in FX is sizing each trade by *risk*, not gut
feel: given how much of your account you'll risk and how far away your stop is in
pips, there is exactly one correct position size. This module computes it.

Conventions:
- 1 standard lot = 100,000 units of the base currency.
- A "pip" is 0.0001 for most pairs, 0.01 for JPY pairs.
- Pip value per standard lot ≈ pip_size * 100,000 in the quote currency.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

STANDARD_LOT_UNITS = 100_000


def pip_size(pair: str) -> float:
    """Pip size for a pair: 0.01 for JPY quote pairs, else 0.0001."""
    return 0.01 if pair.upper().endswith("JPY") else 0.0001


def pips_between(pair: str, price_a: float, price_b: float) -> float:
    """Distance between two prices expressed in pips (always non-negative)."""
    return abs(price_a - price_b) / pip_size(pair)


def pip_value_per_lot(pair: str) -> float:
    """Approx pip value per standard lot, in the quote currency."""
    return pip_size(pair) * STANDARD_LOT_UNITS


def position_size_lots(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pair: str = "EURUSD",
) -> float:
    """Lots to trade so that hitting the stop loses exactly ``risk_percent``.

    Args:
        account_balance: Account equity in the quote currency.
        risk_percent: Percent of the account to risk (e.g. 1.0 for 1%).
        stop_loss_pips: Stop distance in pips (must be > 0).
        pair: Currency pair, used to pick the pip value.

    Returns:
        Position size in standard lots (>= 0).
    """
    if account_balance <= 0 or risk_percent <= 0 or stop_loss_pips <= 0:
        return 0.0
    risk_amount = account_balance * (risk_percent / 100.0)
    risk_per_lot = stop_loss_pips * pip_value_per_lot(pair)
    return risk_amount / risk_per_lot
