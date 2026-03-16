
import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/raw/world_bank_raw.csv")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_world_bank_data():
    df = pd.read_csv(RAW_FILE)

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = df.dropna(subset=["year"])
    df = df[df["year"] >= 2010]

    pivot_df = df.pivot_table(
        index=["country_code", "country_name", "year"],
        columns="indicator",
        values="value",
        aggfunc="mean"
    ).reset_index()

    pivot_df.columns.name = None

    output_file = PROCESSED_DIR / "country_macro_panel.csv"
    pivot_df.to_csv(output_file, index=False)

    print(f"Saved cleaned dataset to {output_file}")
    print(pivot_df.head())


if __name__ == "__main__":
    clean_world_bank_data()