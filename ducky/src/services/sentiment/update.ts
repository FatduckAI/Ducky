import { db } from "@/db";
import { telegramMessages } from "@/db/schema";
import { processSentimentBatchWithComparison } from "@/src/lib/together.sentiment";
import { desc, eq, sql } from "drizzle-orm";

async function recalculateAllSentiments() {
  const batchSize = 100; // DB batch size
  let processed = 0;

  try {
    const totalMessages = await db
      .select({ count: sql<number>`count(*)` })
      .from(telegramMessages)
      .execute();

    const total = totalMessages[0].count;
    console.log(`Starting sentiment recalculation for ${total} messages`);

    while (true) {
      // Fetch batch from DB
      const messages = await db
        .select()
        .from(telegramMessages)
        .orderBy(desc(telegramMessages.timestamp))
        .limit(batchSize)
        .offset(processed)
        .execute();

      if (messages.length === 0) break;

      // Get existing scores for comparison
      const previousScores = messages.map(
        (msg) =>
          [
            msg.sentimentPositive ?? 0.5,
            msg.sentimentNegative ?? 0.5,
            msg.sentimentHelpful ?? 0.5,
            msg.sentimentSarcastic ?? 0.5,
          ] as [number, number, number, number]
      );

      // Process batch with rate limiting
      const { results, errors, changes } =
        await processSentimentBatchWithComparison(
          messages.map((m) => m.content ?? ""),
          previousScores,
          { maxRequestsPerMinute: 55, logProgress: true }
        );

      // Update DB in parallel
      await Promise.all(
        results.map(async (scores, index) => {
          if (!messages[index].content) return;

          await db
            .update(telegramMessages)
            .set({
              sentimentPositive: scores[0],
              sentimentNegative: scores[1],
              sentimentHelpful: scores[2],
              sentimentSarcastic: scores[3],
              sentimentAnalyzed: true,
            })
            .where(eq(telegramMessages.messageId, messages[index].messageId))
            .execute();
        })
      );

      processed += messages.length;
      console.log(`\nBatch complete: ${processed}/${total} messages processed`);
      console.log(`Errors in this batch: ${errors.length}`);
      console.log(`Changes in this batch: ${changes.length}`);
    }

    console.log("\nRecalculation complete!");
    console.log(`Total messages processed: ${processed}`);
  } catch (error) {
    console.error("Fatal error during recalculation:", error);
    throw error;
  }
}

recalculateAllSentiments();
