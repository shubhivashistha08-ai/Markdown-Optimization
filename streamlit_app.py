import streamlit as st
import pandas as pd
from pathlib import Path

DATA_PATH = "data/SYNTHETIC-Markdown-Dataset.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    return df

def main():
    st.title("Retail Markdown Optimization Assistant")

    df = load_data()

    st.sidebar.header("Filters")
    category = st.sidebar.selectbox(
        "Category",
        options=["All"] + sorted(df["Category"].unique().tolist())
    )
    season = st.sidebar.selectbox(
        "Season",
        options=["All"] + sorted(df["Season"].unique().tolist())
    )

    filtered = df.copy()
    if category != "All":
        filtered = filtered[filtered["Category"] == category]
    if season != "All":
        filtered = filtered[filtered["Season"] == season]

    st.subheader("Markdown dataset preview")
    st.write(filtered.head())

    st.subheader("Markdown vs Sales (M1)")
    st.scatter_chart(
        filtered[["Markdown_1", "Sales_After_M1"]].rename(
            columns={"Markdown_1": "x", "Sales_After_M1": "y"}
        )
    )

if __name__ == "__main__":
    main()
