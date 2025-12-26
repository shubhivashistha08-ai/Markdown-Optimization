import streamlit as st
import pandas as pd

from src.data_loading import load_markdown_data
from src.markdown_metrics import (
    compute_revenue_by_stage_category,
    compute_best_stage_per_product
)

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Retail Markdown Optimization Assistant",
    page_icon="🛍️",
    layout="wide"
)

# --------------------------------------------------
# App title
# --------------------------------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")

# --------------------------------------------------
# Problem statement (NO HTML, NO CSS)
# --------------------------------------------------
st.subheader("ℹ️ What problem does this app solve?")

st.markdown("**Business problem**")

st.markdown(
    """
Retailers often apply discounts without knowing:
- How deep to markdown
- Which markdown stage (M1–M4) balances clearance and profit
"""
)

st.markdown("**This app helps you answer:**")

st.markdown(
    """
- Which **categories and seasons** respond best to deeper markdowns  
- Which **markdown stage** maximizes revenue and sell-through for a product
"""
)

st.divider()

# --------------------------------------------------
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    return load_markdown_data()

try:
    df = load_data()
except Exception as e:
    st.error("Failed to load markdown dataset.")
    st.stop()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

categories = sorted(df["Category"].unique())
seasons = sorted(df["Season"].unique())

selected_categories = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

selected_seasons = st.sidebar.multiselect(
    "Select Season",
    seasons,
    default=seasons
)

filtered_df = df[
    (df["Category"].isin(selected_categories)) &
    (df["Season"].isin(selected_seasons))
]

# --------------------------------------------------
# Revenue by stage & category
# --------------------------------------------------
st.subheader("📊 Revenue by Markdown Stage and Category")

revenue_df = compute_revenue_by_stage_category(filtered_df)

if revenue_df.empty:
    st.warning("No data available for the selected filters.")
else:
    st.bar_chart(
        revenue_df,
        x="Stage",
        y="Revenue",
        color="Category",
        use_container_width=True
    )

# --------------------------------------------------
# Best markdown stage per product
# --------------------------------------------------
st.subheader("🏆 Best Markdown Stage per Product")

best_stage_df = compute_best_stage_per_product(filtered_df)

st.dataframe(
    best_stage_df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption("Built with Streamlit • Retail Markdown Optimization Assistant")
