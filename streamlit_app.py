import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Failed to load the dataset: {e}")
    st.stop()

# --------------------------------------------------
# App title
# --------------------------------------------------
st.title("🛍️ Retail Markdown Optimization Assistant")
st.markdown("### *Data-Driven Discount Strategy for Maximum Profitability*")

# --------------------------------------------------
# Problem statement - Collapsible
# --------------------------------------------------
show_info = st.checkbox("ℹ️ Show Problem Statement", value=False)

if show_info:
    st.info("""
    **The Challenge:** Every month, retailers struggle to decide which products to discount and by how much. 
    Too little discount means unsold inventory. Too much discount erodes profit margins.
    
    **The Solution:** This tool analyzes historical markdown performance to recommend the optimal discount strategy 
    for each product, maximizing both revenue and inventory clearance.
    """)

st.divider()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filters")

categories = sorted(df["Category"].unique())
seasons = sorted(df["Season"].unique())
brands = sorted(df["Brand"].unique())

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

selected_brands = st.sidebar.multiselect(
    "Brand",
    brands,
    default=brands[:3] if len(brands) > 3 else brands
)

# Filter data
filtered_df = df[
    df["Category"].isin(selected_categories) &
    df["Season"].isin(selected_seasons) &
    df["Brand"].isin(selected_brands)
].copy()

if len(filtered_df) == 0:
    st.warning("⚠️ No data matches the selected filters. Please adjust your filters.")
    st.stop()

# --------------------------------------------------
# Reshape data for markdown analysis
# --------------------------------------------------
markdown_data = []
for _, row in filtered_df.iterrows():
    for i in range(1, 5):
        markdown_col = f"Markdown_{i}"
        sales_col = f"Sales_After_M{i}"
        
        if markdown_col in row and sales_col in row:
            revenue = row["Original_Price"] * (1 - row[markdown_col]) * row[sales_col]
            markdown_data.append({
                "Product_ID": row["Product_ID"],
                "Category": row["Category"],
                "Season": row["Season"],
                "Brand": row["Brand"],
                "Stage": f"M{i}",
                "Markdown": row[markdown_col],
                "Sales": row[sales_col],
                "Revenue": revenue,
                "Original_Price": row["Original_Price"]
            })

markdown_df = pd.DataFrame(markdown_data)
best_per_product = markdown_df.loc[markdown_df.groupby("Product_ID")["Revenue"].idxmax()]

# --------------------------------------------------
# Executive Summary KPIs
# --------------------------------------------------
st.subheader("📊 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = best_per_product["Revenue"].sum()
    st.metric("💰 Revenue Potential", f"${total_revenue/1e6:.1f}M")

with col2:
    avg_optimal_discount = best_per_product["Markdown"].mean() * 100
    st.metric("🎯 Optimal Discount", f"{avg_optimal_discount:.1f}%")

with col3:
    products_analyzed = len(best_per_product)
    st.metric("📦 Products", f"{products_analyzed:,}")

with col4:
    historical_sales = filtered_df["Historical_Sales"].mean()
    optimal_sales = best_per_product["Sales"].mean()
    sales_lift = ((optimal_sales / historical_sales) - 1) * 100
    st.metric("📈 Sales Lift", f"+{sales_lift:.1f}%")

st.divider()

# --------------------------------------------------
# MAIN TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📖 Story & Insights", 
    "📊 Performance Analysis",
    "🎯 Product Recommendations",
    "🔍 Deep Dive Analysis"
])

# ==================== TAB 1: STORY & INSIGHTS ====================
with tab1:
    st.header("📖 The Markdown Story: A Data-Driven Journey")
    
    st.markdown("---")
    
    # Act 1
    st.markdown("### 🎬 **Act 1: The Current Situation**")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        **Where We Are Today:**
        
        Your retail team manages thousands of products across multiple categories. Each month, decisions about 
        discounting are made manually,
