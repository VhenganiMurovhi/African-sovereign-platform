# African Sovereign Intelligence Platform

A data-driven analytics platform for assessing sovereign macroeconomic risk across African economies.

This project builds a sovereign risk monitoring system using World Bank macroeconomic data, risk scoring models, and interactive dashboards.

## Features

- Automated data ingestion from the World Bank API
- Cleaned country macroeconomic panel dataset
- Sovereign risk scoring model
- Risk band classification
- Risk pillar analysis
- Interactive dashboard built with Streamlit
- Cross-country comparison tools

## Data Indicators

The platform currently analyzes:

- GDP Growth
- Inflation
- Debt to GDP
- Exports to GDP
- Imports to GDP
- Foreign Direct Investment (% of GDP)
- Electricity Access
- Unemployment
- Industry Value Added
- Real Interest Rates

## Risk Model

The sovereign risk score is calculated using a weighted model across several pillars:

- Debt Sustainability
- Macro Stability
- External Vulnerability
- Growth Capacity
- Development Capacity

Scores are normalized and aggregated into a composite **Sovereign Risk Score (0–100)** and classified into risk bands.

## Dashboard

The interactive dashboard allows users to:

- Explore country macro profiles
- View sovereign risk scores
- Analyze macro trends
- Compare countries
- View risk pillar breakdowns

## Running the Project

Install dependencies: