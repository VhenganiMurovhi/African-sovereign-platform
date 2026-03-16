
import os
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")

FX_CACHE_DIR = Path("data/raw/fx")
FX_CACHE_DIR.mkdir(parents=True, exist_ok=True)

CURRENCY_MAP = {
    "South Africa": "ZAR",
    "Nigeria": "NGN",
    "Kenya": "KES",
    "Egypt": "EGP",
    "Ghana": "GHS",
    "Rwanda": "RWF",
}


def normalize(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce")

    min_val = series.min()
    max_val = series.max()

    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series(np.nan, index=series.index)

    return ((series - min_val) / (max_val - min_val)) * 100


def fetch_fx_daily(from_symbol: str, to_symbol: str = "USD", use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch daily FX data from Alpha Vantage and cache locally.
    Returns DataFrame with columns: date, exchange_rate
    """
    cache_file = FX_CACHE_DIR / f"{from_symbol}_{to_symbol}_daily.csv"

    if use_cache and cache_file.exists():
        cached = pd.read_csv(cache_file)
        cached["date"] = pd.to_datetime(cached["date"])
        return cached

    if not API_KEY:
        raise ValueError("Missing ALPHAVANTAGE_API_KEY in .env")

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_DAILY",
        "from_symbol": from_symbol,
        "to_symbol": to_symbol,
        "outputsize": "full",
        "apikey": API_KEY,
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()

    time_series_key = "Time Series FX (Daily)"
    if time_series_key not in data:
        raise ValueError(f"Unexpected FX response for {from_symbol}/{to_symbol}: {data}")

    rows = []
    for date_str, values in data[time_series_key].items():
        rows.append({
            "date": pd.to_datetime(date_str),
            "exchange_rate": pd.to_numeric(values.get("4. close"), errors="coerce")
        })

    fx_df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    fx_df.to_csv(cache_file, index=False)
    return fx_df


def build_fx_features_for_country(country_name: str, years: pd.Series) -> pd.DataFrame:
    """
    Build annual FX features aligned to platform year rows.
    Returns columns: year, fx_change, fx_volatility
    """
    currency = CURRENCY_MAP.get(country_name)

    if currency is None:
        return pd.DataFrame({
            "year": years,
            "fx_change": np.nan,
            "fx_volatility": np.nan,
        })

    try:
        fx_df = fetch_fx_daily(currency, "USD", use_cache=True)

        fx_df["year"] = fx_df["date"].dt.year
        fx_df["daily_return"] = fx_df["exchange_rate"].pct_change()

        annual = (
            fx_df.groupby("year", as_index=False)
            .agg(
                year_end_rate=("exchange_rate", "last"),
                fx_volatility=("daily_return", lambda x: x.std() * np.sqrt(252) * 100 if len(x.dropna()) > 5 else np.nan)
            )
            .sort_values("year")
        )

        annual["fx_change"] = annual["year_end_rate"].pct_change() * 100

        annual = annual[["year", "fx_change", "fx_volatility"]]

        merged = pd.DataFrame({"year": years.astype(int).unique()}).merge(annual, on="year", how="left")
        return merged

    except Exception as e:
        print(f"FX fetch failed for {country_name}: {e}")
        return pd.DataFrame({
            "year": years,
            "fx_change": np.nan,
            "fx_volatility": np.nan,
        })


def calculate_market_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a market-implied sovereign risk layer using:
    - Real FX annual change
    - Real FX volatility
    - Inflation acceleration
    - Debt pressure
    """
    df = df.copy()
    df = df.sort_values(["country_name", "year"]).reset_index(drop=True)

    fx_frames = []
    for country_name, sub_df in df.groupby("country_name"):
        fx_features = build_fx_features_for_country(country_name, sub_df["year"])
        fx_features["country_name"] = country_name
        fx_frames.append(fx_features)

    fx_all = pd.concat(fx_frames, ignore_index=True)

    df = df.merge(
        fx_all,
        on=["country_name", "year"],
        how="left"
    )

    df["inflation_change"] = (
        df.groupby("country_name")["inflation"]
        .diff()
    )

    if "debt_to_gdp" not in df.columns:
        df["debt_to_gdp"] = np.nan

    df["fx_pressure_score"] = normalize(df["fx_change"])
    df["fx_volatility_score"] = normalize(df["fx_volatility"])
    df["inflation_pressure_score"] = normalize(df["inflation_change"])
    df["debt_pressure_score"] = normalize(df["debt_to_gdp"])

    df["market_risk_score"] = (
        df["fx_pressure_score"] * 0.30
        + df["fx_volatility_score"] * 0.25
        + df["inflation_pressure_score"] * 0.20
        + df["debt_pressure_score"] * 0.25
    )

    return df