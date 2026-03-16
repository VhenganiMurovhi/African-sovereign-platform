import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd

from src.reporting.pdf_report import build_country_risk_report

st.set_page_config(
    page_title="PDF Country Risk Report",
    layout="wide"
)

DATA_FILE = Path("data/processed/country_risk_scores.csv")
OUTPUT_DIR = Path("outputs/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.title("PDF Country Risk Report Generator")
st.subheader("Generate a downloadable sovereign risk report")

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

st.write("## Report Preview")
col1, col2, col3 = st.columns(3)
col1.metric("Latest Year", int(latest_row["year"]))
col2.metric("Risk Score", round(float(latest_row["sovereign_risk_score"]), 2))
col3.metric("Risk Band", latest_row["risk_band"])

file_name = f"{selected_country.lower().replace(' ', '_')}_country_risk_report.pdf"
output_path = OUTPUT_DIR / file_name

if st.button("Generate PDF Report"):
    pdf_path = build_country_risk_report(
        latest_row=latest_row,
        country_history=country_df,
        output_path=str(output_path)
    )

    st.success(f"PDF report created: {pdf_path}")

if output_path.exists():
    with open(output_path, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=file_name,
            mime="application/pdf"
        )