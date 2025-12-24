import streamlit as st
import pandas as pd
from pathlib import Path


# ---------- Data loading ----------

@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "SYNTHETIC Markdown Dataset.csv"
    df = pd.read_csv(csv_path)
    return df


# ---------- Helper functions ----------

def compute_stage_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row, compute revenue and sell-through at M1..M4.
    Returns a long-format DataFrame with columns:
    Category, Season, Stage, Markdown, Sales, Revenue, Sell_through.
    """
    records = []

    for _, row in df.iterrows():
        stock = row["Stock_Level"]
        for stage, md_col, sales_col in [
            ("M1", "Markdown_1", "Sales_After_M1"),
            ("M2", "Markdown_2", "Sales_After_M2"),
            ("M3", "Markdown_3", "Sales_After_M3"),
            ("M4", "Markdown_4", "Sales_After_M4"),
        ]:
            markdown = row[md_col]
            sales = row[sales_col]
            price_after = row["Original_Price"] * (1 - markdown)
            revenue = price_after * sales
            sell_through = sales / stock if stock > 0 else 0.0

            records.append(
                {
                    "Category": row["Category"],
                    "Season": row["Season"],
                    "Product_Name": row["Product_Name"],
                    "Stage": stage,
                    "Markdown": markdown,
                    "Sales": sales,
                    "Revenue": revenue,
                    "Sell_through": sell_through,
                }
            )

    return pd.DataFrame(records)


# ---------- App ----------

def main():
    st.set_page_config(
        page_title="Retail Markdown Optimization Assistant",
        layout="wide",
    )

    st.title("Retail Markdown Optimization Assistant")
    st.caption(
        "Understand how markdown levels affect sales and revenue by category and "
        "season, then drill down to individual products."
    )

    df = load_data()
    metrics_long = compute_stage_metrics(df)

    # Sidebar filters used on both tabs
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
        df["Category"].isin(selected_categories) & df["Season"].isin(selected_seasons)
    ].copy()
    filtered_long = metrics_long[
        (metrics_long["Category"].isin(selected_categories)) &
        (metrics_long["Season"].isin(selected_seasons))
    ].copy()

    tab1, tab2 = st.tabs(["Category / Season Dashboard", "Product Drill‑down"])

    # -------------------------------------------------------------------------
    # TAB 1: Category / Season Dashboard
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Category and Season overview")

        if filtered_long.empty:
            st.info("No data for the selected filters.")
        else:
            # Aggregate revenue and sales by Category, Season, Stage
            agg = (
                filtered_long
                .groupby(["Category", "Season", "Stage"], as_index=False)[
                    ["Sales", "Revenue", "Sell_through"]
                ]
                .sum()
            )

            # Pivot: revenue by stage for each category (summed across seasons)
            st.markdown("### Revenue by markdown stage (per category)")
            rev_by_cat_stage = (
                filtered_long
                .groupby(["Category", "Stage"], as_index=False)["Revenue"]
                .sum()
            )
            rev_pivot = rev_by_cat_stage.pivot(
                index="Category", columns="Stage", values="Revenue"
            ).fillna(0)
            st.dataframe(rev_pivot.style.format("{:,.0f}"))

            # Simple bar chart: pick a few categories and show revenue per stage
            st.markdown("#### Chart: revenue per stage for selected categories")
            chart_cats = st.multiselect(
                "Categories to plot",
                options=category_options,
                default=selected_categories[:3] if selected_categories else [],
            )
            if chart_cats:
                chart_df = rev_by_cat_stage[rev_by_cat_stage["Category"].isin(chart_cats)]
                chart_df = chart_df.pivot(
                    index="Stage", columns="Category", values="Revenue"
                )
                st.bar_chart(chart_df)
            else:
                st.info("Select at least one category to show the chart.")

            st.markdown("---")

            # Season x Category heatmap-like table
            st.subheader("Season vs Category: total revenue (all stages combined)")
            heat = (
                filtered_long
                .groupby(["Category", "Season"], as_index=False)["Revenue"]
                .sum()
            )
            heat_pivot = heat.pivot(
                index="Category", columns="Season", values="Revenue"
            ).fillna(0)
            st.dataframe(heat_pivot.style.format("{:,.0f}"))

            st.markdown("#### Interpretation hints")
            st.write(
                "- Look for categories where revenue grows strongly from M1 → M4; "
                "those are more responsive to deeper discounts."
            )
            st.write(
                "- Compare seasons to see when each category generates the most "
                "markdown revenue (e.g., Skincare in Winter vs Summer)."
            )

    # -------------------------------------------------------------------------
    # TAB 2: Product Drill‑down
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Product Drill‑down (by name)")

        if filtered_df.empty:
            st.info("No products for the selected filters.")
            return

        # Select product by name within filtered set
        product_names = sorted(filtered_df["Product_Name"].unique().tolist())
        selected_name = st.selectbox("Select product name", options=product_names)

        prod_rows = filtered_df[filtered_df["Product_Name"] == selected_name]
        row = prod_rows.iloc[0]

        # Product info in horizontal layout
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

        # Build per-stage metrics for this product from long table
        prod_long = filtered_long[
            (filtered_long["Product_Name"] == selected_name)
        ].copy()

        md_sales_df = (
            prod_long[["Stage", "Markdown", "Sales", "Revenue", "Sell_through"]]
            .sort_values("Stage")
            .reset_index(drop=True)
        )

        st.markdown("### Markdown performance by stage")
        st.dataframe(md_sales_df)

        # Identify best stages
        best_rev_stage = md_sales_df.loc[md_sales_df["Revenue"].idxmax(), "Stage"]
        best_sell_stage = md_sales_df.loc[
            md_sales_df["Sell_through"].idxmax(), "Stage"
        ]

        st.markdown("### Sales and revenue by markdown stage")
        chart_df = md_sales_df.set_index("Stage")[["Sales", "Revenue"]]
        st.bar_chart(chart_df)

        st.markdown("### Interpretation")
        st.write(
            f"- **Best revenue stage** for this product: **{best_rev_stage}** "
            "(highest total revenue among M1–M4)."
        )
        st.write(
            f"- **Best sell-through stage** (stock clearance): **{best_sell_stage}** "
            "(highest fraction of stock sold)."
        )
        st.write(
            "When both best stages are the deepest markdown (M4), it implies that this "
            "product benefits from aggressive markdowns in terms of both revenue and "
            "inventory clearance within the tested range."
        )


if __name__ == "__main__":
    main()

