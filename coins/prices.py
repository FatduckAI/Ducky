import os

import requests

from lib import sdk

# API endpoint and headers
url = 'https://api.coingecko.com/api/v3/coins/markets'
params = {
    'vs_currency': 'usd',
    'category': 'solana-meme-coins'
}
headers = {
    'accept': 'application/json',
    'x-cg-demo-api-key': os.environ.get('COINGECKO_API_KEY')
}

if __name__ == "__main__":
    # Make API request
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise an exception for bad responses
    data = response.json()

    # Process each coin and save to database
    for coin in data:
        sdk.save_coin_prices(coin)

    print(f"Successfully updated data for {len(data)} coins.")