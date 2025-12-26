import pandas as pd

def compute_stage_metrics(df: pd.DataFrame) -> pd.DataFrame:
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

            records.append({
                "Category": row["Category"],
                "Season": row["Season"],
                "Product_Name": row["Product_Name"],
                "Brand": row["Brand"],
                "Stage": stage,
                "Markdown": markdown,
                "Sales": sales,
                "Revenue": revenue,
                "Sell_through": sell_through,
            })
    return pd.DataFrame(records)
