from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loading import load_markdown_data
from src.markdown_metrics import compute_stage_metrics


def main():
    # ------------------------------------------------------------------
    # Page config
    # ------------------------------------------------------------------
    st.set_page_config(
        page_title="Retail Markdown Optimization Assistant",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🛍️ Retail Markdown Optimization Assistant")

    # ------------------------------------------------------------------
    # Business problem – hero card
    # ------------------------------------------------------------------
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 28px;
            border-radius: 18px;
            color: white;
            box-shadow: 0 12px 30px rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 25px;
        ">
            <h3 style="margin-top: 0;">ℹ️ What problem does this app solve?</h3>

            <p style="font-size: 0.95em;">
                <strong>Business problem</strong><br>
                Retailers often apply discounts without knowing:
            </p>

            <ul style="font-size: 0.9em;">
                <li>How deep to markdown</li>
                <li>Which markdown stage (M1–M4) balances clearance and profit</li>
            </ul>

            <p style="font-size: 0.95em;"><strong>This app helps you answer:</strong></p>

            <ul style="font-size: 0.9em;">
                <li>Which <strong>categories and seasons</strong> respond best to deeper markdowns</li>
                <li>Which <strong>markdown stage</strong> maximizes revenue and sell-through for a product</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df: pd.DataFrame = load_markdown_data()
    metrics_long: pd.DataFrame = compute_stage_metrics(df)

    # ------------------------------------------------------------------
    # Sidebar filters
    # ------------------------------------------------------------------
    st.sidebar.header("Global filters")

    category_options = sorted(df["Category"].unique())
    season_options = sorted(df["Season"].unique())

    selected_categories = st.sidebar.multiselect(
        "Category", category_options, default=category_options
    )
    selected_seasons = st.sidebar.multiselect(
        "Season", season_options, default=season_options
    )

    filtered_df = df[
        df["Category"].isin(selected_categories)
        & df["Season"].isin(selected_seasons)
    ]

    filtered_long = metrics_long[
        metrics_long["Category"].isin(selected_categories)
        & metrics_long["Season"].isin(selected_seasons)
    ]

    # ------------------------------------------------------------------
    # KPI row
    # ------------------------------------------------------------------
    if not filtered_long.empty:
        c1, c2, c3 = st.columns(3)

        stage_rev = (
            filtered_long.groupby("Stage")["Revenue"]
            .sum()
            .reindex(["M1", "M2", "M3", "M4"])
        )

        with c1:
            st.metric("Best markdown stage", stage_rev.idxmax())
        with c2:
            st.metric("Revenue at best stage", f"{stage_rev.max():,.0f}")
        with c3:
            st.metric(
                "Avg optimal discount",
                f"{filtered_df['Optimal Discount'].mean():.0%}",
            )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    tab1, tab2 = st.tabs(
        ["Category / Season dashboard", "Product drill-down"]
    )

    # ==================================================================
    # TAB 1 – CATEGORY / SEASON DASHBOARD
    # ==================================================================
    with tab1:
        st.subheader("Category × Season performance")

        if filtered_long.empty:
            st.info("No data for selected filters.")
            return

        # ---- Revenue table
        st.markdown("### Revenue by markdown stage (per category)")
        rev_by_cat_stage = (
            filtered_long.groupby(["Category", "Stage"], as_index=False)["Revenue"]
            .sum()
        )

        rev_pivot = (
            rev_by_cat_stage.pivot(
                index="Category", columns="Stage", values="Revenue"
            )
            .fillna(0)
            .round(0)
            .astype(int)
        )

        st.dataframe(rev_pivot.style.format("{:,}"), use_container_width=True)

        # ---- Chart
        st.markdown("### Revenue progression across markdown stages")

        chart_cats = st.multiselect(
            "Categories to chart",
            options=category_options,
            default=selected_categories[: min(3, len(selected_categories))],
        )

        if chart_cats:
            chart_data = rev_by_cat_stage[
                rev_by_cat_stage["Category"].isin(chart_cats)
            ].copy()

            chart_data["Revenue_M"] = chart_data["Revenue"] / 1_000_000

            fig = px.bar(
                chart_data,
                x="Stage",
                y="Revenue_M",
                color="Category",
                barmode="stack",
                labels={
                    "Stage": "Markdown stage",
                    "Revenue_M": "Revenue (Millions)",
                },
            )
            fig.update_traces(texttemplate="%{y:.1f}M", textposition="outside")
            fig.update_yaxes(tickformat=".0f")

            st.plotly_chart(fig, use_container_width=True)

            # ---- Dropdown explanation
            with st.expander("📊 How this chart is computed", expanded=False):
                st.markdown(
                    """
                    **Step 1 – Row level**  
                    Revenue = Price × (1 − Markdownᵢ) × Sales_After_Mᵢ

                    **Step 2 – Group**  
                    Sum revenue by **Category** and **Stage**

                    **Step 3 – Plot**  
                    - X-axis: Markdown stage (M1–M4)  
                    - Y-axis: Revenue (Millions)  
                    - Color: Category  

                    **Step 4 – Insight**  
                    Identify which **stage × category** combinations drive the
                    strongest revenue lift.
                    """
                )

        # ---- Season × Category
        st.markdown("---")
        st.subheader("Season × Category total revenue (all stages)")

        heat = (
            filtered_long.groupby(["Category", "Season"], as_index=False)["Revenue"]
            .sum()
        )

        heat_pivot = (
            heat.pivot(index="Category", columns="Season", values="Revenue")
            .fillna(0)
            .round(0)
            .astype(int)
        )

        st.dataframe(heat_pivot.style.format("{:,}"), use_container_width=True)

    # ==================================================================
    # TAB 2 – PRODUCT DRILL-DOWN
    # ==================================================================
    with tab2:
        st.subheader("Product drill-down")

        if filtered_df.empty:
            st.info("No products for selected filters.")
            return

        c1, c2 = st.columns(2)
        with c1:
            sel_cat = st.selectbox(
                "Category", ["All"] + sorted(filtered_df["Category"].unique())
            )
        with c2:
            sel_brand = st.selectbox(
                "Brand", ["All"] + sorted(filtered_df["Brand"].unique())
            )

        prod_df = filtered_df.copy()
        if sel_cat != "All":
            prod_df = prod_df[prod_df["Category"] == sel_cat]
        if sel_brand != "All":
            prod_df = prod_df[prod_df["Brand"] == sel_brand]

        prod_df["label"] = (
            prod_df["Product_Name"]
            + " | "
            + prod_df["Brand"]
            + " | "
            + prod_df["Season"]
        )

        label = st.selectbox("Select product", sorted(prod_df["label"].unique()))
        row = prod_df[prod_df["label"] == label].iloc[0]

        st.markdown("### Markdown performance by stage")

        prod_metrics = metrics_long[
            (metrics_long["Product_Name"] == row["Product_Name"])
            & (metrics_long["Brand"] == row["Brand"])
            & (metrics_long["Season"] == row["Season"])
        ].sort_values("Stage")

        prod_metrics["Revenue $"] = prod_metrics["Revenue"].round(0).astype(int)
        prod_metrics["Markdown %"] = (prod_metrics["Markdown"] * 100).round(1)

        st.dataframe(
            prod_metrics[
                ["Stage", "Markdown %", "Sales", "Revenue $", "Sell_through"]
            ],
            use_container_width=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(prod_metrics.set_index("Stage")[["Revenue $"]])
        with col2:
            st.bar_chart(prod_metrics.set_index("Stage")[["Sales"]])


if __name__ == "__main__":
    main()
