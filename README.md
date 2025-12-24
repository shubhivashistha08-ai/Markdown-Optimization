# Retail Markdown Optimization Assistant

This project uses a synthetic markdown dataset from Kaggle to:
- Recommend an **optimal markdown percentage** for each product.
- Visualize how sales and revenue change across different markdown levels.

## Dataset

- `data/SYNTHETIC-Markdown-Dataset.csv` [file:64]  
  Columns include:
  - Product, category, brand, season.
  - Original and competitor prices.
  - Markdown_1..4 and Sales_After_M1..4.
  - Stock level, promotion type, ratings, return rate.
  - **Optimal Discount** (synthetic target). [file:64]

## Planned Features

- Streamlit app with:
  - Product explorer & EDA.
  - Markdown recommendation (model on `Optimal Discount`).
  - Markdown vs sales & revenue simulator.

## How to run

