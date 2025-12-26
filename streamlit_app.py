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
# Load data
# --------------------------------------------------
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "src" / "synthetic_markdown_dataset.csv"
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()
st.write("Columns in CSV:", df.columns.tolist())

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

categories = sorted(df["category"].unique())
seasons = sorted(df["season"].unique())

selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
selected_seasons = st.sidebar.multiselect("Season", seasons, default=seasons)

filtered_df = df[
    df["category"].isin(selected_categories) &
    df["season"].isin(selected_seasons)
]

# --------------------------------------------------
# Revenue computation for each stage
# --------------------------------------------------
st.subheader("📊 Revenue by Markdown Stage and Category")

# Calculate revenue per markdown stage
for i in range(1, 5):
    filtered_df[f"revenue_m{i}"] = (
        filtered_df["original_price"]
        * (1 - filtered_df[f"markdown_{i}"])
        * filtered_df[f"sales_after_m{i}"]
    )

# Aggregate revenue by stage and category
revenue_stage_category = pd.DataFrame()
for i in range(1, 5):
    stage_revenue = (
        filtered_df.groupby("category")[f"revenue_m{i}"].sum().reset_index()
    )
    stage_revenue["stage"] = f"M{i}"
    stage_revenue.rename(columns={f"revenue_m{i}": "revenue"}, inplace=True)
    revenue_stage_category = pd.concat([revenue_stage_category, stage_revenue])

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

# Determine best stage per product
stage_cols = [f"revenue_m{i}" for i in range(1, 5)]
best_stage_df = filtered_df[["product_id"] + stage_cols].copy()
best_stage_df["best_stage"] = best_stage_df[stage_cols].idxmax(axis=1)
best_stage_df["best_stage"] = best_stage_df["best_stage"].str.replace("revenue_m", "M")

st.dataframe(best_stage_df[["product_id", "best_stage"]], use_container_width=True)
