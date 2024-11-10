// export-tweets.ts
import { db } from "@/db";
import { finetuneTweets } from "@/db/schema";

async function exportTweetsToJsonl() {
  try {
    // Fetch all tweets
    const tweets = await db.select().from(finetuneTweets);

    // Convert to JSONL format
    const jsonLines = tweets
      .map((tweet) =>
        JSON.stringify({
          text: tweet.content,
          id: tweet.tweetId,
          user_id: tweet.userId,
          timestamp: tweet.timestamp,
        })
      )
      .join("\n");

    // Save to file
    await Bun.write("./src/twitter/scraper/tweets.jsonl", jsonLines);

    console.log(`Exported ${tweets.length} tweets to tweets.jsonl`);
  } catch (error) {
    console.error("Error exporting tweets:", error);
  }
}

// Run the export
exportTweetsToJsonl();
