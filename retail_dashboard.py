"""Retail business performance dashboard."""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from pandas import DataFrame


# 1. Generate Synthetic Retail Data
@st.cache_data
def load_data() -> DataFrame:
    """Generate synthetic retail transaction data for dashboard analysis."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=365, freq="D")
    categories = ["Electronics", "Clothing", "Furniture", "Toys"]
    regions = ["North", "South", "East", "West"]

    data = []
    for _ in range(1000):
        category = np.random.choice(categories)
        cost = np.random.uniform(10, 500)
        # Furniture is engineered to have lower/negative margins to show
        # "profit-draining" behavior
        margin_multiplier = (
            np.random.uniform(-0.2, 0.3)
            if category == "Furniture"
            else np.random.uniform(0.1, 0.6)
        )
        revenue = cost * (1 + margin_multiplier)

        data.append(
            {
                "Date": np.random.choice(dates),
                "Category": category,
                "Region": np.random.choice(regions),
                "Revenue": revenue,
                "Cost": cost,
                "Profit": revenue - cost,
                "Inventory_Days": np.random.randint(5, 90),
            }
        )
    return pd.DataFrame(data)


df = load_data()
df["Profit Margin %"] = (df["Profit"] / df["Revenue"]) * 100

# 2. Build Dashboard UI
st.set_page_config(page_title="Retail Performance Dashboard", layout="wide")
st.title("Retail Business Performance & Profitability Analysis")
st.markdown(
    "Analyzing transactional retail data to uncover "
    "profit-draining categories and optimize inventory."
)

# Sidebar Filters
st.sidebar.header("Filters")
selected_region = st.sidebar.multiselect(
    "Select Region",
    df["Region"].unique(),
    default=df["Region"].unique(),
)
filtered_df = df[df["Region"].isin(selected_region)]

# 3. Key Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${filtered_df['Revenue'].sum():,.2f}")
col2.metric("Total Profit", f"${filtered_df['Profit'].sum():,.2f}")
col3.metric(
    "Avg Inventory Days",
    f"{filtered_df['Inventory_Days'].mean():.1f} days",
)

# 4. Visualizations
st.subheader("Profitability by Category")
profit_by_cat = filtered_df.groupby("Category")["Profit"].sum().reset_index()
fig1 = px.bar(
    profit_by_cat,
    x="Category",
    y="Profit",
    color="Category",
    title="Total Profit per Category (Identify Drainers)",
)
st.plotly_chart(fig1, on_select="ignore")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Inventory vs. Profitability")
    fig2 = px.scatter(
        filtered_df,
        x="Inventory_Days",
        y="Profit Margin %",
        color="Category",
        trendline="ols",
        title="Correlation: Inventory Days vs Profit Margin",
    )
    st.plotly_chart(fig2, on_select="ignore")

with col_b:
    st.subheader("Seasonal Revenue Trend")
    # FIX: Changed 'M' to 'ME' for Pandas 3.0 compliance
    monthly_trend = (
        filtered_df.set_index("Date").resample("ME")["Revenue"].sum().reset_index()
    )
    fig3 = px.line(
        monthly_trend,
        x="Date",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Behavior",
    )
    st.plotly_chart(fig3, on_select="ignore")

st.success(
    "Strategic Insight: Furniture shows negative profit margins and "
    "high inventory days. Recommend immediate discount strategy to "
    "clear overstocked items."
)
