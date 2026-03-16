import sys
from pathlib import Path

# Make project root importable so Streamlit can find src/
sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.modelling.monte_carlo import simulate_sovereign_risk

st.set_page_config(
    page_title="Monte Carlo Sovereign Stress Test",
    layout="wide"
)

DATA_FILE = Path("data/processed/country_risk_scores.csv")

st.title("Monte Carlo Sovereign Stress Simulation")
st.subheader("Scenario-based sovereign risk stress testing")

if not DATA_FILE.exists():
    st.error("Risk score dataset not found. Run the risk scoring script first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["sovereign_risk_score"] = pd.to_numeric(df["sovereign_risk_score"], errors="coerce")
df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

countries = sorted(df["country_name"].dropna().unique().tolist())
selected_country = st.selectbox("Select a Country", countries)

country_df = df[df["country_name"] == selected_country].sort_values("year").copy()
country_scored = country_df.dropna(subset=["sovereign_risk_score"])

if country_scored.empty:
    st.warning("No usable scored data available for this country.")
    st.stop()

latest_row = country_scored.iloc[-1]

st.write("## Simulation Controls")

col1, col2 = st.columns(2)

scenario = col1.selectbox(
    "Scenario",
    [
        "Baseline",
        "Global Rate Shock",
        "Commodity Crash",
        "Debt Crisis",
        "Economic Boom",
    ]
)

n_sims = col2.slider(
    "Number of simulations",
    min_value=100,
    max_value=10000,
    value=2000,
    step=100
)

col3, col4 = st.columns(2)
seed = col3.number_input("Random seed", min_value=1, value=42, step=1)

show_advanced = col4.checkbox("Show advanced volatility controls", value=False)

gdp_vol = 2.0
inflation_vol = 3.0
debt_vol = 5.0

if show_advanced:
    st.write("### Volatility Controls")
    v1, v2, v3 = st.columns(3)

    gdp_vol = v1.slider(
        "GDP shock volatility",
        min_value=0.5,
        max_value=6.0,
        value=2.0,
        step=0.5
    )
    inflation_vol = v2.slider(
        "Inflation shock volatility",
        min_value=0.5,
        max_value=8.0,
        value=3.0,
        step=0.5
    )
    debt_vol = v3.slider(
        "Debt shock volatility",
        min_value=1.0,
        max_value=12.0,
        value=5.0,
        step=0.5
    )

results = simulate_sovereign_risk(
    latest_row=latest_row,
    n_sims=n_sims,
    seed=int(seed),
    scenario=scenario,
    gdp_vol=gdp_vol,
    inflation_vol=inflation_vol,
    debt_vol=debt_vol,
)

avg_score = results["simulated_risk_score"].mean()
median_score = results["simulated_risk_score"].median()
p_high_risk = (results["simulated_risk_score"] >= 67).mean() * 100
p_moderate_or_worse = (results["simulated_risk_score"] >= 34).mean() * 100
worst_case_95 = results["simulated_risk_score"].quantile(0.95)

st.write("## Stress Test Summary")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Base Risk Score", round(float(latest_row["sovereign_risk_score"]), 2))
m2.metric("Avg Simulated Risk", round(avg_score, 2))
m3.metric("Median Risk", round(median_score, 2))
m4.metric("Prob. High Risk (%)", round(p_high_risk, 2))
m5.metric("95th Percentile Risk", round(worst_case_95, 2))

st.write("## Scenario Context")

c1, c2, c3 = st.columns(3)
c1.metric(
    "Base GDP Growth (%)",
    round(pd.to_numeric(latest_row.get("gdp_growth"), errors="coerce"), 2)
    if pd.notna(pd.to_numeric(latest_row.get("gdp_growth"), errors="coerce")) else "N/A"
)
c2.metric(
    "Base Inflation (%)",
    round(pd.to_numeric(latest_row.get("inflation"), errors="coerce"), 2)
    if pd.notna(pd.to_numeric(latest_row.get("inflation"), errors="coerce")) else "N/A"
)
c3.metric(
    "Base Debt to GDP (%)",
    round(pd.to_numeric(latest_row.get("debt_to_gdp"), errors="coerce"), 2)
    if pd.notna(pd.to_numeric(latest_row.get("debt_to_gdp"), errors="coerce")) else "N/A"
)

st.caption(f"Selected scenario: {scenario}")

st.write("## Simulated Risk Distribution")
fig_hist = px.histogram(
    results,
    x="simulated_risk_score",
    nbins=40,
    title=f"Simulated Sovereign Risk Distribution - {selected_country}"
)
st.plotly_chart(fig_hist, use_container_width=True)

st.write("## Simulated Macro Relationships")

scatter_sample = results.sample(min(len(results), 800), random_state=int(seed))

fig_scatter = px.scatter(
    scatter_sample,
    x="sim_debt_to_gdp",
    y="simulated_risk_score",
    title="Debt Stress vs Simulated Risk Score",
    hover_data=["sim_gdp_growth", "sim_inflation", "risk_band"]
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.write("## GDP vs Inflation Under Stress")
fig_macro = px.scatter(
    scatter_sample,
    x="sim_gdp_growth",
    y="sim_inflation",
    color="risk_band",
    title="Simulated GDP Growth vs Inflation"
)
st.plotly_chart(fig_macro, use_container_width=True)

st.write("## Risk Band Outcomes")
band_counts = (
    results["risk_band"]
    .value_counts()
    .rename_axis("risk_band")
    .reset_index(name="count")
)

fig_bands = px.bar(
    band_counts,
    x="risk_band",
    y="count",
    title="Simulated Risk Band Distribution"
)
st.plotly_chart(fig_bands, use_container_width=True)

st.write("## Simulation Sample")
st.dataframe(results.head(20), use_container_width=True)
