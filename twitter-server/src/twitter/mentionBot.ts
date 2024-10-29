import { and, eq } from "drizzle-orm";
import { db } from "../../db";
import { duckyAi, mentionedTweets } from "../../db/schema";
import { saveMessageToDb } from "../../db/utils";
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

  // Search Keywords
  SEARCH_QUERIES: ["@duckunfiltered", "$DUCKAI"],

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

export class MentionBot {
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

  private shouldContinueProcessing(): boolean {
    const timeRunning = Date.now() - this.startTime;
    return (
      this.isProcessing &&
      timeRunning < CONFIG.MAX_RUN_TIME &&
      this.processedCount < CONFIG.MAX_TOTAL_REPLIES_PER_RUN &&
      this.rateLimit.isWithinLimits
    );
  }

  private async searchMentions(
    twitterService: TwitterService,
    query: string
  ): Promise<
    Array<{
      id: string;
      author: string;
      text: string;
      created_at: string;
      likes: number;
      retweets: number;
      author_followers: number;
      author_verified: boolean;
    }>
  > {
    if (!this.rateLimit.searchesRemaining) {
      this.logDebug("Search rate limit reached for this run");
      return [];
    }

    try {
      this.logDebug(`Searching for query: ${query}`);
      this.rateLimit.incrementSearch();

      const results = await twitterService.searchMentionsAndKeywords(query);

      const mentions = results.tweets;

      this.logDebug(`Found ${mentions.length} mentions/keywords to process`, {
        query,
        rateLimitStats: this.rateLimit.stats,
      });

      return mentions;
    } catch (error) {
      this.logError(`Error searching mentions for query ${query}`, error);
      return [];
    }
  }

