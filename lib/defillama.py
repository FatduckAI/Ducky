import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

# Assuming env.DEFILLAMA_API_KEY is stored in an environment variable
DEFILLAMA_API_KEY = os.environ.get('DEFILLAMA_API_KEY')
BASE_URL = f"https://pro-api.llama.fi/{DEFILLAMA_API_KEY}"

def fetch_data(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    url = f"{BASE_URL}/{endpoint}"
    print('url', url)

    # Append params to URL
    if params:
        url += '?' + '&'.join(f"{key}={value}" for key, value in params.items())

    # Fetch the data
    response = requests.get(url, headers={'accept': 'application/json'})

    if not response.ok:
        print('response', response)
        raise Exception(f"Failed to fetch: {response.status_code} {response.reason}")

    return response.json()

class Narratives:
    @staticmethod
    def fdv_performance(period: str) -> Dict[str, Any]:
        if period not in ['7', '30', 'ytd', '365']:
            raise ValueError("Period must be one of ['7', '30', 'ytd', '365']")
        url = f"fdv/performance/{period}"
        return fetch_data(url)

# Usage example:
# narratives = Narratives()
# data = narratives.fdv_performance('7')