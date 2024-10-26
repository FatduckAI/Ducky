import logging
import time
from typing import Dict

import requests

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Price cache configuration
price_cache: Dict[str, float] = {}
last_check: Dict[str, float] = {}
CACHE_DURATION = 60  # Cache duration in seconds

async def get_token_price() -> tuple[float, bool]:
    """
    Fetch token price from Raydium API
    Returns: (price, is_cached)
    """
    token_address = "HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump"
    current_time = time.time()
    
    # Check cache
    if token_address in last_check and current_time - last_check[token_address] < CACHE_DURATION:
        return price_cache[token_address], True
    
    # Fetch new price
    api_url = "https://api.raydium.io/v2/main/price"
    response = requests.get(api_url, params={"tokens": token_address})
    response.raise_for_status()
    
    data = response.json()
    if token_address not in data:
        raise ValueError("Token price not found in API response")
    
    price = float(data[token_address])
    
    # Update cache
    price_cache[token_address] = price
    last_check[token_address] = current_time
    
    return price, False