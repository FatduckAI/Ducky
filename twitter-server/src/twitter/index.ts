// src/twitter/index.ts

import { Scraper, SearchMode } from "agent-twitter-client";
import axios from "axios";
import { db } from "../../db";
import { duckyAi } from "../../db/schema";
import type { CookieJSON, TweetResponse, TwitterReply } from "../../types";

export class TwitterService {
  private scraper: Scraper;
  private cookiesPath: string;
  private telegramBotToken: string;
  private targetChannelId: string;
  private loginRetryAttempts = 0;
  private readonly MAX_LOGIN_RETRIES = 3;

  // Rate limiting constants
  private static readonly RATE_LIMITS = {
    TWEETS_PER_HOUR: 50,
    TWEETS_PER_15_MIN: 15,
    SEARCH_PER_15_MIN: 180,
    MIN_DELAY_BETWEEN_TWEETS: 3000,
    MIN_DELAY_BETWEEN_SEARCHES: 1000,
  } as const;

  // Rate tracking
  private tweetCount = 0;
  private searchCount = 0;
  private lastTweetTime = 0;
  private lastSearchTime = 0;

  constructor() {
    this.scraper = new Scraper();
    this.cookiesPath = process.env.COOKIES_PATH || "cookies.json";
    this.telegramBotToken = process.env.TELEGRAM_BOT_TOKEN || "";
    this.targetChannelId = process.env.TARGET_CHANNEL_ID || "";

    if (!this.telegramBotToken || !this.targetChannelId) {
      console.warn("Missing Telegram credentials");
    }
  }

  private logDebug(message: string, data?: any) {
    console.log(`[TwitterService] ${message}`);
    if (data) {
      console.log(JSON.stringify(data, null, 2));
    }
  }

  private logError(message: string, error: any) {
    console.error(`[TwitterService Error] ${message}`);
    console.error("Error details:", {
      name: error?.name,
      message: error?.message,
      status: error?.response?.status,
      headers: error?.response?.headers,
      data: error?.response?.data,
    });
  }

  private async loadCookies(): Promise<string[]> {
    try {
      const cookiesJson = JSON.parse(await Bun.file(this.cookiesPath).text());
      return cookiesJson.map((cookieJson: CookieJSON) => {
        const parts = [
          `${cookieJson.key}=${cookieJson.value}`,
          `Domain=${cookieJson.domain || ".twitter.com"}`,
          `Path=${cookieJson.path || "/"}`,
        ];

        if (cookieJson.secure) parts.push("Secure");
        if (cookieJson.httpOnly) parts.push("HttpOnly");
        if (cookieJson.sameSite) parts.push(`SameSite=${cookieJson.sameSite}`);
        if (cookieJson.expires) parts.push(`Expires=${cookieJson.expires}`);

        return parts.join("; ");
      });
    } catch (error) {
      this.logError("Could not load cookies", error);
      return [];
    }
  }

  private async saveCookies() {
    try {
      const cookies = await this.scraper.getCookies();
      await Bun.write(this.cookiesPath, JSON.stringify(cookies, null, 2));
    } catch (error) {
      this.logError("Error saving cookies", error);
      throw error;
    }
  }

  private async handleRateLimit(error: any): Promise<void> {
    if (error?.response?.status === 429) {
      const resetTime = error.response.headers?.["x-rate-limit-reset"];
      if (resetTime) {
        const waitTime = parseInt(resetTime) * 1000 - Date.now();
        this.logDebug(`Rate limited. Waiting ${waitTime / 1000} seconds...`);
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      } else {
        // If no reset time, wait 15 minutes
        this.logDebug("Rate limited. Waiting 15 minutes...");
        await new Promise((resolve) => setTimeout(resolve, 15 * 60 * 1000));
      }
    }
  }

