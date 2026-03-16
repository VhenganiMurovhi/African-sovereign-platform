import requests
import pandas as pd
from pathlib import Path
from config import COUNTRIES, INDICATORS

BASE_URL = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_indicator(country_code, indicator_code):

    url = BASE_URL.format(country=country_code, indicator=indicator_code)

    params = {
        "format": "json",
        "per_page": 2000,
        "source": 2
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    if len(data) < 2:
        return []

    return data[1]


def collect_all_data():

    records = []

    for country_code, country_name in COUNTRIES.items():

        for indicator_code, indicator_name in INDICATORS.items():

            print(f"Fetching {country_name} - {indicator_name}")

            try:

                results = fetch_indicator(country_code, indicator_code)

                for item in results:

                    records.append({
                        "country_code": country_code,
                        "country_name": country_name,
                        "indicator": indicator_name,
                        "year": item["date"],
                        "value": item["value"]
                    })

            except Exception as e:

                print(f"Error {country_name} - {indicator_name}: {e}")

    return pd.DataFrame(records)


def main():

    df = collect_all_data()

    print(f"Total rows fetched: {len(df)}")

    if df.empty:
        print("No data fetched")
        return

    output_file = RAW_DATA_DIR / "world_bank_raw.csv"

    df.to_csv(output_file, index=False)

    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    main()