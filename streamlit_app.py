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
    
    # Story Timeline
    st.markdown("---")
    
    # Step 1
    st.markdown("### 🎬 **Act 1: The Current Situation**")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
**Where We Are Today:**

Your retail team manages thousands of products across multiple categories. Each month, decisions about
discounting are made manually, often leading to:

- 🔴 **Over-discounting** → Lost profit margins
- 🔴 **Under-discounting** → Excess inventory and missed sales
- 🔴 **Inconsistent strategy** → No clear framework for markdown decisions

The cost of these inefficiencies? Potentially **millions in lost revenue** annually.
""")
    
    with col2:
        # Current state metrics
        baseline_revenue = filtered_df["Original_Price"].sum() * filtered_df["Historical_Sales"].mean()
        potential_revenue = best_per_product["Revenue"].sum()
        revenue_gap = potential_revenue - baseline_revenue
        
        st.markdown(f"""
<div style="background-color: #2d1b1b; padding: 20px; border-radius: 10px; border-left: 4px solid #FF6B6B;">
<h4 style="color: white; margin-bottom: 15px;">⚠️ Opportunity Gap</h4>
<p style="color: #cccccc; font-size: 16px; margin-bottom: 10px;">
<strong style="color: white;">Potential Revenue Increase:</strong><br>
<span style="font-size: 28px; color: #FF6B6B;">${revenue_gap/1e6:.1f}M</span>
</p>
<p style="color: #cccccc; font-size: 14px;">
This is what we're leaving on the table with suboptimal markdown strategies.
</p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Step 2
    st.markdown("### 💡 **Act 2: The Discovery**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
**What The Data Reveals:**

Our analysis of historical markdown performance uncovered three critical insights:
""")
        
        # Find best performing category
        category_revenue = best_per_product.groupby("Category")["Revenue"].sum()
        best_category = category_revenue.idxmax()
        
        # Find best stage
        stage_totals = markdown_df.groupby("Stage")["Revenue"].sum()
        best_stage = stage_totals.idxmax()
        
        # Calculate average optimal discount range
        discount_range = best_per_product["Markdown"].quantile([0.25, 0.75]) * 100
        
        st.markdown(f"""
**1️⃣ Not All Categories Are Created Equal**
- **{best_category}** products generate the highest revenue with optimized markdowns
- Different categories respond differently to discount depths

**2️⃣ Timing Matters**
- Stage **{best_stage}** consistently delivers the best revenue performance
- Early or late markdowns can hurt profitability

**3️⃣ The Sweet Spot**
- Optimal discounts typically fall between **{discount_range[0.25]:.0f}% - {discount_range[0.75]:.0f}%**
- Going deeper doesn't always mean more sales or revenue
""")
    
    with col2:
        # Best stage performance chart
        stage_revenue_df = markdown_df.groupby("Stage")["Revenue"].sum().reset_index()
        fig = px.bar(
            stage_revenue_df,
            x="Stage",
            y="Revenue",
            title="💰 Revenue Performance by Markdown Stage",
            color="Revenue",
            color_continuous_scale=["#45B7D1", "#4ECDC4", "#FFB800", "#FF6B6B"],
            text_auto='.2s'
        )
        fig.update_traces(texttemplate='$%{text}', textposition='outside')
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Step 3
    st.markdown("### 🎯 **Act 3: The Path Forward**")
    
    st.markdown("""
**Recommended Action Plan:**

Based on data analysis, here's your roadmap to optimized markdown strategy:
""")
    
    # Create action plan boxes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
<div style="background-color: #1b2d1b; padding: 20px; border-radius: 10px; border-top: 4px solid #4ECDC4;">
<h4 style="color: white;">📅 Week 1-2</h4>
<p style="color: #cccccc; font-size: 14px;">
<strong style="color: white;">Review & Prioritize</strong><br><br>
• Identify high-impact products<br>
• Set category-specific targets<br>
• Align with inventory goals
</p>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
<div style="background-color: #1b1b2d; padding: 20px; border-radius: 10px; border-top: 4px solid #45B7D1;">
<h4 style="color: white;">📅 Week 3-4</h4>
<p style="color: #cccccc; font-size: 14px;">
<strong style="color: white;">Test & Learn</strong><br><br>
• Implement optimal discounts<br>
• Monitor daily performance<br>
• Adjust based on early signals
</p>
</div>
""", unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
<div style="background-color: #2d1b2d; padding: 20px; border-radius: 10px; border-top: 4px solid #FFB800;">
<h4 style="color: white;">📅 Month 2+</h4>
<p style="color: #cccccc; font-size: 14px;">
<strong style="color: white;">Scale & Optimize</strong><br><br>
• Roll out winning strategies<br>
• Refine discount rules<br>
• Build predictive models
</p>
</div>
""", unsafe_allow_html=True)

# ==================== TAB 2: PERFORMANCE ANALYSIS ====================
with tab2:
    st.header("📊 Performance Analysis")
    
    # Revenue by Stage
    st.subheader("💵 Revenue Performance Across Markdown Stages")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        revenue_by_stage = markdown_df.groupby(["Stage", "Category"])["Revenue"].sum().reset_index()
        
        # CHART 1: Revenue by Markdown Stage and Category (NO DATA LABELS)
        fig = px.bar(
            revenue_by_stage,
            x="Stage",
            y="Revenue",
            color="Category",
            title="Revenue by Markdown Stage and Category",
            barmode="group",
            color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"],
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        stage_totals = markdown_df.groupby("Stage")["Revenue"].sum()
        best_stage = stage_totals.idxmax()
        
        st.markdown(f"""
<div style="background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            height: 360px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            border: 1px solid #333;">
<h3 style="color: white; margin-bottom: 20px;">📊 Key Insights</h3>
<ul style="color: white; font-size: 16px; line-height: 2;">
<li><strong>Best Overall Stage:</strong> {best_stage}</li>
<li><strong>Total Revenue:</strong> ${stage_totals[best_stage]:,.0f}</li>
</ul>
<p style="color: #cccccc; margin-top: 20px; font-size: 14px;">
The optimal markdown stage varies by category and product. Use the chart to identify patterns.
</p>
</div>
""", unsafe_allow_html=True)
    
    st.divider()
    
    # Category Performance
    st.subheader("🏆 Category Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_revenue = best_per_product.groupby("Category")["Revenue"].sum().reset_index()
        category_revenue = category_revenue.sort_values("Revenue", ascending=False)
        
        fig = px.pie(
            category_revenue,
            values="Revenue",
            names="Category",
            title="Revenue Distribution by Category",
            color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"],
            hole=0.4
        )
        fig.update_traces(textposition='outside', textinfo='percent+label+value',
                         texttemplate='%{label}<br>%{percent:.1%}<br>$%{value:.2s}')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        category_discount = best_per_product.groupby("Category")["Markdown"].mean().reset_index()
        category_discount["Markdown"] = category_discount["Markdown"] * 100
        category_discount = category_discount.sort_values("Markdown", ascending=False)
        
        # CHART 2: Average Optimal Discount by Category (NO DATA LABELS)
        fig = px.bar(
            category_discount,
            x="Category",
            y="Markdown",
            title="Average Optimal Discount by Category",
            color="Markdown",
            color_continuous_scale=["#00D9FF", "#FFB800", "#FF6B6B"],
        )
        fig.update_layout(height=400, yaxis_title="Discount (%)", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Seasonal Analysis
    st.subheader("🌤️ Seasonal Performance Trends")
    
    season_stage = markdown_df.groupby(["Season", "Stage"])["Revenue"].sum().reset_index()
    
    fig = px.line(
        season_stage,
        x="Stage",
        y="Revenue",
        color="Season",
        markers=True,
        title="How Season Impacts Markdown Performance",
        color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFB800"],
        text="Revenue"
    )
    fig.update_traces(texttemplate='$%{text:.2s}', textposition='top center')
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 3: PRODUCT RECOMMENDATIONS ====================
with tab3:
    st.header("🎯 Product-Level Recommendations")
    
    st.markdown("""
This table shows the **top 30 products** with the highest revenue potential when discounted optimally.
Use this to prioritize which products to markdown first.
""")
    
    # Show top products
    top_products = best_per_product.nlargest(30, "Revenue")[
        ["Product_ID", "Category", "Season", "Brand", "Stage", "Markdown", "Revenue"]
    ].copy()
    
    top_products["Optimal Discount %"] = (top_products["Markdown"] * 100).round(1)
    top_products["Expected Revenue"] = top_products["Revenue"].round(0)
    
    # Add recommendation column
    def get_recommendation(row):
        if row["Stage"] in ["M1", "M2"]:
            return "✅ Early Markdown"
        elif row["Stage"] == "M3":
            return "⭐ Sweet Spot"
        else:
            return "⚠️ Deep Discount"
    
    top_products["Strategy"] = top_products.apply(get_recommendation, axis=1)
    
    st.dataframe(
        top_products[["Product_ID", "Category", "Season", "Brand", "Strategy", "Stage", "Optimal Discount %", "Expected Revenue"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Expected Revenue": st.column_config.NumberColumn(
                "Expected Revenue",
                format="$%.0f"
            ),
            "Optimal Discount %": st.column_config.NumberColumn(
                "Optimal Discount",
                format="%.1f%%"
            )
        }
    )
    
    # Download option
    csv = best_per_product.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Product Recommendations (CSV)",
        data=csv,
        file_name="markdown_recommendations.csv",
        mime="text/csv"
    )

# ==================== TAB 4: DEEP DIVE ====================
with tab4:
    st.header("🔍 Deep Dive Analysis")
    
    # Discount effectiveness by range
    st.subheader("📉 Discount Effectiveness by Range")
    
    st.markdown("""
This analysis shows how revenue changes as discount depth increases.
The goal is to find the "sweet spot" where discounts drive sales without eroding too much margin.
""")
    
    # Create discount bins
    markdown_df["Discount_Range"] = pd.cut(
        markdown_df["Markdown"] * 100,
        bins=[0, 15, 20, 25, 30, 35, 40, 50],
        labels=["10-15%", "15-20%", "20-25%", "25-30%", "30-35%", "35-40%", "40-50%"]
    )
    
    discount_analysis = markdown_df.groupby(["Discount_Range", "Category"]).agg({
        "Revenue": "sum",
        "Sales": "sum",
        "Product_ID": "count"
    }).reset_index()
    
    discount_analysis.columns = ["Discount_Range", "Category", "Revenue", "Sales", "Product_Count"]
    
    # CHART 3: Revenue by Discount Range and Category (NO DATA LABELS)
    fig = px.bar(
        discount_analysis,
        x="Discount_Range",
        y="Revenue",
        color="Category",
        title="Revenue by Discount Range and Category",
        barmode="group",
        color_discrete_sequence=["#FF6B6B", "#4ECDC4", "#45B7D1"],
    )
    fig.update_layout(height=400, xaxis_title="Discount Range", yaxis_title="Total Revenue")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Brand performance comparison
    st.subheader("🏢 Brand Performance Comparison")
    
    brand_performance = best_per_product.groupby("Brand").agg({
        "Revenue": "sum",
        "Markdown": "mean",
        "Product_ID": "count"
    }).reset_index()
    
    brand_performance["Avg_Discount"] = (brand_performance["Markdown"] * 100).round(1)
    brand_performance = brand_performance.sort_values("Revenue", ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            brand_performance.head(10),
            x="Brand",
            y="Revenue",
            title="Top 10 Brands by Revenue Potential",
            color="Revenue",
            color_continuous_scale="Viridis",
            text_auto='.2s'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.scatter(
            brand_performance,
            x="Avg_Discount",
            y="Revenue",
            size="Product_ID",
            color="Brand",
            title="Brand Strategy: Discount vs Revenue",
            labels={"Avg_Discount": "Average Optimal Discount (%)", "Product_ID": "Products"},
            hover_data=["Brand", "Product_ID"]
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.caption("Built with Streamlit • Retail Markdown Optimization Assistant")
st.caption(f"📊 Analyzing {len(filtered_df)} products across {len(selected_categories)} categories")
