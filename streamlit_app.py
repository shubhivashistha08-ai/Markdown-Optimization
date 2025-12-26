import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# -------------------------------
# Data loading and preprocessing
# -------------------------------
@st.cache_data
def load_markdown_data():
    csv_path = Path(__file__).parent / "src" / "synthetic_markdown_dataset.csv"
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip().str.lower()
    
    # Rename columns to match template
    df.rename(columns={
        "original_price": "price",
        "sales_after_m1": "sales_m1",
        "sales_after_m2": "sales_m2",
        "sales_after_m3": "sales_m3",
        "sales_after_m4": "sales_m4",
        "markdown_1": "markdown_m1",
        "markdown_2": "markdown_m2",
        "markdown_3": "markdown_m3",
        "markdown_4": "markdown_m4"
    }, inplace=True)
    return df

def compute_stage_metrics(df):
    stage_data = []
    for stage in range(1, 5):
        stage_df = df.copy()
        stage_df["stage"] = f"M{stage}"
        stage_df["markdown"] = stage_df[f"markdown_m{stage}"]
        stage_df["sales"] = stage_df[f"sales_m{stage}"]
        stage_df["revenue"] = stage_df["price"] * (1 - stage_df["markdown"]) * stage_df["sales"]
        stage_df["sell_through"] = stage_df["sales"] / stage_df["stock_level"]
        stage_data.append(stage_df)
    metrics_long = pd.concat(stage_data, ignore_index=True)
    return metrics_long

# -------------------------------
# Load data
# -------------------------------
df = load_markdown_data()
metrics_long = compute_stage_metrics(df)

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(
    page_title="Retail Markdown Optimization Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Heading & problem statement
# -------------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")

with st.expander("ℹ️ What problem does this app solve?", expanded=True):
    st.markdown("""
        **Business problem**  
        Retailers often apply discounts without knowing **how deep** to markdown
        or **which stage** (M1–M4) gives the best balance between:
        - Clearing seasonal or slow-moving stock  
        - Protecting profit margin

        This app helps you answer:
        - Which **categories and seasons** respond best to deeper markdowns?
        - For a given product, which **markdown stage** maximizes
          **revenue** and **sell-through**?
    """)

# -------------------------------
# Sidebar filters
# -------------------------------
st.sidebar.header("Global filters")

category_options = sorted(df["category"].unique())
season_options = sorted(df["season"].unique())

selected_categories = st.sidebar.multiselect("Category", options=category_options, default=category_options)
selected_seasons = st.sidebar.multiselect("Season", options=season_options, default=season_options)

filtered_df = df[
    df["category"].isin(selected_categories) &
    df["season"].isin(selected_seasons)
].copy()

filtered_long = metrics_long[
    metrics_long["category"].isin(selected_categories) &
    metrics_long["season"].isin(selected_seasons)
].copy()

# -------------------------------
# Key insights cards
# -------------------------------
st.subheader("📌 Key Insights")
k1, k2, k3, k4 = st.columns(4)

total_products = filtered_df["product_id"].nunique()
total_categories = filtered_df["category"].nunique()
best_selling_category = filtered_df.groupby("category")["price"].sum().idxmax()
top_season = filtered_df.groupby("season")["price"].sum().idxmax()

k1.metric("Total Products", total_products)
k2.metric("Total Categories", total_categories)
k3.metric("Best Selling Category", best_selling_category)
k4.metric("Top Season", top_season)

st.divider()

# -------------------------------
# Tabs for dashboard & drill-down
# -------------------------------
tab1, tab2 = st.tabs(["Category/Season Dashboard", "Product Drill-down"])

# -------------------------------
# TAB 1: Category/Season Dashboard
# -------------------------------
with tab1:
    st.subheader("Revenue by markdown stage (per category)")

    if filtered_long.empty:
        st.info("No data for selected filters.")
    else:
        rev_by_cat_stage = (
            filtered_long.groupby(["category", "stage"], as_index=False)["revenue"].sum()
        )
        
        # Plot with Plotly
        fig = px.bar(
            rev_by_cat_stage,
            x="stage",
            y="revenue",
            color="category",
            barmode="group",
            labels={"stage": "Markdown Stage", "revenue": "Revenue ($)", "category": "Category"}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Season × Category revenue
        st.subheader("Season × Category: total revenue")
        heat = filtered_long.groupby(["category", "season"], as_index=False)["revenue"].sum()
        heat_pivot = heat.pivot(index="category", columns="season", values="revenue").fillna(0)
        st.dataframe(heat_pivot.style.format("{:,.0f}"), use_container_width=True)

# -------------------------------
# TAB 2: Product Drill-down
# -------------------------------
with tab2:
    st.subheader("Product drill-down")

    if filtered_df.empty:
        st.info("No products for selected filters.")
    else:
        prod_subset = filtered_df.copy()
        prod_subset["product_label"] = (
            prod_subset["product_name"] + " | " +
            prod_subset["brand"] + " | " +
            prod_subset["season"]
        )
        selected_label = st.selectbox("Select product", sorted(prod_subset["product_label"].unique()))
        row = prod_subset[prod_subset["product_label"] == selected_label].iloc[0]

        # Display product info
        st.markdown("### Product Info")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write(f"**Name:** {row['product_name']}")
            st.write(f"**Category:** {row['category']}")
            st.write(f"**Brand:** {row['brand']}")
            st.write(f"**Season:** {row['season']}")
        with c2:
            st.write(f"**Original Price:** {row['price']:.2f}")
            st.write(f"**Competitor Price:** {row['competitor_price']:.2f}")
            st.write(f"**Seasonality Factor:** {row['seasonality_factor']:.2f}")
        with c3:
            st.write(f"**Stock Level:** {int(row['stock_level'])}")
            st.write(f"**Customer Ratings:** {row['customer_ratings']:.1f}")
            st.write(f"**Return Rate:** {row['return_rate']:.2f}")
        with c4:
            st.write(f"**Optimal Discount:** {row['optimal_discount']:.2f}")
            st.write(f"**Promotion Type:** {row['promotion_type']}")

        # Stage metrics for this product
        prod_metrics = metrics_long[
            (metrics_long["product_name"] == row["product_name"]) &
            (metr
