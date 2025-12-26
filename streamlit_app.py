import streamlit as st
import plotly.express as px
import pandas as pd

from src.data_loading import load_markdown_data
from src.markdown_metrics import compute_stage_metrics


def main():
    st.set_page_config(
        page_title="Retail Markdown Optimization Assistant",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Retail Markdown Optimization Assistant")

    # --- Problem statement / intro for newcomers ---
    with st.expander("ℹ️ What problem does this app solve?", expanded=True):
        st.markdown(
            """
            **Business problem**

            Retailers often apply discounts without knowing **how deep** to markdown
            or **which stage** (M1–M4) gives the best balance between:

            - Clearing seasonal or slow-moving stock  
            - Protecting profit margin

            This app helps you answer:

            - Which **categories and seasons** respond best to deeper markdowns?
            - For a given product, which **markdown stage** maximizes
              **revenue** and **sell-through**?
            """
        )

    # Optional usage guide
    show_help = st.checkbox("Show quick usage guide", value=False)
    if show_help:
        st.markdown("### How to use this app")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                **Step 1 – Filter context**  
                Use the left sidebar to pick:
                - Category  
                - Season  
                """
            )
        with c2:
            st.markdown(
                """
                **Step 2 – See high‑level impact**  
                In the *Category/Season dashboard* tab:
                - Compare **revenue by markdown stage (M1–M4)** per category.  
                - Check which **Season × Category** pairs generate most markdown revenue.
                """
            )
        with c3:
            st.markdown(
                """
                **Step 3 – Drill into a product**  
                In the *Product drill‑down* tab:
                - Choose a product by **Category → Brand → Name**.  
                - Review **sales, revenue, and sell‑through** at each markdown stage.
                """
            )

    # --- Load data & precomputed metrics ---
    df: pd.DataFrame = load_markdown_data()
    metrics_long: pd.DataFrame = compute_stage_metrics(df)

    # ---------- Global sidebar filters ----------
    st.sidebar.header("Global filters")

    category_options = sorted(df["Category"].unique().tolist())
    season_options = sorted(df["Season"].unique().tolist())

    selected_categories = st.sidebar.multiselect(
        "Category", options=category_options, default=category_options
    )
    selected_seasons = st.sidebar.multiselect(
        "Season", options=season_options, default=season_options
    )

    filtered_df = df[
        df["Category"].isin(selected_categories)
        & df["Season"].isin(selected_seasons)
    ].copy()
    filtered_long = metrics_long[
        (metrics_long["Category"].isin(selected_categories))
        & (metrics_long["Season"].isin(selected_seasons))
    ].copy()

    # ---------- Dynamic highlight metrics ----------
    if not filtered_long.empty and not filtered_df.empty:
        k1, k2, k3 = st.columns(3)

        stage_rev = (
            filtered_long.groupby("Stage")["Revenue"]
            .sum()
            .reindex(["M1", "M2", "M3", "M4"])
        )
        best_stage = stage_rev.idxmax()
        best_stage_rev = stage_rev.max()

        avg_opt_disc = filtered_df["Optimal Discount"].mean()

        with k1:
            st.metric(
                "Best markdown stage (revenue)",
                best_stage,
                help="Stage with highest total revenue for the current filters.",
            )
        with k2:
            st.metric(
                "Revenue at best stage",
                f"{best_stage_rev:,.0f}",
            )
        with k3:
            st.metric(
                "Avg optimal discount (filtered)",
                f"{avg_opt_disc:.0%}",
            )

    st.markdown("---")

    # ---------- Tabs ----------
    tab1, tab2 = st.tabs(["Category/Season dashboard", "Product drill‑down"])

    # -------------------------------------------------------------------------
    # TAB 1: Category / Season Dashboard
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Category × Season performance")

        if filtered_long.empty:
            st.info("No data for the selected filters.")
        else:
            # Revenue by Category & Stage (table)
            st.markdown("### Revenue by markdown stage (per category)")
            rev_by_cat_stage = (
                filtered_long.groupby(["Category", "Stage"], as_index=False)["Revenue"]
                .sum()
            )
            rev_pivot = (
                rev_by_cat_stage.pivot(index="Category", columns="Stage", values="Revenue")
                .fillna(0)
                .round(0)
                .astype(int)
            )
            st.dataframe(rev_pivot.style.format("{:,}"), use_container_width=True)

            # Chart: revenue per stage for selected categories (Y axis in millions)
            st.markdown("#### Revenue progression across stages")
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
                        "Category": "Category",
                    },
                )
                fig.update_yaxes(tickformat=".0f")
                fig.update_traces(
                    texttemplate="%{y:.1f}M",
                    textposition="outside",
                )

                st.plotly_chart(fig, use_container_width=True)

                st.markdown("##### How this chart is computed")
                st.markdown(
                    """
                    1️⃣ **Row level:** For each product and markdown stage M1–M4, compute  
                    &nbsp;&nbsp;&nbsp;&nbsp;`Revenue = Original_Price × (1 − Markdown_i) × Sales_After_Mi`. [file:64]

                    2️⃣ **Group:** Sum revenue by **Category** and **Stage** to get total
                    revenue per category at each markdown stage. [file:64]

                    3️⃣ **Plot:** X‑axis = Stage (M1–M4), Y‑axis = total revenue in **millions**, color = Category, value labels on each stack.
                    """
                )
            else:
                st.info("Select at least one category to see the chart.")

            st.markdown("---")

            # Season × Category total revenue
            st.subheader("Season × Category: total revenue (all stages)")
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

    # -------------------------------------------------------------------------
    # TAB 2: Product Drill‑down (by name, not ID)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Product drill‑down (by name)")

        if filtered_df.empty:
            st.info("No products for the selected filters.")
            return

        # Step 1: product-level filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sel_cat = st.selectbox(
                "Category", ["All"] + sorted(filtered_df["Category"].unique())
            )
        with col_f2:
            sel_brand = st.selectbox(
                "Brand", ["All"] + sorted(filtered_df["Brand"].unique())
            )

        prod_subset = filtered_df.copy()
        if sel_cat != "All":
            prod_subset = prod_subset[prod_subset["Category"] == sel_cat]
        if sel_brand != "All":
            prod_subset = prod_subset[prod_subset["Brand"] == sel_brand]

        if prod_subset.empty:
            st.info("No products after applying category/brand filters.")
            return

        # Step 2: friendly labels "Product_Name | Brand | Season"
        prod_subset = prod_subset.copy()
        prod_subset["product_label"] = (
            prod_subset["Product_Name"] + " | "
            + prod_subset["Brand"] + " | "
            + prod_subset["Season"]
        )

        labels = sorted(prod_subset["product_label"].unique().tolist())
        selected_label = st.selectbox("Select product", options=labels)

        row = prod_subset[prod_subset["product_label"] == selected_label].iloc[0]

        # Product info (horizontal)
        st.markdown("### Product info")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write(f"**Name**: {row['Product_Name']}")
            st.write(f"**Category**: {row['Category']}")
            st.write(f"**Brand**: {row['Brand']}")
            st.write(f"**Season**: {row['Season']}")
        with c2:
            st.write(f"**Original price**: {row['Original_Price']:.2f}")
            st.write(f"**Competitor price**: {row['Competitor_Price']:.2f}")
            st.write(f"**Seasonality factor**: {row['Seasonality_Factor']:.2f}")
        with c3:
            st.write(f"**Stock level**: {int(row['Stock_Level'])}")
            st.write(f"**Customer rating**: {row['Customer Ratings']:.1f}")
            st.write(f"**Return rate**: {row['Return Rate']:.2f}")
        with c4:
            st.write(f"**Optimal discount (label)**: {row['Optimal Discount']:.2f}")
            st.write(f"**Promotion type**: {row['Promotion_Type']}")

        st.markdown("---")

        # Stage metrics for this product
        prod_metrics = metrics_long[
            (metrics_long["Product_Name"] == row["Product_Name"])
            & (metrics_long["Brand"] == row["Brand"])
            & (metrics_long["Season"] == row["Season"])
        ][["Stage", "Markdown", "Sales", "Revenue", "Sell_through"]].copy()

        prod_metrics = prod_metrics.sort_values("Stage").reset_index(drop=True)
        prod_metrics["Markdown %"] = (prod_metrics["Markdown"] * 100).round(1)
        prod_metrics["Revenue $"] = prod_metrics["Revenue"].round(0).astype(int)

        st.markdown("### Markdown performance by stage")
        st.dataframe(
            prod_metrics[["Stage", "Markdown %", "Sales", "Revenue $", "Sell_through"]],
            use_container_width=True,
        )

        # Charts
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Revenue by stage")
            st.bar_chart(prod_metrics.set_index("Stage")[["Revenue $"]])
        with col_c2:
            st.markdown("#### Sales by stage")
            st.bar_chart(prod_metrics.set_index("Stage")[["Sales"]])

        # Best stages
        best_rev_stage = prod_metrics.loc[prod_metrics["Revenue"].idxmax(), "Stage"]
        best_sell_stage = prod_metrics.loc[prod_metrics["Sell_through"].idxmax(), "Stage"]

        st.markdown("### Interpretation")
        st.write(
            f"- **Best revenue stage**: {best_rev_stage} "
            "(highest total revenue among markdown levels)."
        )
        st.write(
            f"- **Best sell-through stage**: {best_sell_stage} "
            "(highest fraction of stock sold)."
        )


if __name__ == "__main__":
    main()