  private async respectRateLimit(type: "tweet" | "search"): Promise<void> {
    const now = Date.now();

    if (type === "tweet") {
      // Ensure minimum delay between tweets
      const timeSinceLastTweet = now - this.lastTweetTime;
      if (
        timeSinceLastTweet < TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS
      ) {
        await new Promise((resolve) =>
          setTimeout(
            resolve,
            TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS -
              timeSinceLastTweet
          )
        );
      }

      // Reset count every 15 minutes
      if (now - this.lastTweetTime > 15 * 60 * 1000) {
        this.tweetCount = 0;
      }

      // Check if we're approaching limits
      if (this.tweetCount >= TwitterService.RATE_LIMITS.TWEETS_PER_15_MIN) {
        const waitTime = 15 * 60 * 1000 - (now - this.lastTweetTime);
        this.logDebug(
          `Approaching tweet rate limit. Waiting ${waitTime / 1000} seconds...`
        );
        await new Promise((resolve) => setTimeout(resolve, waitTime));
        this.tweetCount = 0;
      }

      this.tweetCount++;
      this.lastTweetTime = now;
    }

    if (type === "search") {
      // Ensure minimum delay between searches
      const timeSinceLastSearch = now - this.lastSearchTime;
      if (
        timeSinceLastSearch <
        TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_SEARCHES
      ) {
        await new Promise((resolve) =>
          setTimeout(
            resolve,
            TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_SEARCHES -
              timeSinceLastSearch
          )
        );
      }

      // Reset count every 15 minutes
      if (now - this.lastSearchTime > 15 * 60 * 1000) {
        this.searchCount = 0;
      }

      // Check if we're approaching limits
      if (this.searchCount >= TwitterService.RATE_LIMITS.SEARCH_PER_15_MIN) {
        const waitTime = 15 * 60 * 1000 - (now - this.lastSearchTime);
        this.logDebug(
          `Approaching search rate limit. Waiting ${waitTime / 1000} seconds...`
        );
        await new Promise((resolve) => setTimeout(resolve, waitTime));
        this.searchCount = 0;
      }

      this.searchCount++;
      this.lastSearchTime = now;
    }
  }

  private async attemptLogin(): Promise<boolean> {
    if (!process.env.TWITTER_USERNAME || !process.env.TWITTER_PASSWORD) {
      throw new Error("Missing Twitter credentials");
    }

    await this.scraper.login(
      process.env.TWITTER_USERNAME,
      process.env.TWITTER_PASSWORD,
      process.env.TWITTER_EMAIL,
      process.env.TWITTER_2FA_SECRET
    );

    const isLoggedIn = await this.scraper.isLoggedIn();
    if (isLoggedIn) {
      await this.saveCookies();
      this.loginRetryAttempts = 0;
    }
    return isLoggedIn;
  }

  async initialize() {
    try {
      const cookies = await this.loadCookies();
      if (cookies.length > 0) {
        await this.scraper.setCookies(cookies);

        if (await this.scraper.isLoggedIn()) {
          this.logDebug("Successfully initialized with cookies");
          return;
        }
      }

      if (await this.attemptLogin()) {
        this.logDebug("Successfully initialized with login");
        return;
      }

      throw new Error("Failed to login with both cookies and credentials");
    } catch (error) {
      this.logError("Error initializing Twitter service", error);
      await this.logToDatabase(
        `Error initializing Twitter service: ${
          error instanceof Error ? error.message : String(error)
        }`
      );
      throw error;
    }
  }

  private async ensureLoggedIn(): Promise<void> {
    if (!(await this.scraper.isLoggedIn())) {
      if (this.loginRetryAttempts >= this.MAX_LOGIN_RETRIES) {
        throw new Error("Maximum login retry attempts reached");
      }
      this.loginRetryAttempts++;
      await this.initialize();
    }
  }

  protected async logToDatabase(message: string, speaker = "System") {
    try {
      await db.insert(duckyAi).values({
        content: message,
        timestamp: new Date().toISOString(),
        speaker,
        posted: false,
      });
    } catch (error) {
      this.logError("Error logging to database", error);
    }
  }

  public async tweetExists(tweetId: string): Promise<boolean> {
    try {
      await this.respectRateLimit("search");
      const tweet = await this.scraper.getTweet(tweetId);
      return !!tweet;
    } catch {
      return false;
    }
  }

  private async getAuthorFollowers(userId: string): Promise<number> {
    try {
      await this.respectRateLimit("search");
      const profile = await this.scraper.getProfile(userId);
      return profile.followersCount || 0;
    } catch {
      return 0;
    }
  }

