import pandas as pd
import requests

# 1. Your SatNOGS DB API Token (from db.satnogs.org)
DB_API_TOKEN = "2d5b4f9c69d6eba2a7f420213e3528f167b23358"

# 2. Your SatNOGS Network API Token (from network.satnogs.org)
NETWORK_API_TOKEN = "687b7e5a491dbaa2b1c4dc9411b832df9f0ba742"


def fetch_paginated_data(endpoint_url, token):
    """Fetches data from a paginated API using the provided API token."""
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }
    results = []
    url = f"{endpoint_url}?format=json"

    print(f"Fetching: {endpoint_url}...")
    while url:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(
                f"  --> Failed! Status {response.status_code}: {response.text}"
            )
            break

        data = response.json()

        # Handle flat lists vs paginated dictionaries with 'results'
        if isinstance(data, list):
            results.extend(data)
            url = None
        else:
            results.extend(data.get("results", []))
            url = data.get("next")

    return results


# --- 1. Export SatNOGS DB Data ---
db_endpoints = {
    "satellites": "https://db.satnogs.org/api/satellites/",
    "transmitters": "https://db.satnogs.org/api/transmitters/",
    "modes": "https://db.satnogs.org/api/modes/",
    "tle": "https://db.satnogs.org/api/tle/",
    "artifacts": "https://db.satnogs.org/api/artifacts/",
    "optical_observations": "https://db.satnogs.org/api/optical-observations/",
    "transmitter_params_schemas": "https://db.satnogs.org/api/transmitter-params-schemas/",
}

print("=== Downloading SatNOGS DB Datasets ===")
for name, url in db_endpoints.items():
    data = fetch_paginated_data(url, DB_API_TOKEN)
    if data:
        filename = f"satnogs_db_{name}.csv"
        pd.DataFrame(data).to_csv(filename, index=False, encoding="utf-8")
        print(f"-> Saved {filename} ({len(data)} records)\n")

# --- 2. Export SatNOGS Network Data ---
network_endpoints = {
    "stations": "https://network.satnogs.org/api/stations/",
    "observations": "https://network.satnogs.org/api/observations/",
    "jobs": "https://network.satnogs.org/api/jobs/",
}

print("=== Downloading SatNOGS Network Datasets ===")
for name, url in network_endpoints.items():
    data = fetch_paginated_data(url, NETWORK_API_TOKEN)
    if data:
        filename = f"satnogs_network_{name}.csv"
        pd.DataFrame(data).to_csv(filename, index=False, encoding="utf-8")
        print(f"-> Saved {filename} ({len(data)} records)\n")