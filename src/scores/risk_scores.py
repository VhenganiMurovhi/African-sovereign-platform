import pandas as pd
import numpy as np
from pathlib import Path

from src.modelling.market_risk import calculate_market_risk

INPUT_FILE = Path("data/processed/country_macro_panel.csv")
OUTPUT_FILE = Path("data/processed/country_risk_scores.csv")

RISK_COLUMNS = {
    "debt_to_gdp": ("high_bad", 0.22, "debt_sustainability"),
    "inflation": ("high_bad", 0.18, "macro_stability"),
    "imports_to_gdp": ("high_bad", 0.12, "external_vulnerability"),
    "unemployment": ("high_bad", 0.13, "growth_capacity"),
    "gdp_growth": ("high_good", 0.15, "growth_capacity"),
    "electricity_access": ("high_good", 0.10, "development_capacity"),
    "fdi_pct_gdp": ("high_good", 0.10, "external_vulnerability"),
}

PILLAR_NAMES = [
    "debt_sustainability",
    "macro_stability",
    "external_vulnerability",
    "growth_capacity",
    "development_capacity",
]


def min_max_scale(series: pd.Series, reverse: bool = False) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce")

    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series(np.nan, index=series.index)

    scaled = (series - min_val) / (max_val - min_val)

    if reverse:
        scaled = 1 - scaled

    return scaled * 100


def assign_risk_band(score: float) -> str:
    if pd.isna(score):
        return "Unknown"
    if score <= 33:
        return "Low Risk"
    elif score <= 66:
        return "Moderate Risk"
    return "High Risk"


def weighted_average_from_available(row, items, min_weight_required=0.30):
    weighted_sum = 0
    weight_sum = 0

    for score_col, weight in items:
        value = row.get(score_col)
        if pd.notna(value):
            weighted_sum += value * weight
            weight_sum += weight

    if weight_sum < min_weight_required:
        return np.nan

    return weighted_sum / weight_sum


def calculate_scores():
    df = pd.read_csv(INPUT_FILE)

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    score_columns_with_weights = []
    pillar_map = {pillar: [] for pillar in PILLAR_NAMES}

    # Fundamental risk scaling
    for col, (direction, weight, pillar) in RISK_COLUMNS.items():
        if col not in df.columns:
            df[col] = np.nan

        reverse = direction == "high_good"
        score_col = f"{col}_score"

        df[score_col] = min_max_scale(df[col], reverse=reverse)

        score_columns_with_weights.append((score_col, weight))
        pillar_map[pillar].append((score_col, weight))

    # Pillar scores
    for pillar, items in pillar_map.items():
        df[pillar] = df.apply(
            lambda row: weighted_average_from_available(row, items, min_weight_required=0.05),
            axis=1
        )

    # Fundamental sovereign risk score
    df["sovereign_risk_score"] = df.apply(
        lambda row: weighted_average_from_available(row, score_columns_with_weights, min_weight_required=0.40),
        axis=1
    )

    # Fundamental risk band
    df["risk_band"] = df["sovereign_risk_score"].apply(assign_risk_band)

    
    # Add market-implied risk layer
    
    df = calculate_market_risk(df)


    # Composite risk score = 70% fundamental + 30% market
    df["composite_risk_score"] = np.where(
        df["sovereign_risk_score"].notna() & df["market_risk_score"].notna(),
        df["sovereign_risk_score"] * 0.70 + df["market_risk_score"] * 0.30,
        np.nan
    )

    df["composite_risk_band"] = df["composite_risk_score"].apply(assign_risk_band)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved risk scores to {OUTPUT_FILE}")
    print(
        df[
            [
                "country_name",
                "year",
                "sovereign_risk_score",
                "market_risk_score",
                "composite_risk_score",
                "risk_band",
                "composite_risk_band",
            ]
        ].tail(20)
    )


if __name__ == "__main__":
    calculate_scores()