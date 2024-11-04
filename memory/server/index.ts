import { env } from "bun";
import { and, avg, count, desc, eq, gte, sql } from "drizzle-orm";
import { db } from "../";
import { duckyAi, telegramMessages } from "../schema/schema";

// Configuration
const API_KEY = env.INTERNAL_API_KEY;
const PORT = parseInt(env.PORT || "3000");

// Helper functions
function verifyApiKey(apiKey: string | null): boolean {
  return apiKey === API_KEY;
}

// Route handlers
async function handleChatHistory(): Promise<Response> {
  try {
    const chatHistory = await db
      .select()
      .from(duckyAi)
      .orderBy(desc(duckyAi.timestamp))
      .limit(200);

    return new Response(
      JSON.stringify({
        messages: chatHistory.reverse(),
      }),
      {
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function handleSentimentStats(req: Request): Promise<Response> {
  try {
    const url = new URL(req.url);
    const days = parseInt(url.searchParams.get("days") || "30");
    const daysAgo = new Date();
    daysAgo.setDate(daysAgo.getDate() - days);

    const result = await db
      .select({
        total_messages: count(),
        avg_positive: avg(telegramMessages.sentimentPositive),
        avg_negative: avg(telegramMessages.sentimentNegative),
        avg_helpful: avg(telegramMessages.sentimentHelpful),
        avg_sarcastic: avg(telegramMessages.sentimentSarcastic),
      })
      .from(telegramMessages)
      .where(
        and(
          eq(telegramMessages.sentimentAnalyzed, true),
          gte(telegramMessages.timestamp, daysAgo)
        )
      );

    const stats = result[0];
    const sentimentBalance =
      (Number(stats?.avg_positive) || 0) - (Number(stats?.avg_negative) || 0);

    return new Response(
      JSON.stringify({
        ...stats,
        avg_sentiment_balance: sentimentBalance,
      }),
      {
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function handleDailyTrends(req: Request): Promise<Response> {
  try {
    const url = new URL(req.url);
    const days = parseInt(url.searchParams.get("days") || "30");
    const daysAgo = new Date();
    daysAgo.setDate(daysAgo.getDate() - days);

    const results = await db
      .select({
        date: sql<string>`DATE(${telegramMessages.timestamp})`,
        positive: avg(telegramMessages.sentimentPositive),
        negative: avg(telegramMessages.sentimentNegative),
        helpful: avg(telegramMessages.sentimentHelpful),
        sarcastic: avg(telegramMessages.sentimentSarcastic),
        message_count: count(),
      })
      .from(telegramMessages)
      .where(
        and(
          eq(telegramMessages.sentimentAnalyzed, true),
          gte(telegramMessages.timestamp, daysAgo)
        )
      )
      .groupBy(sql`DATE(${telegramMessages.timestamp})`)
      .orderBy(sql`DATE(${telegramMessages.timestamp})`);

    return new Response(JSON.stringify(results), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function handleHourlyPattern(): Promise<Response> {
  try {
    const results = await db
      .select({
        hour: sql<number>`EXTRACT(HOUR FROM ${telegramMessages.timestamp})::integer`,
        positive: avg(telegramMessages.sentimentPositive),
        negative: avg(telegramMessages.sentimentNegative),
        helpful: avg(telegramMessages.sentimentHelpful),
        sarcastic: avg(telegramMessages.sentimentSarcastic),
        message_count: count(),
      })
      .from(telegramMessages)
      .where(eq(telegramMessages.sentimentAnalyzed, true))
      .groupBy(sql`EXTRACT(HOUR FROM ${telegramMessages.timestamp})`)
      .orderBy(sql`EXTRACT(HOUR FROM ${telegramMessages.timestamp})`);

    return new Response(JSON.stringify(results), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function handleUserSentimentAnalysis(req: Request): Promise<Response> {
  try {
    const url = new URL(req.url);
    const minMessages = parseInt(url.searchParams.get("min_messages") || "10");

    const userStats = await db
      .select({
        username: telegramMessages.senderUsername,
        positive: avg(telegramMessages.sentimentPositive),
        negative: avg(telegramMessages.sentimentNegative),
        helpful: avg(telegramMessages.sentimentHelpful),
        sarcastic: avg(telegramMessages.sentimentSarcastic),
        message_count: count(),
        user_rank: sql<number>`ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC)`,
      })
      .from(telegramMessages)
      .where(
        and(
          eq(telegramMessages.sentimentAnalyzed, true),
          sql`${telegramMessages.senderUsername} IS NOT NULL`
        )
      )
      .groupBy(telegramMessages.senderUsername)
      .having(sql`count(*) >= ${minMessages}`)
      .limit(20);

    // Transform results to anonymize usernames and add sentiment balance
    const results = userStats.map((stat) => ({
      anonymous_username: `User${String(stat.user_rank).padStart(2, "0")}`,
      positive: stat.positive,
      negative: stat.negative,
      helpful: stat.helpful,
      sarcastic: stat.sarcastic,
      message_count: stat.message_count,
      sentiment_balance:
        (Number(stat.positive) || 0) - (Number(stat.negative) || 0),
    }));

    // Sort by sentiment balance
    results.sort((a, b) => b.sentiment_balance - a.sentiment_balance);

    return new Response(JSON.stringify(results), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// Server setup
Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    // API key verification for protected routes
    if (url.pathname !== "/api/health") {
      const apiKey = req.headers.get("x-api-key");
      if (!verifyApiKey(apiKey)) {
        return new Response(JSON.stringify({ error: "Invalid API Key" }), {
          status: 403,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    try {
      switch (url.pathname) {
        case "/api/chat_history":
          return await handleChatHistory();
        case "/api/daily_trends":
          return await handleDailyTrends(req);
        case "/api/hourly_pattern":
          return await handleHourlyPattern();
        case "/api/user_sentiment_analysis":
          return await handleUserSentimentAnalysis(req);
        case "/api/sentiment_stats":
          return await handleSentimentStats(req);
        case "/api/health":
          return new Response(JSON.stringify({ status: "ok" }), {
            headers: { "Content-Type": "application/json" },
          });
        default:
          return new Response("Not Found", { status: 404 });
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e) }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      });
    }
  },
});

console.log(`Server running at http://localhost:${PORT}`);