  public async searchConversation(tweetId: string): Promise<TwitterReply[]> {
    try {
      await this.respectRateLimit("search");

      // First get the original tweet
      const tweetObj = await this.scraper.getTweet(tweetId);
      if (!tweetObj) {
        this.logDebug(`Tweet ${tweetId} not found`);
        return [];
      }

      const username = tweetObj.username;
      if (!username) {
        this.logDebug(`No username found for tweet ${tweetId}`);
        return [];
      }

      // Search for replies using both username and conversation_id
      const searchQuery = `to:${username} conversation_id:${tweetId}`;
      this.logDebug(`Searching with query: ${searchQuery}`);

      try {
        const results = await this.scraper.fetchSearchTweets(
          searchQuery,
          100,
          SearchMode.Latest
        );

        // Transform tweets to TwitterReply format
        const replies = await Promise.all(
          results.tweets
            .filter((tweet) => tweet.inReplyToStatusId === tweetId)
            .map(async (tweet) => ({
              id: tweet.id || "",
              author: tweet.username || "",
              text: tweet.text || "",
              created_at:
                tweet.timeParsed?.toISOString() || new Date().toISOString(),
              likes: tweet.likes || 0,
              retweets: tweet.retweets || 0,
              author_followers: tweet.userId
                ? await this.getAuthorFollowers(tweet.userId)
                : 0,
              author_verified: false,
            }))
        );

        this.logDebug(`Found ${replies.length} replies for tweet ${tweetId}`);
        return replies;
      } catch (error: any) {
        if (error?.response?.status === 429) {
          await this.handleRateLimit(error);
          // Retry once after rate limit
          return this.searchConversation(tweetId);
        }
        throw error;
      }
    } catch (error) {
      this.logError(`Error searching conversation for tweet ${tweetId}`, error);
      return [];
    }
  }

  public async getConversationMetrics(tweetId: string): Promise<{
    replyCount: number;
    participantCount: number;
    averageEngagement: number;
  }> {
    try {
      const replies = await this.searchConversation(tweetId);
      const participants = new Set(replies.map((r) => r.author));
      const totalEngagement = replies.reduce(
        (sum, reply) => sum + (reply.likes || 0) + (reply.retweets || 0),
        0
      );

      return {
        replyCount: replies.length,
        participantCount: participants.size,
        averageEngagement: replies.length
          ? totalEngagement / replies.length
          : 0,
      };
    } catch (error) {
      this.logError(
        `Error getting conversation metrics for tweet ${tweetId}`,
        error
      );
      return {
        replyCount: 0,
        participantCount: 0,
        averageEngagement: 0,
      };
    }
  }

