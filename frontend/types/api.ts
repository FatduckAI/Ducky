// Types for the protected routes (save these in app/types/api.ts)
export interface Tweet {
  content: string;
  tweet_id: string;
}

export interface Conversation {
  content: string;
  summary: string;
  tweet_url: string;
}

export interface Narrative {
  content: string;
  summary: string;
}

export interface Coin {
  id: string;
  symbol: string;
  name: string;
  image: string;
}

export interface CoinPrices {
  id: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  fully_diluted_valuation: number;
  total_volume: number;
  high_24h: number;
  low_24h: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  market_cap_change_24h: number;
  market_cap_change_percentage_24h: number;
  circulating_supply: number;
  total_supply: number;
  max_supply: number;
  ath: number;
  ath_change_percentage: number;
  ath_date: string;
  atl: number;
  atl_change_percentage: number;
  atl_date: string;
  roi: string;
  last_updated: string;
}
