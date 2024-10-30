// src/services/twitter/TwitterService.ts
import { Scraper } from "agent-twitter-client";
import { BaseService } from "../base/BaseService";
import { RateLimitService } from "../base/RateLimitService";
import { TelegramService } from "../notification/TelegramService";
import { TwitterAuthService } from "./TwitterAuthService";

export class TwitterService extends BaseService {
  private scraper: Scraper;
  private authService: TwitterAuthService;
  private telegramService: TelegramService;
  private tweetRateLimit: RateLimitService;
  private searchRateLimit: RateLimitService;

  private static readonly RATE_LIMITS = {
    TWEETS_PER_HOUR: 50,
    TWEETS_PER_15_MIN: 15,
    SEARCH_PER_15_MIN: 180,
    MIN_DELAY_BETWEEN_TWEETS: 3000,
    MIN_DELAY_BETWEEN_SEARCHES: 1000,
  } as const;

  constructor() {
    super();
    this.scraper = new Scraper();
    this.authService = new TwitterAuthService(this.scraper);
    this.telegramService = new TelegramService();
    
    this.tweetRateLimit = new RateLimitService(
      TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS,
      TwitterService.RATE_LIMITS.TWEETS_PER_15_MIN
    );
    
    this.searchRateLimit = new RateLimitService(
      TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_SEARCHES,
      TwitterService.RATE_LIMITS.SEARCH_PER_15_MIN
    );
  }

  async initialize(): Promise<void> {
    await this.authService.initialize();
  }

  private async handleRateLimit(error: any): Promise<void> {
    if (error?.response?.status === 429) {
      const resetTime = error.response.headers?.["x-rate-limit-reset"];
      if (resetTime) {
        const waitTime = parseInt(resetTime) * 1000 - Date.now();
        this.logDebug(`Rate limited. Waiting ${waitTime / 1000} seconds...`);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      } else {
        this.logDebug("Rate limited. Waiting 15 minutes...");
        await new Promise((resolve) => setTimeout(resolve, 15 * 60 * 1000));
      }
    }
  }