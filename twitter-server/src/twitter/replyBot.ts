import { and, eq } from "drizzle-orm";
import { db } from "../../db";
import { duckyAi, tweetReplies } from "../../db/schema";
import { getDuckyAiTweets, saveMessageToDb } from "../../db/utils";
import type { TwitterReply } from "../../types";
import { ducky, generatePrompt } from "../ducky/character";
import { generateClaudeResponse } from "../lib/anthropic";
import { getTwitterService, TwitterService } from "./index";

const CONFIG = {
  // Twitter's rate limits
  MAX_TWEETS_PER_HOUR: 40, // Conservative from 50/hour limit
  MAX_SEARCH_PER_HOUR: 150, // Conservative from 180/15min limit

  // Processing limits
  BATCH_SIZE: 5,
  MAX_REPLIES_PER_TWEET: 5,
  MAX_TOTAL_REPLIES_PER_RUN: 30,

  // Delays
  MIN_DELAY_BETWEEN_REPLIES: 5000, // 5 seconds
  BATCH_DELAY: 30000, // 30 seconds

  // Retries
  MAX_RETRIES: 3,
  RETRY_DELAY: 5000,

  // Run time limits
  MAX_RUN_TIME: 45 * 60 * 1000, // 45 minutes
} as const;

class RateLimitTracker {
  private tweetCount: number = 0;
  private searchCount: number = 0;
  private startTime: number = Date.now();

  get isWithinLimits(): boolean {
    return (
      this.tweetCount < CONFIG.MAX_TWEETS_PER_HOUR &&
      this.searchCount < CONFIG.MAX_SEARCH_PER_HOUR
    );
  }

  get tweetsRemaining(): number {
    return CONFIG.MAX_TWEETS_PER_HOUR - this.tweetCount;
  }

  get searchesRemaining(): number {
    return CONFIG.MAX_SEARCH_PER_HOUR - this.searchCount;
  }

  incrementTweet(): void {
    this.tweetCount++;
  }

  incrementSearch(): void {
    this.searchCount++;
  }

  get stats(): string {
    const runtime = (Date.now() - this.startTime) / 1000;
    return `Runtime: ${runtime}s, Tweets: ${this.tweetCount}/${CONFIG.MAX_TWEETS_PER_HOUR}, Searches: ${this.searchCount}/${CONFIG.MAX_SEARCH_PER_HOUR}`;
  }

  reset(): void {
    this.tweetCount = 0;
    this.searchCount = 0;
    this.startTime = Date.now();
  }
}

export class ReplyBot {
  private dbSave: typeof saveMessageToDb;
  private isProcessing: boolean = false;
  private startTime: number = 0;
  private processedCount: number = 0;
  private rateLimit: RateLimitTracker;
  private readonly testMode: boolean;

  constructor(testMode: boolean = false) {
    this.dbSave = testMode ? this.mockSaveMessageToDb : saveMessageToDb;
    this.rateLimit = new RateLimitTracker();
    this.testMode = testMode;
  }

  private async mockSaveMessageToDb(
    message: string,
    speaker: string,
    delay: number
  ) {
    console.log("TEST MODE - Would save to DB:", { message, speaker, delay });
  }

  private async logToDatabase(message: string, speaker = "System") {
    if (!this.testMode) {
      await db.insert(duckyAi).values({
        content: message,
        timestamp: new Date().toISOString(),
        speaker,
        posted: false,
      });
    } else {
      console.log("TEST MODE - Would log to DB:", { message, speaker });
    }
  }

  private async wait(ms: number): Promise<void> {
    if (!this.testMode) {
      await new Promise((resolve) => setTimeout(resolve, ms));
    }
  }

  private logDebug(message: string, data?: any) {
    const timestamp = new Date().toISOString();
    console.log(`[DEBUG ${timestamp}] ${message}`);
    if (data) {
      console.dir(data, { depth: null, colors: true });
    }
  }

  private logError(message: string, error: any) {
    const timestamp = new Date().toISOString();
    console.error(`[ERROR ${timestamp}] ${message}`);
    console.error("Error details:", {
      name: error?.name,
      message: error?.message,
      stack: error?.stack,
      data: error?.data,
      status: error?.response?.status,
      statusText: error?.response?.statusText,
      responseData: error?.response?.data,
    });
  }

