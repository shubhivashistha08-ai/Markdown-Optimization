import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Retail Markdown Optimization Assistant",
    page_icon="🛍️",
    layout="wide"
)

# --------------------------------------------------
# Load data FIRST
# --------------------------------------------------

@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "src" / "synthetic_markdown_dataset.csv"
    return pd.read_csv(csv_path)


try:
    df = load_data()
except Exception:
    st.error("❌ Failed to load the dataset.")
    st.stop()

# --------------------------------------------------
# App title (only shown if data loads)
# --------------------------------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")

# --------------------------------------------------
# Problem statement (TEXT ONLY)
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
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

categories = sorted(df["Category"].unique())
seasons = sorted(df["Season"].unique())

selected_categories = st.sidebar.multiselect(
    "Category",
    categories,
    default=categories
)

selected_seasons = st.sidebar.multiselect(
    "Season",
    seasons,
    default=seasons
)

filtered_df = df[
    df["Category"].isin(selected_categories) &
    df["Season"].isin(selected_seasons)
]

# --------------------------------------------------
# Revenue computation
# --------------------------------------------------
st.subheader("📊 Revenue by Markdown Stage and Category")

filtered_df["Revenue"] = (
    filtered_df["Price"]
    * (1 - filtered_df["Markdown"])
    * filtered_df["Sales_After"]
)

revenue_stage_category = (
    filtered_df
    .groupby(["Stage", "Category"], as_index=False)["Revenue"]
    .sum()
)

st.bar_chart(
    revenue_stage_category,
    x="Stage",
    y="Revenue",
    color="Category",
    use_container_width=True
)

# --------------------------------------------------
# Best markdown stage per product
# --------------------------------------------------
st.subheader("🏆 Best Markdown Stage per Product")

best_stage = (
    filtered_df
    .groupby(["Product_ID", "Stage"], as_index=False)["Revenue"]
    .sum()
    .sort_values(["Product_ID", "Revenue"], ascending=[True, False])
    .drop_duplicates("Product_ID")
)

st.dataframe(
    best_stage.rename(columns={"Stage": "Best_Markdown_Stage"}),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption("Built with Streamlit • Retail Markdown Optimization Assistant")
