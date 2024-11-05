import { db } from "@/db";
import { telegramMessages } from "@/db/schema";
import { generateTogetherResponse } from "@/src/lib/together";
import { sql } from "drizzle-orm";

interface ContributorMetrics {
  senderUsername: string;
  messageCount: number;
  averagePositive: number;
  averageNegative: number;
  averageHelpful: number;
  averageSarcastic: number;
  positiveMessageCount: number;
  totalSentimentScore: number;
  lastMessageTimestamp: Date;
}

async function getTopContributors(): Promise<ContributorMetrics[]> {
  // Get metrics for each contributor
  const fiveDaysAgo = new Date();
  fiveDaysAgo.setDate(fiveDaysAgo.getDate() - 5);

  const contributorMetrics = await db
    .select({
      senderUsername: telegramMessages.senderUsername,
      messageCount: sql<number>`count(*)`,
      averagePositive: sql<number>`avg(${telegramMessages.sentimentPositive})`,
      averageNegative: sql<number>`avg(${telegramMessages.sentimentNegative})`,
      averageHelpful: sql<number>`avg(${telegramMessages.sentimentHelpful})`,
      averageSarcastic: sql<number>`avg(${telegramMessages.sentimentSarcastic})`,
      positiveMessageCount: sql<number>`sum(case when ${telegramMessages.sentimentPositive} > 0.6 then 1 else 0 end)`,
      // Calculate total sentiment score (weighted average)
      totalSentimentScore: sql<number>`
        avg(
          (${telegramMessages.sentimentPositive} * 2) + 
          (${telegramMessages.sentimentHelpful}) -
          (${telegramMessages.sentimentNegative} * 2) -
          (${telegramMessages.sentimentSarcastic})
        )
      `,
      lastMessageTimestamp: sql<Date>`max(${telegramMessages.timestamp})`,
    })
    .from(telegramMessages)
    .where(
      sql`${telegramMessages.sentimentAnalyzed} = true AND 
      EXISTS (
        SELECT 1 
        FROM ${telegramMessages} recent 
        WHERE recent.sender_username = ${telegramMessages.senderUsername}
        AND recent.timestamp >= ${fiveDaysAgo.toISOString()}
        AND recent.sender_username != 'Cryptoinfluence99'
        AND recent.sender_username != 'zeroxglu'
      )`
    )
    .groupBy(telegramMessages.senderUsername)
    .having(sql`count(*) >= 20`) // Minimum 10 messages to be considered
    .orderBy(sql`count(*) desc`);

  return contributorMetrics as ContributorMetrics[];
}

async function analyzeTopContributors(
  metrics: ContributorMetrics[]
): Promise<{ response: string; winners: string[] }> {
  // Format the data for Claude
  const top3Data = metrics
    .map(
      (m, index) => `
Contributor ${index + 1}: ${m.senderUsername}
- Total Messages: ${m.messageCount}
- Positive Messages: ${m.positiveMessageCount}
- Average Sentiments:
  * Positive: ${(m.averagePositive * 100).toFixed(1)}%
  * Negative: ${(m.averageNegative * 100).toFixed(1)}%
  * Helpful: ${(m.averageHelpful * 100).toFixed(1)}%
  * Sarcastic: ${(m.averageSarcastic * 100).toFixed(1)}%
- Total Sentiment Score: ${m.totalSentimentScore.toFixed(2)}
- Last Active: ${m.lastMessageTimestamp.toLocaleString()}
`
    )
    .join("\n");

  const systemPrompt = `You are analyzing Telegram community contributors to select the top 5 most valuable community members. 
Focus on both quantity (message count) and quality (sentiment scores) of contributions. A large number of messages shows engagement, and the sentiment scores show the quality of the contributions.
Explain your choices briefly but clearly. Ensure to regard the quantity of the contributions higher than the sentiment scores.`;

  const userPrompt = `Here are the top 5 contributors by message volume. Please analyze their metrics and select 5 winners based on the criteria:

${top3Data}

Return your response in this exact format:
🚨 Weekly Engagers 🚨:
These 5 users went above and beyond this past week. Check the telegram to claim your 69,000 $DUCKAI!
1. [username] - [summary of reasons for selection]
2. [username] - [summary of reasons for selection]
3. [username] - [summary of reasons for selection]
4. [username] - [summary of reasons for selection]
5. [username] - [summary of reasons for selection]

`;

  const response = await generateTogetherResponse(systemPrompt, userPrompt);
  // Extract usernames from Claude's response
  const lines = response.split("\n");
  const winners = lines
    .filter((line) => line.includes("."))
    .map((line) =>
      line
        .split("-")[0]
        .trim()
        .replace(/^\d+\.\s*/, "")
    );

  return { response, winners };
}

export async function findTopContributors() {
  try {
    console.log("Fetching top 50 contributors...");
    const topContributors = await getTopContributors();

    console.log("Analyzing top contributors with Together...");
    const selectedContributors = await analyzeTopContributors(topContributors);

    return {
      allTopContributors: topContributors,
      selectedContributors: selectedContributors,
    };
  } catch (error) {
    console.error("Error in findTopContributors:", error);
    throw error;
  }
}

export const main = async () => {
  const results = await findTopContributors();
  console.log(results.selectedContributors.response);
};

//main();