  private logTest(message: string, data?: any) {
    if (this.testMode) {
      console.log("\n[TEST MODE]", message);
      if (data) {
        console.dir(data, { depth: null, colors: true });
      }
    }
  }

  private shouldContinueProcessing(): boolean {
    const timeRunning = Date.now() - this.startTime;
    return (
      this.isProcessing &&
      timeRunning < CONFIG.MAX_RUN_TIME &&
      this.processedCount < CONFIG.MAX_TOTAL_REPLIES_PER_RUN &&
      this.rateLimit.isWithinLimits
    );
  }

  private extractTweetId(tweetIdOrUrl: string): string {
    const match =
      tweetIdOrUrl.match(/\/status\/(\d+)/) || tweetIdOrUrl.match(/^(\d+)$/);
    return match ? match[1] : tweetIdOrUrl;
  }

  private async searchReplies(
    twitterService: TwitterService,
    tweetId: string
  ): Promise<TwitterReply[]> {
    if (!this.rateLimit.searchesRemaining) {
      this.logDebug("Search rate limit reached for this run");
      return [];
    }

    try {
      this.logDebug(`Searching replies for tweet ${tweetId}`);
      this.rateLimit.incrementSearch();

      const exists = await twitterService.tweetExists(tweetId);
      if (!exists) {
        this.logDebug(`Tweet ${tweetId} not found or inaccessible`);
        return [];
      }

      const replies = await twitterService.searchConversation(tweetId);

      const sortedReplies = replies
        .sort(
          (a, b) =>
            (b.likes || 0) +
            (b.retweets || 0) -
            ((a.likes || 0) + (a.retweets || 0))
        )
        .slice(0, CONFIG.MAX_REPLIES_PER_TWEET);

      this.logDebug(
        `Found ${sortedReplies.length} relevant replies to process`,
        {
          totalFound: replies.length,
          processing: sortedReplies.length,
          rateLimitStats: this.rateLimit.stats,
        }
      );

      return sortedReplies;
    } catch (error) {
      this.logError(`Error searching replies for tweet ${tweetId}`, error);
      return [];
    }
  }

  private async processReply(
    twitterService: TwitterService,
    reply: TwitterReply,
    parentTweetId: string
  ): Promise<boolean> {
    if (!this.rateLimit.tweetsRemaining) {
      this.logDebug("Tweet rate limit reached for this run");
      return false;
    }

    try {
      this.logDebug(`Processing reply ${reply.id}`, {
        replyDetails: reply,
        rateLimitStats: this.rateLimit.stats,
      });

      if (!this.testMode) {
        const processed = await db
          .select()
          .from(tweetReplies)
          .where(
            and(eq(tweetReplies.id, reply.id), eq(tweetReplies.processed, true))
          )
          .limit(1);

        if (processed.length > 0) {
          this.logDebug(`Reply ${reply.id} already processed`);
          return true;
        }

        await db
          .insert(tweetReplies)
          .values({
            id: reply.id,
            text: reply.text,
            author: reply.author,
            createdAt: new Date(reply.created_at),
            likes: reply.likes,
            retweets: reply.retweets,
            authorFollowers: reply.author_followers,
            authorVerified: reply.author_verified,
            processed: false,
            createdTimestamp: new Date(),
            parentTweetId,
          })
          .onConflictDoNothing();
      }

      const prompt = generatePrompt.forReply(reply.text);
      const response = await generateClaudeResponse(
        prompt,
        ducky.prompts.reply.user
      );

      // Log the reply generation to database
      await this.logToDatabase(
        `Generated reply to @${reply.author}: "${response}"`,
        "System"
      );

      await this.wait(CONFIG.MIN_DELAY_BETWEEN_REPLIES);

      if (this.testMode) {
        this.rateLimit.incrementTweet();
        this.processedCount++;
        return true;
      }

      let attempts = 0;
      while (attempts < CONFIG.MAX_RETRIES) {
        try {
          this.rateLimit.incrementTweet();
          const tweetResponse = await twitterService.sendReply(
            response,
            reply.id
          );

          if (tweetResponse.success && tweetResponse.url) {
            const responseId = tweetResponse.url.match(/\/status\/(\d+)/)?.[1];
            if (responseId) {
              await db
                .update(tweetReplies)
                .set({
                  processed: true,
                  responseTweetId: responseId,
                  processedAt: new Date(),
                })
                .where(eq(tweetReplies.id, reply.id));

              this.processedCount++;

              // Log successful reply to database
              await this.logToDatabase(
                `Successfully replied to tweet ${reply.id} from @${reply.author} (${this.processedCount}/${CONFIG.MAX_TOTAL_REPLIES_PER_RUN})`,
                "System"
              );

              return true;
            }
          }
          break;
        } catch (error) {
          attempts++;
          if (attempts < CONFIG.MAX_RETRIES) {
            await this.wait(CONFIG.RETRY_DELAY * attempts);
          }
        }
      }

      return false;
    } catch (error) {
      this.logError(`Error processing reply ${reply.id}`, error);
      return false;
    }
  }

