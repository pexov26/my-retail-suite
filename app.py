"""
app.py — Layer 4: Interactive Dashboard Presentation
====================================================

Pure presentation: sidebar filters, KPI cards and Plotly figures.

Imports from ``config`` are limited to the names present in the project's
config.py: PAGE_TITLE, PAGE_ICON, APP_TITLE, APP_SUBTITLE, CURRENCY_SYMBOL,
REGIONS, CATEGORIES, CUSTOM_CSS. Everything else is defined locally.

Run:  ./lab.sh run      (or: streamlit run app.py)
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics_engine as ae
from config import (
    APP_SUBTITLE,
    APP_TITLE,
    CATEGORIES,
    CURRENCY_SYMBOL,
    CUSTOM_CSS,
    PAGE_ICON,
    PAGE_TITLE,
    REGIONS,
)
from data_generator import load_data

# --------------------------------------------------------------------------- #
# Local presentation constants
# --------------------------------------------------------------------------- #
CATEGORY_COLORS = {
    "Electronics": "#636EFA",
    "Clothing": "#EF553B",
    "Furniture": "#00CC96",
    "Toys": "#AB63FA",
}
PRIMARY_COLOR = "#636EFA"
CHART_KWARGS = {"width": "stretch", "on_select": "ignore"}
PLOT_LAYOUT = {
    "template": "plotly_white",
    "margin": {"l": 10, "r": 10, "t": 50, "b": 10},
    "legend": {"orientation": "h", "yanchor": "bottom", "y": -0.3, "x": 0},
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def fmt_currency(value: float) -> str:
    """Compact currency formatting: $1.23M / $45.6K / $789."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    s = CURRENCY_SYMBOL
    if v >= 1e6:
        return f"{sign}{s}{v / 1e6:,.2f}M"
    if v >= 1e3:
        return f"{sign}{s}{v / 1e3:,.1f}K"
    return f"{sign}{s}{v:,.0f}"


def show_chart(fig: go.Figure, key: str) -> None:
    """Apply the shared layout and render with current Streamlit sizing."""
    fig.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig, key=key, **CHART_KWARGS)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
def render_sidebar(df):
    """Render filters and return the filtered DataFrame."""
    st.sidebar.header("Filters")

    regions = st.sidebar.multiselect("Region", options=REGIONS, default=REGIONS)
    categories = st.sidebar.multiselect(
        "Category", options=CATEGORIES, default=CATEGORIES
    )

    min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
    picked = st.sidebar.date_input(
        "Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d
    )
    # date_input yields a 1-tuple while the user is mid-selection.
    start, end = (picked[0], picked[1]) if len(picked) == 2 else (min_d, max_d)

    return ae.apply_filters(df, regions, categories, start, end)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def render_kpis(df) -> None:
    """Render the four headline KPI cards."""
    kpis = ae.compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", fmt_currency(kpis.total_revenue))
    c2.metric("Total Profit", fmt_currency(kpis.total_profit))
    c3.metric("Profit Margin", f"{kpis.profit_margin_pct:.1f}%")
    c4.metric("Avg Inventory Days", f"{kpis.avg_inventory_days:.1f} days")


def render_category_profit(df) -> None:
    """Render the profit-by-category bar chart."""
    st.subheader("Profitability by Category")
    fig = px.bar(
        ae.profit_by_category(df),
        x="Category",
        y="Profit",
        color="Category",
        color_discrete_map=CATEGORY_COLORS,
        title="Total Profit per Category (Identify Drainers)",
    )
    fig.update_layout(showlegend=False)
    show_chart(fig, "chart_profit_by_category")


def render_inventory_scatter(df) -> None:
    """Render inventory-vs-margin scatter with OLS trend lines."""
    st.subheader("Inventory vs. Profitability")
    sample, trend, stats = ae.inventory_margin_ols(df)

    fig = px.scatter(
        sample,
        x="Inventory_Days",
        y="Profit Margin %",
        color="Category",
        color_discrete_map=CATEGORY_COLORS,
        opacity=0.35,
        title="Correlation: Inventory Days vs Profit Margin (OLS)",
    )
    if not trend.empty:
        lines = px.line(
            trend,
            x="Inventory_Days",
            y="Profit Margin %",
            color="Category",
            color_discrete_map=CATEGORY_COLORS,
        )
        lines.update_traces(showlegend=False, line={"width": 3})
        fig.add_traces(lines.data)
    show_chart(fig, "chart_inventory_scatter")

    with st.expander("OLS fit details"):
        st.dataframe(
            stats,
            hide_index=True,
            width="stretch",
            column_config={
                "Slope": st.column_config.NumberColumn(format="%.3f"),
                "Intercept": st.column_config.NumberColumn(format="%.2f"),
                "R2": st.column_config.NumberColumn("R²", format="%.3f"),
            },
        )


def render_revenue_trend(df) -> None:
    """Render the monthly revenue line chart."""
    st.subheader("Seasonal Revenue Trend")
    fig = px.line(
        ae.monthly_revenue(df),
        x="Date",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Behavior",
    )
    fig.update_traces(line_color=PRIMARY_COLOR)
    show_chart(fig, "chart_monthly_revenue")


def render_scorecard(df) -> None:
    """Render the per-category scorecard table."""
    st.subheader("Category Scorecard")
    st.dataframe(
        ae.category_summary(df),
        hide_index=True,
        width="stretch",
        column_config={
            "Revenue": st.column_config.NumberColumn(format="dollar"),
            "Profit": st.column_config.NumberColumn(format="dollar"),
            "Avg_Inventory_Days": st.column_config.NumberColumn(
                "Avg Inventory Days", format="%.1f"
            ),
            "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
            "Transactions": st.column_config.NumberColumn(format="%d"),
        },
    )


def render_insights(df) -> None:
    """Render data-driven insight banners."""
    renderers = {"error": st.error, "warning": st.warning, "info": st.info}
    for insight in ae.generate_insights(df):
        renderers[insight.level](insight.text)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def main() -> None:
    """Dashboard entrypoint."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.title(APP_TITLE)
    st.markdown(APP_SUBTITLE)

    df = ae.add_margin_column(load_data())
    filtered = render_sidebar(df)

    if filtered.empty:
        st.warning("No data matches the current filters. Adjust the sidebar.")
        st.stop()

    render_kpis(filtered)
    render_category_profit(filtered)

    col_a, col_b = st.columns(2)
    with col_a:
        render_inventory_scatter(filtered)
    with col_b:
        render_revenue_trend(filtered)

    render_scorecard(filtered)
    render_insights(filtered)


main()
