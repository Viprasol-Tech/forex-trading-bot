"""Deterministic synthetic FX price series for demos and tests.

No network, no randomness library state to manage: a tiny linear-congruential
generator gives reproducible pseudo-random walks so demos and tests are stable
across machines and runs.

Part of Forex Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math


def _lcg(seed: int) -> tuple[float, int]:
    seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
    return seed / 0x7FFFFFFF, seed


def synthetic_closes(
    n: int = 300,
    start: float = 1.1000,
    drift: float = 0.0002,
    noise: float = 0.0008,
    seed: int = 42,
) -> list[float]:
    """A trending pseudo-random walk of ``n`` closes.

    Combines a linear drift, a slow sine wave, and seeded noise so the series
    has genuine trends and pullbacks for strategies to react to.
    """
    closes: list[float] = []
    state = seed
    price = start
    for i in range(n):
        rnd, state = _lcg(state)
        wave = 0.0010 * math.sin(i / 18.0)
        price = price + drift + wave * 0.05 + (rnd - 0.5) * noise
        closes.append(round(price, 5))
    return closes


def synthetic_pairs(n: int = 300) -> dict[str, list[float]]:
    """A small basket of synthetic pairs for portfolio demos.

    EURUSD and GBPUSD are built from a shared driver (so they are correlated),
    while USDJPY uses an independent driver.
    """
    base = synthetic_closes(n, start=1.1000, seed=1)
    correlated = [round(1.2500 + (c - 1.1000) * 0.9 + 0.0001, 5) for c in base]
    independent = synthetic_closes(n, start=150.00, drift=0.01, noise=0.05, seed=99)
    return {"EURUSD": base, "GBPUSD": correlated, "USDJPY": independent}
