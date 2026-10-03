"""
analytics_engine.py — Layer 3: Analytics, Metrics & Business Logic
===================================================================

All aggregation and statistical logic; no UI rendering and **no imports from
config** — the few constants needed are defined below. Heavy computations are
wrapped in ``@st.cache_data`` so widget reruns are served from cache.

Public API
----------
add_margin_column, apply_filters, compute_kpis, profit_by_category,
category_summary, monthly_revenue, inventory_margin_ols, generate_insights
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import streamlit as st

MONTH_END_FREQ = "ME"  # Pandas 3.0+ month-end offset ('M' was removed)
SCATTER_SAMPLE_SIZE = 4_000  # points rendered; OLS is fitted on ALL rows
SAMPLE_SEED = 42


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class KPISet:
    """Headline metrics for the filtered dataset."""

    total_revenue: float
    total_profit: float
    profit_margin_pct: float
    avg_inventory_days: float
    transactions: int


@dataclass(frozen=True)
class Insight:
    """A business insight; ``level`` is one of: 'error', 'warning', 'info'."""

    level: str
    text: str


def _money(value: float) -> str:
    """Format a signed dollar amount as -$1,234 (not $-1,234)."""
    return f"-${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"


# --------------------------------------------------------------------------- #
# Preparation & filtering
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def add_margin_column(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with 'Profit Margin %' = Profit / Revenue * 100."""
    out = df.copy()
    out["Profit Margin %"] = out["Profit"] / out["Revenue"] * 100.0
    return out


def apply_filters(
    df: pd.DataFrame,
    regions: list[str],
    categories: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Filter rows by region, category and inclusive date range."""
    mask = (
        df["Region"].isin(regions)
        & df["Category"].isin(categories)
        & (df["Date"] >= pd.Timestamp(start))
        & (df["Date"] <= pd.Timestamp(end))
    )
    return df.loc[mask]


# --------------------------------------------------------------------------- #
# Metrics & aggregations
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def compute_kpis(df: pd.DataFrame) -> KPISet:
    """Compute headline KPIs; safe on empty input."""
    revenue = float(df["Revenue"].sum())
    profit = float(df["Profit"].sum())
    return KPISet(
        total_revenue=revenue,
        total_profit=profit,
        profit_margin_pct=(profit / revenue * 100.0) if revenue else 0.0,
        avg_inventory_days=float(df["Inventory_Days"].mean()) if len(df) else 0.0,
        transactions=len(df),
    )


@st.cache_data(show_spinner=False)
def profit_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Total profit per category, ascending (biggest drainer first)."""
    return (
        df.groupby("Category", observed=True)["Profit"]
        .sum()
        .reset_index()
        .sort_values("Profit", ignore_index=True)
    )


@st.cache_data(show_spinner=False)
def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Per-category scorecard: revenue, profit, margin %, inventory, volume."""
    grouped = df.groupby("Category", observed=True).agg(
        Revenue=("Revenue", "sum"),
        Profit=("Profit", "sum"),
        Avg_Inventory_Days=("Inventory_Days", "mean"),
        Transactions=("Revenue", "size"),
    )
    grouped["Margin %"] = grouped["Profit"] / grouped["Revenue"] * 100.0
    return grouped.reset_index().sort_values("Profit", ignore_index=True)


@st.cache_data(show_spinner=False)
def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue resampled to month-end ('ME', required by Pandas 3.0+)."""
    return df.set_index("Date")["Revenue"].resample(MONTH_END_FREQ).sum().reset_index()


# --------------------------------------------------------------------------- #
# Statistical modelling
# --------------------------------------------------------------------------- #
def _ols_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float] | None:
    """Closed-form simple OLS. Returns (slope, intercept, r_squared) or None."""
    if len(x) < 3 or np.ptp(x) == 0:
        return None
    slope, intercept = np.polyfit(x, y, deg=1)
    r = np.corrcoef(x, y)[0, 1]
    return float(slope), float(intercept), float(r**2)


@st.cache_data(show_spinner=False)
def inventory_margin_ols(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Map Inventory_Days -> Profit Margin % per category.

    Requires 'Profit Margin %' (see ``add_margin_column``).

    Returns
    -------
    sample : random subset of rows for scatter rendering
    trend  : two endpoints per category describing the OLS line (all rows)
    stats  : slope / intercept / R² per category
    """
    sample = df.sample(min(len(df), SCATTER_SAMPLE_SIZE), random_state=SAMPLE_SEED)

    trend_rows: list[dict] = []
    stat_rows: list[dict] = []
    for category, grp in df.groupby("Category", observed=True):
        x = grp["Inventory_Days"].to_numpy(dtype=float)
        y = grp["Profit Margin %"].to_numpy(dtype=float)
        fit = _ols_line(x, y)
        if fit is None:
            continue
        slope, intercept, r2 = fit
        for x_pt in (x.min(), x.max()):
            trend_rows.append(
                {
                    "Category": category,
                    "Inventory_Days": x_pt,
                    "Profit Margin %": slope * x_pt + intercept,
                }
            )
        stat_rows.append(
            {"Category": category, "Slope": slope, "Intercept": intercept, "R2": r2}
        )

    return sample, pd.DataFrame(trend_rows), pd.DataFrame(stat_rows)


# --------------------------------------------------------------------------- #
# Business logic
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def generate_insights(df: pd.DataFrame) -> list[Insight]:
    """Derive strategic insights from the data (nothing is hard-coded)."""
    if df.empty:
        return []

    summary = category_summary(df)
    overall_inv = float(df["Inventory_Days"].mean())
    insights: list[Insight] = []

    worst = summary.iloc[0]  # sorted ascending by profit
    best = summary.iloc[-1]

    if worst["Profit"] < 0:
        insights.append(
            Insight(
                "error",
                f"**{worst['Category']}** is a profit drainer: "
                f"{_money(worst['Profit'])} total profit at a "
                f"{worst['Margin %']:.1f}% margin, holding stock "
                f"{worst['Avg_Inventory_Days']:.0f} days on average vs "
                f"{overall_inv:.0f} overall. Recommend a discount strategy to "
                "clear overstocked items.",
            )
        )
    elif worst["Margin %"] < summary["Margin %"].median():
        insights.append(
            Insight(
                "warning",
                f"**{worst['Category']}** is the weakest category "
                f"({worst['Margin %']:.1f}% margin). Review pricing and cost.",
            )
        )

    insights.append(
        Insight(
            "info",
            f"**{best['Category']}** leads profitability with "
            f"{_money(best['Profit'])} profit ({best['Margin %']:.1f}% margin).",
        )
    )

    peak = monthly_revenue(df).nlargest(1, "Revenue")
    if not peak.empty:
        month = peak.iloc[0]["Date"].strftime("%B %Y")
        insights.append(
            Insight("info", f"Peak revenue month in this selection: **{month}**.")
        )
    return insights
