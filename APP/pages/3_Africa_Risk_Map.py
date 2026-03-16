import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Africa Sovereign Risk Map",
    layout="wide"
)

DATA_FILE = Path("data/processed/country_risk_scores.csv")

st.title("Africa Sovereign Risk Map")
st.subheader("Latest available sovereign risk scores across selected African economies")

if not DATA_FILE.exists():
    st.error("Risk score dataset not found. Run the risk scoring script first.")
    st.stop()

df = pd.read_csv(DATA_FILE)

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["sovereign_risk_score"] = pd.to_numeric(df["sovereign_risk_score"], errors="coerce")

df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

# Keep only rows with actual scores
valid_df = df.dropna(subset=["sovereign_risk_score"]).copy()

if valid_df.empty:
    st.warning("No valid sovereign risk scores available for mapping.")
    st.stop()

# Get latest valid row per country
latest_country_scores = (
    valid_df.sort_values(["country_name", "year"])
    .groupby("country_name", as_index=False)
    .tail(1)
    .copy()
)

latest_country_scores["display_label"] = (
    latest_country_scores["country_name"]
    + "<br>Year: " + latest_country_scores["year"].astype(str)
    + "<br>Risk Score: " + latest_country_scores["sovereign_risk_score"].round(2).astype(str)
    + "<br>Risk Band: " + latest_country_scores["risk_band"].astype(str)
)

st.write("## Map View")

fig = px.choropleth(
    latest_country_scores,
    locations="country_code",
    color="sovereign_risk_score",
    hover_name="country_name",
    hover_data={
        "country_code": False,
        "year": True,
        "risk_band": True,
        "sovereign_risk_score": ":.2f"
    },
    color_continuous_scale="RdYlGn_r",
    range_color=(0, 100),
    scope="africa",
    title="Africa Sovereign Risk Map"
)

fig.update_layout(
    margin=dict(l=10, r=10, t=60, b=10),
    coloraxis_colorbar=dict(title="Risk Score")
)

st.plotly_chart(fig, use_container_width=True)

st.write("## Latest Country Scores")

display_df = latest_country_scores[
    ["country_name", "country_code", "year", "sovereign_risk_score", "risk_band"]
].sort_values("sovereign_risk_score", ascending=False)

st.dataframe(display_df, use_container_width=True)

st.write("## Risk Ranking Bar Chart")

fig_bar = px.bar(
    display_df,
    x="country_name",
    y="sovereign_risk_score",
    color="risk_band",
    title="Latest Sovereign Risk Ranking"
)

st.plotly_chart(fig_bar, use_container_width=True)