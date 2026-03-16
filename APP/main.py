import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="African Sovereign Platform", layout="wide")

DATA_FILE = Path("data/processed/country_risk_scores.csv")

st.title("African Sovereign Platform")
st.subheader("Sovereign Risk Intelligence Dashboard")

if not DATA_FILE.exists():
    st.error("Risk score dataset not found. Run the risk scoring script first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["sovereign_risk_score"] = pd.to_numeric(df["sovereign_risk_score"], errors="coerce")
df["market_risk_score"] = pd.to_numeric(df["market_risk_score"], errors="coerce")
df["composite_risk_score"] = pd.to_numeric(df["composite_risk_score"], errors="coerce")

df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

countries = sorted(df["country_name"].dropna().unique().tolist())
selected_country = st.selectbox("Select a Country", countries)

country_df = df[df["country_name"] == selected_country].sort_values("year").copy()
country_scored = country_df.dropna(subset=["sovereign_risk_score"])

if country_scored.empty:
    st.warning("No usable risk score data available for this country.")
    st.stop()

latest_row = country_scored.iloc[-1]

st.write("## Latest Sovereign Risk Snapshot")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Scored Year", int(latest_row["year"]))
col2.metric("Fundamental Risk", round(latest_row["sovereign_risk_score"], 2) if pd.notna(latest_row["sovereign_risk_score"]) else "N/A")
col3.metric("Market Risk", round(latest_row["market_risk_score"], 2) if pd.notna(latest_row["market_risk_score"]) else "N/A")
col4.metric("Composite Risk", round(latest_row["composite_risk_score"], 2) if pd.notna(latest_row["composite_risk_score"]) else "N/A")

col5, col6, col7 = st.columns(3)
col5.metric("Fundamental Band", latest_row["risk_band"] if pd.notna(latest_row["risk_band"]) else "Unknown")
col6.metric("Composite Band", latest_row["composite_risk_band"] if pd.notna(latest_row["composite_risk_band"]) else "Unknown")
col7.metric("GDP Growth (%)", round(latest_row["gdp_growth"], 2) if pd.notna(latest_row["gdp_growth"]) else "N/A")

st.write("## Risk Layers Comparison")

comparison_df = pd.DataFrame({
    "Type": ["Fundamental", "Market-Implied", "Composite"],
    "Score": [
        latest_row["sovereign_risk_score"],
        latest_row["market_risk_score"],
        latest_row["composite_risk_score"]
    ]
}).dropna()

if not comparison_df.empty:
    fig_layers = px.bar(
        comparison_df,
        x="Type",
        y="Score",
        title=f"Risk Layers - {selected_country}"
    )
    st.plotly_chart(fig_layers, use_container_width=True)

st.write("## Risk Pillar Breakdown")

pillar_df = pd.DataFrame({
    "Pillar": [
        "Debt Sustainability",
        "Macro Stability",
        "External Vulnerability",
        "Growth Capacity",
        "Development Capacity",
    ],
    "Score": [
        latest_row["debt_sustainability"],
        latest_row["macro_stability"],
        latest_row["external_vulnerability"],
        latest_row["growth_capacity"],
        latest_row["development_capacity"],
    ],
})

pillar_df = pillar_df.dropna()

if not pillar_df.empty:
    fig_pillars = px.bar(
        pillar_df,
        x="Pillar",
        y="Score",
        title=f"Risk Pillar Scores - {selected_country}"
    )
    st.plotly_chart(fig_pillars, use_container_width=True)

st.write("## Fundamental Risk Trend")
risk_chart_df = country_scored[["year", "sovereign_risk_score"]].dropna()

if not risk_chart_df.empty:
    fig_risk = px.line(
        risk_chart_df,
        x="year",
        y="sovereign_risk_score",
        markers=True,
        title=f"Fundamental Sovereign Risk Trend - {selected_country}"
    )
    st.plotly_chart(fig_risk, use_container_width=True)

st.write("## Composite Risk Trend")
composite_chart_df = country_df[["year", "composite_risk_score"]].dropna()

if not composite_chart_df.empty:
    fig_composite = px.line(
        composite_chart_df,
        x="year",
        y="composite_risk_score",
        markers=True,
        title=f"Composite Risk Trend - {selected_country}"
    )
    st.plotly_chart(fig_composite, use_container_width=True)

st.write("## Indicator Trend")
chart_options = {
    "GDP Growth": "gdp_growth",
    "Inflation": "inflation",
    "Debt to GDP": "debt_to_gdp",
    "Exports to GDP": "exports_to_gdp",
    "Imports to GDP": "imports_to_gdp",
    "FDI % GDP": "fdi_pct_gdp",
    "Real Interest Rate": "real_interest_rate",
    "Unemployment": "unemployment",
    "Industry Value Added": "industry_value_added",
    "Electricity Access": "electricity_access",
    "FX Change Proxy": "fx_change",
    "FX Volatility Proxy": "fx_volatility",
    "Inflation Change": "inflation_change"
}

selected_metric_label = st.selectbox("Choose a metric to visualize", list(chart_options.keys()))
selected_metric = chart_options[selected_metric_label]

metric_df = country_df[["year", selected_metric]].dropna()

if not metric_df.empty:
    fig_metric = px.line(
        metric_df,
        x="year",
        y=selected_metric,
        markers=True,
        title=f"{selected_metric_label} Trend - {selected_country}"
    )
    st.plotly_chart(fig_metric, use_container_width=True)
else:
    st.warning(f"No data available for {selected_metric_label}.")

st.write("## Cross-Country Composite Ranking")

valid_score_df = df.dropna(subset=["composite_risk_score"]).copy()
if not valid_score_df.empty:
    ranking_year = valid_score_df["year"].max()

    ranking_df = valid_score_df[valid_score_df["year"] == ranking_year][
        ["country_name", "composite_risk_score", "composite_risk_band"]
    ].sort_values("composite_risk_score", ascending=False)

    st.caption(f"Composite ranking year: {ranking_year}")
    st.dataframe(ranking_df, use_container_width=True)

    if not ranking_df.empty:
        fig_rank = px.bar(
            ranking_df,
            x="country_name",
            y="composite_risk_score",
            color="composite_risk_band",
            title=f"Composite Sovereign Risk Ranking - {ranking_year}"
        )
        st.plotly_chart(fig_rank, use_container_width=True)

st.write("## Recent Country Data")
preview_df = country_df.sort_values("year", ascending=False).head(10).copy()
st.dataframe(preview_df, use_container_width=True)