  async sendTweet(content: string): Promise<TweetResponse> {
    try {
      await this.respectRateLimit("tweet");
      await this.ensureLoggedIn();

      const response = await this.scraper.sendTweet(content);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Twitter API error: ${response.status} ${errorText}`);
      }

      const tweetId = await this.extractTweetId(response);
      const tweetUrl = `https://twitter.com/i/status/${tweetId}`;

      await this.saveTweetToDatabase(content, tweetId);
      await this.sendTelegramNotification(content, tweetUrl);

      return { success: true, url: tweetUrl };
    } catch (error: any) {
      if (error?.response?.status === 429) {
        await this.handleRateLimit(error);
        // Retry once after rate limit
        return this.sendTweet(content);
      }
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      this.logError("Error sending tweet", error);
      await this.logToDatabase(`Error sending tweet: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }

  async sendReply(
    content: string,
    replyToTweetId: string
  ): Promise<TweetResponse> {
    try {
      await this.respectRateLimit("tweet");
      await this.ensureLoggedIn();

      const response = await this.scraper.sendTweet(content, replyToTweetId);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Twitter API error: ${response.status} ${errorText}`);
      }

      const tweetId = await this.extractTweetId(response);
      const tweetUrl = `https://twitter.com/i/status/${tweetId}`;

      await this.saveTweetToDatabase(content, tweetId, replyToTweetId);
      //await this.sendTelegramNotification(content, tweetUrl, replyToTweetId);

      return { success: true, url: tweetUrl };
    } catch (error: any) {
      if (error?.response?.status === 429) {
        await this.handleRateLimit(error);
        // Retry once after rate limit
        return this.sendReply(content, replyToTweetId);
      }
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      this.logError("Error sending reply", error);
      await this.logToDatabase(`Error sending reply: ${errorMessage}`);
      return { success: false, error: errorMessage };
    }
  }

  private async extractTweetId(response: Response): Promise<string> {
    try {
      const data = await response.json();
      const tweetId =
        data?.rest_id ||
        data?.data?.tweet?.rest_id ||
        data?.data?.create_tweet?.tweet_results?.result?.rest_id;

      if (!tweetId) {
        throw new Error("Could not find tweet ID in response");
      }

      return tweetId;
    } catch (error) {
      this.logError("Error extracting tweet ID from response", error);
      throw new Error("Failed to extract tweet ID from response");
    }
  }

  private async saveTweetToDatabase(
    content: string,
    tweetId: string,
    replyToTweetId?: string
  ) {
    try {
      await db.insert(duckyAi).values({
        content,
        tweetId,
        postTime: new Date().toISOString(),
        posted: true,
        timestamp: new Date().toISOString(),
        conversationId: replyToTweetId,
        speaker: "Ducky",
      });
    } catch (error) {
      this.logError("Error saving tweet to database", error);
      // Don't throw - this is non-critical
    }
  }

  protected async sendTelegramNotification(
    content: string,
    tweetUrl: string,
    replyTweetUrl?: string
  ) {
    if (!this.telegramBotToken || !this.targetChannelId) return;

    const message = replyTweetUrl
      ? `🦆 Replying...\n\n'${content}'\n\n${tweetUrl}\n\n`
      : `🦆 Tweeting...\n\n'${content}'\n\n${tweetUrl}`;

    try {
      await axios.post(
        `https://api.telegram.org/bot${this.telegramBotToken}/sendMessage`,
        {
          chat_id: this.targetChannelId,
          text: message,
          disable_web_page_preview: false,
        }
      );
    } catch (error) {
      this.logError("Error sending Telegram notification", error);
      // Don't throw - this is non-critical
    }
  }

  // Utility methods for handling bulk operations
  public async processBatchWithRateLimits<T>(
    items: T[],
    processor: (item: T) => Promise<void>,
    type: "tweet" | "search"
  ): Promise<void> {
    for (const item of items) {
      try {
        await this.respectRateLimit(type);
        await processor(item);
      } catch (error: any) {
        if (error?.response?.status === 429) {
          await this.handleRateLimit(error);
          // Retry this item
          await this.respectRateLimit(type);
          await processor(item);
        } else {
          this.logError(`Error processing batch item`, error);
          // Continue with next item
        }
      }
    }
  }

  // Method to check account status and limits
  public async getAccountStatus(): Promise<{
    isLoggedIn: boolean;
    tweetCount: number;
    searchCount: number;
    remainingTweets: number;
    remainingSearches: number;
  }> {
    const now = Date.now();
    const timeInWindow =
      now - Math.max(this.lastTweetTime, now - 15 * 60 * 1000);
    const remainingTweets =
      TwitterService.RATE_LIMITS.TWEETS_PER_15_MIN -
      (timeInWindow < 15 * 60 * 1000 ? this.tweetCount : 0);
    const remainingSearches =
      TwitterService.RATE_LIMITS.SEARCH_PER_15_MIN -
      (timeInWindow < 15 * 60 * 1000 ? this.searchCount : 0);

    return {
      isLoggedIn: await this.scraper.isLoggedIn(),
      tweetCount: this.tweetCount,
      searchCount: this.searchCount,
      remainingTweets,
      remainingSearches,
    };
  }

  // Method to check if we can perform operations
  public async canPerformOperations(): Promise<{
    canTweet: boolean;
    canSearch: boolean;
    waitTimeForTweet: number;
    waitTimeForSearch: number;
  }> {
    const now = Date.now();

    const tweetWaitTime = Math.max(
      0,
      TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS -
        (now - this.lastTweetTime)
    );

    const searchWaitTime = Math.max(
      0,
      TwitterService.RATE_LIMITS.MIN_DELAY_BETWEEN_SEARCHES -
        (now - this.lastSearchTime)
    );

    const status = await this.getAccountStatus();

    return {
      canTweet: status.remainingTweets > 0 && tweetWaitTime === 0,
      canSearch: status.remainingSearches > 0 && searchWaitTime === 0,
      waitTimeForTweet: tweetWaitTime,
      waitTimeForSearch: searchWaitTime,
    };
  }

  // Method to reset rate limiting counters
  public resetRateLimits(): void {
    this.tweetCount = 0;
    this.searchCount = 0;
    this.lastTweetTime = 0;
    this.lastSearchTime = 0;
    this.logDebug("Rate limits have been reset");
  }

  // Method to get the scraper instance (useful for direct access when needed)
  public getScraper(): Scraper {
    return this.scraper;
  }
}

// Export a singleton instance
let twitterServiceInstance: TwitterService | null = null;

export async function getTwitterService(): Promise<TwitterService> {
  if (!twitterServiceInstance) {
    twitterServiceInstance = new TwitterService();
    await twitterServiceInstance.initialize();
  }
  return twitterServiceInstance;
}

// Export types and constants
export { SearchMode };
export type { TweetResponse, TwitterReply };
