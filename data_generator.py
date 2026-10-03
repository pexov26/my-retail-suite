"""
data_generator.py — Layer 2: High-Performance Simulated Data Engine
===================================================================

Builds a multi-year synthetic retail transaction table.

Only ``REGIONS`` and ``CATEGORIES`` are imported from ``config``; every other
constant (margin / inventory ranges, seasonality, volume) lives in this file.

* Fully vectorized with NumPy's ``Generator`` API (no Python row loops).
* ``generate_transactions`` is pure and testable without Streamlit.
* ``load_data`` is the ``@st.cache_data`` entry point used by the UI.

Output schema:
    Date, Category, Region, Revenue, Cost, Profit, Inventory_Days
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from config import CATEGORIES, REGIONS

# --------------------------------------------------------------------------- #
# Local constants (intentionally NOT in config.py)
# --------------------------------------------------------------------------- #
# revenue = cost * (1 + U(low, high)); Furniture is engineered to bleed profit.
MARGIN_RANGES: dict[str, tuple[float, float]] = {
    "Electronics": (0.15, 0.45),
    "Clothing": (0.10, 0.55),
    "Furniture": (-0.30, 0.15),
    "Toys": (0.10, 0.55),
}

# Inventory holding period in days; Furniture is slow-moving.
INVENTORY_DAY_RANGES: dict[str, tuple[int, int]] = {
    "Electronics": (10, 45),
    "Clothing": (5, 60),
    "Furniture": (40, 120),
    "Toys": (5, 60),
}

# Relative sales volume per calendar month -> Q4 holiday peak.
SEASONALITY: dict[int, float] = {
    1: 0.80,
    2: 0.75,
    3: 0.90,
    4: 0.95,
    5: 1.00,
    6: 0.95,
    7: 0.90,
    8: 0.95,
    9: 1.00,
    10: 1.10,
    11: 1.40,
    12: 1.60,
}


@dataclass(frozen=True)
class SimulationSettings:
    """Parameters for the generator (hashable -> usable as a cache key)."""

    seed: int = 42
    n_records: int = 50_000
    start_date: str = "2022-01-01"
    end_date: str = "2024-12-31"
    cost_low: float = 10.0
    cost_high: float = 500.0


DEFAULT_SETTINGS = SimulationSettings()


def generate_transactions(
    settings: SimulationSettings = DEFAULT_SETTINGS,
) -> pd.DataFrame:
    """Generate synthetic transactions (deterministic for a given seed)."""
    rng = np.random.default_rng(settings.seed)
    n = settings.n_records

    # Seasonally weighted dates across the full multi-year window.
    dates = pd.date_range(settings.start_date, settings.end_date, freq="D")
    months = dates.to_series().dt.month
    weights = months.map(SEASONALITY).to_numpy(dtype=float)
    date_idx = rng.choice(len(dates), size=n, p=weights / weights.sum())

    # Dimensions (uniform over whatever config.py defines).
    cat_idx = rng.integers(0, len(CATEGORIES), size=n)
    category = np.asarray(CATEGORIES)[cat_idx]
    region = rng.choice(np.asarray(REGIONS), size=n)

    # Per-category bounds, broadcast by category index.
    margin_lo = np.array([MARGIN_RANGES[c][0] for c in CATEGORIES])[cat_idx]
    margin_hi = np.array([MARGIN_RANGES[c][1] for c in CATEGORIES])[cat_idx]
    inv_lo = np.array([INVENTORY_DAY_RANGES[c][0] for c in CATEGORIES])[cat_idx]
    inv_hi = np.array([INVENTORY_DAY_RANGES[c][1] for c in CATEGORIES])[cat_idx]

    cost = rng.uniform(settings.cost_low, settings.cost_high, size=n)
    revenue = cost * (1.0 + rng.uniform(margin_lo, margin_hi))
    inventory_days = rng.integers(inv_lo, inv_hi, endpoint=False)

    df = pd.DataFrame(
        {
            "Date": dates[date_idx],
            "Category": category,
            "Region": region,
            "Revenue": revenue,
            "Cost": cost,
            "Profit": revenue - cost,
            "Inventory_Days": inventory_days,
        }
    )
    return df.sort_values("Date", ignore_index=True)


@st.cache_data(show_spinner="Generating retail dataset…")
def load_data(settings: SimulationSettings = DEFAULT_SETTINGS) -> pd.DataFrame:
    """Cached entry point: build the dataset once per unique settings object."""
    return generate_transactions(settings)
