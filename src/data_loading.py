from pathlib import Path
import pandas as pd

def load_markdown_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "SYNTHETIC Markdown Dataset.csv"
    return pd.read_csv(csv_path)
