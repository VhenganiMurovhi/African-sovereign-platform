import numpy as np
import pandas as pd


def _safe_number(value, fallback):
    value = pd.to_numeric(value, errors="coerce")
    if pd.isna(value):
        return fallback
    return float(value)


def _apply_scenario(base_gdp, base_inflation, base_debt, scenario):
    """
    Apply deterministic scenario adjustments before random simulation.
    """
    if scenario == "Global Rate Shock":
        base_inflation += 3.0
        base_debt += 5.0

    elif scenario == "Commodity Crash":
        base_gdp -= 2.0
        base_debt += 3.0

    elif scenario == "Debt Crisis":
        base_debt += 10.0
        base_inflation += 2.0
        base_gdp -= 1.0

    elif scenario == "Economic Boom":
        base_gdp += 2.0
        base_debt -= 3.0

    return base_gdp, base_inflation, base_debt


def _score_to_band(score):
    if pd.isna(score):
        return "Unknown"
    if score <= 33:
        return "Low Risk"
    if score <= 66:
        return "Moderate Risk"
    return "High Risk"


def simulate_sovereign_risk(
    latest_row: pd.Series,
    n_sims: int = 2000,
    seed: int = 42,
    scenario: str = "Baseline",
    gdp_vol: float = 2.0,
    inflation_vol: float = 3.0,
    debt_vol: float = 5.0,
) -> pd.DataFrame:
    """
    Simulate sovereign macro stress outcomes using a simple Monte Carlo framework.
    Returns a DataFrame of simulated GDP growth, inflation, debt, risk score, and risk band.
    """
    rng = np.random.default_rng(seed)

    # Base values from latest country row
    base_gdp = _safe_number(latest_row.get("gdp_growth"), 2.0)
    base_inflation = _safe_number(latest_row.get("inflation"), 6.0)
    base_debt = _safe_number(latest_row.get("debt_to_gdp"), 60.0)

    # Apply scenario assumptions
    base_gdp, base_inflation, base_debt = _apply_scenario(
        base_gdp, base_inflation, base_debt, scenario
    )

    # Random shocks
    gdp_shocks = rng.normal(loc=0.0, scale=gdp_vol, size=n_sims)
    inflation_shocks = rng.normal(loc=0.0, scale=inflation_vol, size=n_sims)
    debt_shocks = rng.normal(loc=0.0, scale=debt_vol, size=n_sims)

    sim_gdp = base_gdp + gdp_shocks
    sim_inflation = np.clip(base_inflation + inflation_shocks, 0, None)
    sim_debt = np.clip(base_debt + debt_shocks, 0, None)

    # Stress score logic
    # Higher debt and inflation worsen risk.
    # Higher growth reduces risk.
    simulated_risk = (
        0.45 * sim_debt
        + 0.35 * sim_inflation
        - 0.25 * sim_gdp
    )

    # Rescale to a rough 0-100 band
    simulated_risk = np.clip(simulated_risk / 1.5, 0, 100)

    results = pd.DataFrame({
        "sim_gdp_growth": sim_gdp,
        "sim_inflation": sim_inflation,
        "sim_debt_to_gdp": sim_debt,
        "simulated_risk_score": simulated_risk,
    })

    results["risk_band"] = results["simulated_risk_score"].apply(_score_to_band)
    return results