  public async start(): Promise<void> {
    if (this.isProcessing) {
      this.logDebug("Reply bot is already running");
      return;
    }

    this.isProcessing = true;
    this.startTime = Date.now();
    this.processedCount = 0;
    this.rateLimit.reset();

    try {
      // Log start to database
      await this.logToDatabase(
        `Starting Reply Bot (${
          this.testMode ? "TEST MODE" : "LIVE MODE"
        }) - Max replies: ${CONFIG.MAX_TOTAL_REPLIES_PER_RUN}, Max run time: ${
          CONFIG.MAX_RUN_TIME / 1000 / 60
        } minutes`,
        "System"
      );

      const twitterService = await getTwitterService();
      const recentTweets = await getDuckyAiTweets();

      this.logTest("Recent tweets to process:", recentTweets);

      for (
        let i = 0;
        i < recentTweets.length && this.shouldContinueProcessing();
        i += CONFIG.BATCH_SIZE
      ) {
        const batch = recentTweets.slice(i, i + CONFIG.BATCH_SIZE);
        this.logDebug(
          `Processing batch ${Math.floor(i / CONFIG.BATCH_SIZE) + 1}`,
          {
            batchSize: batch.length,
            rateLimitStats: this.rateLimit.stats,
          }
        );

        for (const tweet of batch) {
          if (!tweet.tweetId || !this.shouldContinueProcessing()) continue;

          const tweetId = this.extractTweetId(tweet.tweetId);
          const replies = await this.searchReplies(twitterService, tweetId);

          for (const reply of replies) {
            if (!this.shouldContinueProcessing()) break;
            await this.processReply(twitterService, reply, tweetId);
          }

          await this.wait(1000);
        }

        if (
          this.shouldContinueProcessing() &&
          i + CONFIG.BATCH_SIZE < recentTweets.length
        ) {
          await this.wait(CONFIG.BATCH_DELAY);
        }
      }

      const runtime = (Date.now() - this.startTime) / 1000;

      // Log completion to database
      await this.logToDatabase(
        `Reply Bot run completed (${
          this.testMode ? "TEST MODE" : "LIVE MODE"
        }) - Runtime: ${runtime}s, Processed replies: ${
          this.processedCount
        }, Rate limits: ${this.rateLimit.stats}`,
        "System"
      );
    } catch (error) {
      this.logError("Error in reply bot", error);

      // Log error to database
      await this.logToDatabase(
        `Error in Reply Bot: ${
          error instanceof Error ? error.message : String(error)
        }`,
        "System"
      );

      throw error;
    } finally {
      this.isProcessing = false;
    }
  }

  public async stop(): Promise<void> {
    this.logDebug(
      `Stopping reply bot (${this.testMode ? "TEST MODE" : "LIVE MODE"})`,
      {
        rateLimitStats: this.rateLimit.stats,
      }
    );

    // Log stop to database
    await this.logToDatabase(
      `Stopping Reply Bot (${this.testMode ? "TEST MODE" : "LIVE MODE"}) - ${
        this.rateLimit.stats
      }`,
      "System"
    );

    this.isProcessing = false;
  }
}

// Export default instance
export const replyBot = new ReplyBot(process.env.TEST_MODE === "false");

replyBot.start().catch(console.error);
