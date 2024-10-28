import { NextResponse } from "next/server";

export async function GET(request: Request) {
  try {
    // Fetch all sentiment data in parallel
    const [dailyResponse, hourlyResponse, userResponse, statsResponse] =
      await Promise.all([
        fetch(`${process.env.API_URL}/api/daily_trends`, {
          headers: {
            "x-api-key": process.env.INTERNAL_API_KEY || "",
          },
        }),
        fetch(`${process.env.API_URL}/api/hourly_pattern`, {
          headers: {
            "x-api-key": process.env.INTERNAL_API_KEY || "",
          },
        }),
        fetch(`${process.env.API_URL}/api/user_sentiment_analysis`, {
          headers: {
            "x-api-key": process.env.INTERNAL_API_KEY || "",
          },
        }),
        fetch(`${process.env.API_URL}/api/sentiment_stats`, {
          headers: {
            "x-api-key": process.env.INTERNAL_API_KEY || "",
          },
        }),
      ]);

    const [daily, hourly, users, stats] = await Promise.all([
      dailyResponse.json(),
      hourlyResponse.json(),
      userResponse.json(),
      statsResponse.json(),
    ]);

    return NextResponse.json({
      daily,
      hourly,
      users,
      stats,
    });
  } catch (error) {
    console.error("Error fetching sentiment data:", error);
    return NextResponse.json(
      { error: "Failed to fetch sentiment data" },
      { status: 500 }
    );
  }
}
