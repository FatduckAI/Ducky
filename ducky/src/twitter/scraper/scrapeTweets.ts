import { db } from "@/db";
import { finetuneTweets } from "@/db/schema";
import { ServiceInitializer } from "../../delivery/twitter.init";

export async function scrapeTweets() {
  const scraper = await ServiceInitializer.initialize();
  const tweets = [];
  for await (const tweet of scraper.getTweets("DuckUnfiltered", 1000)) {
    tweets.push(tweet);
  }
  // save to db
  await db
    .insert(finetuneTweets)
    .values(
      tweets.map((t) => ({
        content: t.text ?? "",
        tweetId: t.id,
        userId: t.userId ?? "",
        timestamp: t.timestamp?.toString() ?? new Date().toISOString(),
      }))
    )
    .onConflictDoNothing();
}

await scrapeTweets().then(() => console.log("done"));
