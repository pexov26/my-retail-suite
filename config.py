# L1: Core Configuration & Styling Layer

# Application UI Metadata
PAGE_TITLE = "Retail Intelligence Suite"
PAGE_ICON = "📊"
APP_TITLE = "📊 Enterprise Retail Performance & Profitability Analysis"
APP_SUBTITLE = (
    "Analyzing transactional retail data to uncover profit-draining categories."
)

# System Constants & Settings
CURRENCY_SYMBOL = "$"
ANIMATION_SPEED = 0.5
MONTH_END_FREQ = "ME"
SCATTER_SAMPLE_SIZE = 4000

# Data Engine Structural Parameters
REGIONS = ["North", "South", "East", "West"]
CATEGORIES = ["Electronics", "Clothing", "Furniture", "Toys"]

# Range Settings for Synthetic Data Framework Generation
INVENTORY_DAY_RANGES = {
    "Electronics": (10, 45),
    "Furniture": (40, 120),
    "Clothing": (5, 60),
    "Toys": (5, 60),
}

MARGIN_RANGES = {
    "Electronics": (0.15, 0.45),
    "Furniture": (-0.30, 0.15),
    "Clothing": (0.10, 0.55),
    "Toys": (0.10, 0.55),
}

# Interface Color Tokens mapping
CATEGORY_COLORS = {
    "Electronics": "#636EFA",
    "Clothing": "#EF553B",
    "Furniture": "#00CC96",
    "Toys": "#AB63FA",
}

# Streamlit-specific visual configuration setups
SIM_CONFIG = {"on_select": "ignore", "width": "stretch"}

# Translucent theme styles compatible with both light and dark backgrounds
CUSTOM_CSS = """
<style>
    div[data-testid="stMetricSimpleColumn"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
    }
</style>
"""
