import { Scraper } from "agent-twitter-client";
import { desc, eq } from "drizzle-orm";
import { db } from "../../db";
import { duckyAi } from "../../db/schema";
import type { DeliverySystem } from "../agent/types";

export class TwitterDeliveryService implements DeliverySystem {
  type: "twitter" = "twitter";
  private scraper: Scraper;
  private static instance: TwitterDeliveryService;
  private lastTweetTime: number = 0;

  private static readonly RATE_LIMITS = {
    TWEETS_PER_HOUR: 50,
    TWEETS_PER_15_MIN: 15,
    MIN_DELAY_BETWEEN_TWEETS: 3000,
  };

  private constructor(scraper: Scraper) {
    this.scraper = scraper;
  }

  public static getInstance(scraper: Scraper): TwitterDeliveryService {
    if (!TwitterDeliveryService.instance) {
      TwitterDeliveryService.instance = new TwitterDeliveryService(scraper);
    }
    return TwitterDeliveryService.instance;
  }

  private async logToDatabase(message: string, speaker = "System") {
    try {
      await db.insert(duckyAi).values({
        content: message,
        timestamp: new Date().toISOString(),
        speaker,
        posted: false,
      });
    } catch (error) {
      console.error("Error logging to database:", error);
    }
  }

  private async respectRateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastTweet = now - this.lastTweetTime;

    if (
      timeSinceLastTweet <
      TwitterDeliveryService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS
    ) {
      await new Promise((resolve) =>
        setTimeout(
          resolve,
          TwitterDeliveryService.RATE_LIMITS.MIN_DELAY_BETWEEN_TWEETS -
            timeSinceLastTweet
        )
      );
    }
  }

  private async extractTweetId(response: Response): Promise<string> {
    const data = await response.json();

    // Log the response structure for debugging
    console.log("Twitter API Response:", JSON.stringify(data, null, 2));

    // Try all possible paths to find the tweet ID
    const tweetId =
      // New Twitter API v2 path
      data?.data?.id ||
      // Legacy API path
      data?.rest_id ||
      // Alternative v2 paths
      data?.data?.tweet?.id ||
      data?.data?.create_tweet?.tweet_id ||
      // Nested results path
      data?.data?.create_tweet?.tweet_results?.result?.rest_id ||
      // Deep nested path for quoted/replied tweets
      data?.data?.create_tweet?.tweet_results?.result?.tweet?.rest_id;

    if (!tweetId) {
      console.error("Failed to extract tweet ID from response:", data);
      throw new Error(
        "Could not find tweet ID in response. Response structure: " +
          JSON.stringify(data, null, 2)
      );
    }

    return tweetId;
  }

  async send(content: string, replyToTweetId?: string): Promise<string> {
    try {
      await this.respectRateLimit();

      const response = await this.scraper.sendTweet(content, replyToTweetId);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Twitter API error: ${response.status} ${errorText}`);
      }

      const tweetId = await this.extractTweetId(response);
      const tweetUrl = `https://twitter.com/i/status/${tweetId}`;

      // Save to database
      await db.insert(duckyAi).values({
        content,
        tweetId,
        postTime: new Date().toISOString(),
        posted: true,
        timestamp: new Date().toISOString(),
        conversationId: replyToTweetId,
        speaker: "Ducky",
      });

      await this.logToDatabase(`Successfully posted tweet: ${tweetUrl}`);
      this.lastTweetTime = Date.now();
      return tweetId;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      await this.logToDatabase(`Error sending tweet: ${errorMessage}`);
      throw error;
    }
  }

  async getRecentMessages(): Promise<string[]> {
    try {
      const tweets = await db
        .select({
          content: duckyAi.content,
        })
        .from(duckyAi)
        .where(eq(duckyAi.speaker, "Ducky"))
        .orderBy(desc(duckyAi.timestamp))
        .limit(50);

      return tweets.map((t) => t.content);
    } catch (error) {
      console.error("Error getting recent messages:", error);
      return [];
    }
  }
}
