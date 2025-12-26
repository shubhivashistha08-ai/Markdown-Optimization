import streamlit as st
import pandas as pd
from src.data_loading import load_markdown_data
from src.markdown_metrics import compute_revenue_by_stage

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Retail Markdown Optimization Assistant",
    layout="wide",
)

# -----------------------------
# Title
# -----------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")

# -----------------------------
# What problem does this app solve?
# (NO HTML — Streamlit-native blocks)
# -----------------------------
with st.container():
    st.subheader("ℹ️ What problem does this app solve?")

    st.markdown("**Business problem**")

    st.markdown(
        """
        Retailers often apply discounts without clearly knowing:
        - How deep to markdown
        - Which markdown stage (M1–M4) best balances clearance and profit
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

# -----------------------------
# Load data
# -----------------------------
df: pd.DataFrame = load_markdown_data()

# -----------------------------
# Filters
# -----------------------------
st.sidebar.header("🔍 Filters")

category_filter = st.sidebar.multiselect(
    "Select category",
    options=sorted(df["Category"].unique()),
    default=sorted(df["Category"].unique()),
)

season_filter = st.sidebar.multiselect(
    "Select season",
    options=sorted(df["Season"].unique()),
    default=sorted(df["Season"].unique()),
)

filtered_df = df[
    (df["Category"].isin(category_filter))
    & (df["Season"].isin(season_filter))
]

# -----------------------------
# Compute metrics
# -----------------------------
revenue_df = compute_revenue_by_stage(filtered_df)

# -----------------------------
# Chart
# -----------------------------
st.subheader("📈 Revenue by Markdown Stage")

st.bar_chart(
    revenue_df,
    x="Stage",
    y="Revenue",
    color="Category",
)

# -----------------------------
# How this chart is computed (DROPDOWN)
# -----------------------------
with st.expander("📊 How this chart is computed"):
    st.markdown(
        """
        **Step 1 – Row level**  
        For each product and markdown stage (M1–M4):

        Revenue = Price × (1 − Markdown) × Sales After Markdown

        **Step 2 – Group**  
        Revenue is summed by **Category** and **Markdown Stage**.

        **Step 3 – Plot**  
        - X-axis: Markdown stage (M1–M4)  
        - Y-axis: Revenue  
        - Color: Category  

        **Step 4 – Insight**  
        Identify which category and markdown stage combinations generate the strongest revenue lift.
        """
    )
