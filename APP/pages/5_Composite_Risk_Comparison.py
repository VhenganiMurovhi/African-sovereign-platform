import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Composite Risk Comparison",
    layout="wide"
)

DATA_FILE = Path("data/processed/country_risk_scores.csv")

st.title("Composite Sovereign Risk Comparison")
st.subheader("Compare fundamental, market-implied, and composite sovereign risk across countries")

if not DATA_FILE.exists():
    st.error("Risk score dataset not found. Run the scoring pipeline first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["sovereign_risk_score"] = pd.to_numeric(df["sovereign_risk_score"], errors="coerce")
df["market_risk_score"] = pd.to_numeric(df["market_risk_score"], errors="coerce")
df["composite_risk_score"] = pd.to_numeric(df["composite_risk_score"], errors="coerce")

df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

countries = sorted(df["country_name"].dropna().unique().tolist())

default_countries = countries[:3] if len(countries) >= 3 else countries

selected_countries = st.multiselect(
    "Select countries to compare",
    countries,
    default=default_countries
)

metric_options = {
    "Fundamental Risk": "sovereign_risk_score",
    "Market-Implied Risk": "market_risk_score",
    "Composite Risk": "composite_risk_score",
    "GDP Growth": "gdp_growth",
    "Inflation": "inflation",
    "Debt to GDP": "debt_to_gdp",
    "FX Annual Change": "fx_change",
    "FX Volatility": "fx_volatility",
}

selected_metric_label = st.selectbox("Select comparison metric", list(metric_options.keys()))
selected_metric = metric_options[selected_metric_label]

compare_df = df[df["country_name"].isin(selected_countries)].copy()

if compare_df.empty:
    st.warning("Please select at least one country.")
    st.stop()

chart_df = compare_df[["country_name", "year", selected_metric]].dropna()

if chart_df.empty:
    st.warning(f"No usable data available for {selected_metric_label}.")
    st.stop()

st.write("## Comparison Trend")

fig_line = px.line(
    chart_df,
    x="year",
    y=selected_metric,
    color="country_name",
    markers=True,
    title=f"{selected_metric_label} Comparison"
)
st.plotly_chart(fig_line, use_container_width=True)

st.write("## Latest Available Snapshot")

latest_rows = (
    chart_df.sort_values("year")
    .groupby("country_name", as_index=False)
    .tail(1)
    .sort_values(selected_metric, ascending=False)
)

st.dataframe(latest_rows, use_container_width=True)

fig_bar = px.bar(
    latest_rows,
    x="country_name",
    y=selected_metric,
    color="country_name",
    title=f"Latest {selected_metric_label} by Country"
)
st.plotly_chart(fig_bar, use_container_width=True)

st.write("## Risk Layer Comparison Table")

layer_cols = [
    "country_name",
    "year",
    "sovereign_risk_score",
    "market_risk_score",
    "composite_risk_score",
    "risk_band",
    "composite_risk_band"
]

layer_df = (
    compare_df[layer_cols]
    .dropna(subset=["composite_risk_score"], how="all")
    .sort_values("year")
    .groupby("country_name", as_index=False)
    .tail(1)
    .sort_values("composite_risk_score", ascending=False)
)

st.dataframe(layer_df, use_container_width=True)
