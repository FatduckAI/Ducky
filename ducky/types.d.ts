export interface TweetResponse {
  success: boolean;
  url?: string;
  error?: string;
}

export interface CookieJSON {
  key: string;
  value: string;
  domain?: string;
  path?: string;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: string;
  expires?: string;
}

export interface TwitterReply {
  id: string;
  author: string;
  text: string;
  created_at: string;
  likes: number;
  retweets: number;
  author_followers?: number;
  author_verified?: boolean;
}

export interface AnalysisResponse {
  selectedTweet: {
    author: string;
    text: string;
  };
  reasoning: string;
}

export interface InfluencerTweet {
  author: string;
  text: string;
  engagement: number;
  tweetId: string;
  followers?: number;
}

export interface AnalysisResponse {
  selectedTweet: {
    author: string;
    text: string;
  };
  reasoning: string;
}
