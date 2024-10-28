// types/sentiment.ts
export interface DailySentiment {
  date: string;
  positive: number;
  negative: number;
  helpful: number;
  sarcastic: number;
  message_count: number;
}

export interface HourlyPattern {
  hour: number;
  positive: number;
  negative: number;
  helpful: number;
  sarcastic: number;
  message_count: number;
}

export interface UserSentiment {
  username: string;
  positive: number;
  negative: number;
  helpful: number;
  sarcastic: number;
  message_count: number;
  sentiment_balance: number;
}

export interface SentimentStats {
  total_messages: number;
  avg_positive: number;
  avg_negative: number;
  avg_helpful: number;
  avg_sarcastic: number;
  avg_sentiment_balance: number;
}

export interface SentimentData {
  daily: DailySentiment[];
  hourly: HourlyPattern[];
  users: UserSentiment[];
  stats: SentimentStats;
}
