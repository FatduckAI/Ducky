# price_lib.py

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import requests

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token configuration
TOKEN_ADDRESS = "HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump"
SOL_ADDRESS = "So11111111111111111111111111111111111111112"  # SOL
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
TOKEN_SUPPLY = 1_000_000_000  # 1 billion fixed supply

# Cache configuration
CACHE_DURATION = 60  # seconds

@dataclass
class PriceInfo:
    usd_price: float
    sol_price: float
    market_cap: float
    best_dex: str
    timestamp: float
    is_cached: bool

class PriceCache:
    def __init__(self):
        self._cache: Dict[str, PriceInfo] = {}
    
    def get(self, token: str) -> Optional[PriceInfo]:
        if token not in self._cache:
            return None
        if time.time() - self._cache[token].timestamp > CACHE_DURATION:
            return None
        cached_info = self._cache[token]
        return PriceInfo(
            usd_price=cached_info.usd_price,
            sol_price=cached_info.sol_price,
            market_cap=cached_info.market_cap,
            best_dex=cached_info.best_dex,
            timestamp=cached_info.timestamp,
            is_cached=True
        )
    
    def set(self, token: str, info: PriceInfo):
        self._cache[token] = info

price_cache = PriceCache()

async def get_sol_price() -> float:
    """Get SOL price in USD"""
    try:
        url = "https://price.jup.ag/v4/price"
        params = {
            "ids": SOL_ADDRESS
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data or SOL_ADDRESS not in data["data"]:
            raise ValueError("No SOL price data in response")
            
        return float(data["data"][SOL_ADDRESS]["price"])
    
    except Exception as e:
        logger.error(f"Error fetching SOL price: {str(e)}")
        raise

async def get_token_price() -> PriceInfo:
    """
    Fetch token prices from Jupiter API
    Returns: PriceInfo object with USD and SOL prices
    """
    # Check cache
    cached = price_cache.get(TOKEN_ADDRESS)
    if cached:
        return cached
    
    try:
        url = "https://price.jup.ag/v4/price"
        params = {
            "ids": f"{TOKEN_ADDRESS},{SOL_ADDRESS}"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "data" not in data:
            raise ValueError("No price data in response")
            
        token_data = data["data"].get(TOKEN_ADDRESS)
        sol_data = data["data"].get(SOL_ADDRESS)
        
        if not token_data or not sol_data:
            raise ValueError("Missing price data for token or SOL")
        
        # Get USD prices with full precision
        sol_price_usd = float(sol_data["price"])
        token_price_usd = float(token_data["price"])
        
        # Calculate SOL price with full precision
        sol_price = token_price_usd / sol_price_usd
        
        # Calculate market cap using fixed supply
        market_cap = token_price_usd * TOKEN_SUPPLY
        
        # Get best DEX info
        best_dex = token_data.get("project", "Jupiter")
        
        price_info = PriceInfo(
            usd_price=token_price_usd,
            sol_price=sol_price,
            market_cap=market_cap,
            best_dex=best_dex,
            timestamp=time.time(),
            is_cached=False
        )
        
        # Update cache
        price_cache.set(TOKEN_ADDRESS, price_info)
        logger.info(f"Updated price cache for {TOKEN_ADDRESS}: ${token_price_usd} USD, ◎{sol_price} SOL, MCap: ${market_cap}")
        
        return price_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching price from Jupiter: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error processing Jupiter response: {str(e)}")
        raise

def format_market_cap(market_cap: float) -> str:
    """Format market cap to human readable format"""
    if market_cap >= 1_000_000_000:  # Billions
        return f"${market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:  # Millions
        return f"${market_cap / 1_000_000:.2f}M"
    elif market_cap >= 1_000:  # Thousands
        return f"${market_cap / 1_000:.2f}K"
    else:
        return f"${market_cap:.2f}"

# For testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            print("\nFetching prices...")
            price_info = await get_token_price()
            print(f"\nToken Price Information:")
            print(f"USD Price: ${price_info.usd_price}")
            print(f"SOL Price: ◎{price_info.sol_price}")
            print(f"Market Cap: {format_market_cap(price_info.market_cap)}")
            print(f"Best DEX: {price_info.best_dex}")
            print(f"Cached: {price_info.is_cached}")
            
            # Test cache
            print("\nTesting cache...")
            cached_price = await get_token_price()
            print(f"Cached: {cached_price.is_cached}")
            
        except Exception as e:
            print(f"Error: {str(e)}")

    asyncio.run(main())