  private async processMention(
    twitterService: TwitterService,
    mention: {
      id: string;
      author: string;
      text: string;
      created_at: string;
      likes: number;
      retweets: number;
      author_followers: number;
      author_verified: boolean;
    },
    searchQuery: string
  ): Promise<boolean> {
    if (!this.rateLimit.tweetsRemaining) {
      this.logDebug("Tweet rate limit reached for this run");
      return false;
    }

    try {
      this.logDebug(`Processing mention ${mention.id}`, {
        mentionDetails: mention,
        rateLimitStats: this.rateLimit.stats,
      });

      if (!this.testMode) {
        const processed = await db
          .select()
          .from(mentionedTweets)
          .where(
            and(
              eq(mentionedTweets.id, mention.id),
              eq(mentionedTweets.processed, true)
            )
          )
          .limit(1);

        if (processed.length > 0) {
          this.logDebug(`Mention ${mention.id} already processed`);
          return true;
        }

        await db
          .insert(mentionedTweets)
          .values({
            id: mention.id,
            text: mention.text,
            author: mention.author,
            authorUsername: mention.author,
            createdAt: new Date(mention.created_at),
            likes: mention.likes,
            retweets: mention.retweets,
            authorFollowers: mention.author_followers,
            authorVerified: mention.author_verified,
            processed: false,
            createdTimestamp: new Date(),
            searchQuery,
            mentionType: searchQuery.startsWith("@") ? "username" : "keyword",
          })
          .onConflictDoNothing();
      }

      const prompt = generatePrompt.forMention(mention.text, searchQuery);
      const response = await generateClaudeResponse(
        prompt,
        ducky.prompts.mention.user
      );

      await this.logToDatabase(
        `Generated reply to ${searchQuery} from @${mention.author}: "${response}"`,
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
            mention.id
          );

          if (tweetResponse.success && tweetResponse.url) {
            const responseId = tweetResponse.url.match(/\/status\/(\d+)/)?.[1];
            if (responseId) {
              await db
                .update(mentionedTweets)
                .set({
                  processed: true,
                  responseTweetId: responseId,
                  processedAt: new Date(),
                })
                .where(eq(mentionedTweets.id, mention.id));

              this.processedCount++;

              await this.logToDatabase(
                `Successfully replied to ${searchQuery} mention ${mention.id} from @${mention.author} (${this.processedCount}/${CONFIG.MAX_TOTAL_REPLIES_PER_RUN})`,
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
      this.logError(`Error processing mention ${mention.id}`, error);
      return false;
    }
  }

  public async start(): Promise<void> {
    if (this.isProcessing) {
      this.logDebug("Mention bot is already running");
      return;
    }

    this.isProcessing = true;
    this.startTime = Date.now();
    this.processedCount = 0;
    this.rateLimit.reset();

    try {
      await this.logToDatabase(
        `Starting Mention Bot (${
          this.testMode ? "TEST MODE" : "LIVE MODE"
        }) - Max replies: ${CONFIG.MAX_TOTAL_REPLIES_PER_RUN}, Max run time: ${
          CONFIG.MAX_RUN_TIME / 1000 / 60
        } minutes`,
        "System"
      );

      const twitterService = await getTwitterService();

      for (
        let i = 0;
        i < CONFIG.SEARCH_QUERIES.length && this.shouldContinueProcessing();
        i += CONFIG.BATCH_SIZE
      ) {
        const batchQueries = CONFIG.SEARCH_QUERIES.slice(
          i,
          i + CONFIG.BATCH_SIZE
        );
        this.logDebug(
          `Processing query batch ${Math.floor(i / CONFIG.BATCH_SIZE) + 1}`,
          {
            batchSize: batchQueries.length,
            rateLimitStats: this.rateLimit.stats,
          }
        );

        for (const query of batchQueries) {
          if (!this.shouldContinueProcessing()) break;

          const mentions = await this.searchMentions(twitterService, query);

          for (const mention of mentions) {
            if (!this.shouldContinueProcessing()) break;
            await this.processMention(twitterService, mention, query);
          }

          await this.wait(1000);
        }

        if (
          this.shouldContinueProcessing() &&
          i + CONFIG.BATCH_SIZE < CONFIG.SEARCH_QUERIES.length
        ) {
          await this.wait(CONFIG.BATCH_DELAY);
        }
      }

      const runtime = (Date.now() - this.startTime) / 1000;

      await this.logToDatabase(
        `Mention Bot run completed (${
          this.testMode ? "TEST MODE" : "LIVE MODE"
        }) - Runtime: ${runtime}s, Processed mentions: ${
          this.processedCount
        }, Rate limits: ${this.rateLimit.stats}`,
        "System"
      );
    } catch (error) {
      this.logError("Error in mention bot", error);

      await this.logToDatabase(
        `Error in Mention Bot: ${
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
      `Stopping mention bot (${this.testMode ? "TEST MODE" : "LIVE MODE"})`,
      {
        rateLimitStats: this.rateLimit.stats,
      }
    );

    await this.logToDatabase(
      `Stopping Mention Bot (${this.testMode ? "TEST MODE" : "LIVE MODE"}) - ${
        this.rateLimit.stats
      }`,
      "System"
    );

    this.isProcessing = false;
  }
}

// Export default instance
export const mentionBot = new MentionBot(process.env.TEST_MODE === "true");

// Modify the main execution to handle process exit
async function main() {
  try {
    await mentionBot.start();
    // Give a small delay to ensure all logs are written
    await new Promise((resolve) => setTimeout(resolve, 1000));
    process.exit(0);
  } catch (error) {
    console.error("Fatal error:", error);
    process.exit(1);
  }
}

// Add handlers for graceful shutdown
process.on("SIGTERM", async () => {
  console.log("Received SIGTERM signal. Stopping bot...");
  await mentionBot.stop();
  process.exit(0);
});

process.on("SIGINT", async () => {
  console.log("Received SIGINT signal. Stopping bot...");
  await mentionBot.stop();
  process.exit(0);
});

// Run the bot
main().catch((error) => {
  console.error("Uncaught error in main:", error);
  process.exit(1);
});
