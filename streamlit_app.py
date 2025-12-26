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
    df = pd.read_csv(csv_path)
    # Normalize column names: lowercase, strip spaces, replace spaces with underscores
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()
    return df

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

categories = sorted(df["category"].unique())
seasons = sorted(df["season"].unique())

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
    df["category"].isin(selected_categories) &
    df["season"].isin(selected_seasons)
]

# --------------------------------------------------
# Revenue computation
# --------------------------------------------------
st.subheader("📊 Revenue by Markdown Stage and Category")

filtered_df["revenue"] = (
    filtered_df["price"]
    * (1 - filtered_df["markdown"])
    * filtered_df["sales_after"]
)

revenue_stage_category = (
    filtered_df
    .groupby(["stage", "category"], as_index=False)["revenue"]
    .sum()
)

st.bar_chart(
    revenue_stage_category,
    x="stage",
    y="revenue",
    color="category",
    use_container_width=True
)

# --------------------------------------------------
# Best markdown stage per product
# --------------------------------------------------
st.subheader("🏆 Best Markdown Stage per Product")

best_stage = (
    filtered_df
    .groupby(["product_id", "stage"], as_index=False)["revenue"]
    .sum()
    .sort_values(["product_id", "revenue"], ascending=[True, False])
    .drop_duplicates("product_id")
)

st.dataframe(
    best_stage.rename(columns={"stage": "Best_Markdown_Stage"}),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption("Built with Streamlit • Retail Markdown Optimization Assistant")
