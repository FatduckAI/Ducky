import { db } from "../../db";
import { duckyAi } from "../../db/schema";
import { getDuckyAiForTweetGeneration } from "../../db/utils";
import { ducky, generatePrompt } from "../ducky/character";
import { generateClaudeResponse } from "../lib/anthropic";
import { getTwitterService } from "./index";

class SingleTweetBot {
  private readonly testMode: boolean;

  constructor(testModeEnv?: string) {
    // Convert string environment variable to boolean
    this.testMode = testModeEnv?.toLowerCase() === "true";
    this.logDebug(`Initialized in ${this.testMode ? "TEST" : "LIVE"} mode`);
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

  public async tweet(): Promise<void> {
    try {
      // Log start to database
      await this.logToDatabase(
        `Starting Single Tweet Bot (${
          this.testMode ? "TEST MODE" : "LIVE MODE"
        })`,
        "System"
      );

      // Generate the tweet
      const tweets = await getDuckyAiForTweetGeneration();
      const prompt = generatePrompt.forTweet(
        tweets.map((tweet) => tweet.content)
      );
      const tweetContent = await generateClaudeResponse(
        prompt,
        ducky.prompts.tweet.user
      );

      // Log the tweet generation
      await this.logToDatabase(`Generated tweet: "${tweetContent}"`, "System");

      if (this.testMode) {
        this.logDebug("TEST MODE - Would tweet:", { content: tweetContent });
        return;
      }

      // Send the tweet
      const twitterService = await getTwitterService();
      const tweetResponse = await twitterService.sendTweet(tweetContent);

      if (tweetResponse.success && tweetResponse.url) {
        // Log success to database
        await this.logToDatabase(
          `Successfully posted tweet: ${tweetResponse.url}`,
          "System"
        );
      } else {
        throw new Error("Failed to post tweet");
      }
    } catch (error) {
      this.logError("Error in single tweet bot", error);

      // Log error to database
      await this.logToDatabase(
        `Error in Single Tweet Bot: ${
          error instanceof Error ? error.message : String(error)
        }`,
        "System"
      );

      throw error;
    }
  }
}

// Export default instance
export const singleTweetBot = new SingleTweetBot(process.env.TEST_MODE);

async function main() {
  try {
    await singleTweetBot.tweet();
    await new Promise((resolve) => setTimeout(resolve, 1000));
    process.exit(0);
  } catch (error) {
    console.error("Fatal error:", error);
    process.exit(1);
  }
}

process.on("SIGTERM", () => {
  console.log("Received SIGTERM signal. Exiting...");
  process.exit(0);
});

process.on("SIGINT", () => {
  console.log("Received SIGINT signal. Exiting...");
  process.exit(0);
});

main().catch((error) => {
  console.error("Uncaught error in main:", error);
  process.exit(1);
});
