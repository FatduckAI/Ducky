import { NextResponse } from "next/server";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const minMessages = searchParams.get("min_messages") || "10";

    const response = await fetch(
      `${process.env.API_URL}/user_sentiment_analysis?min_messages=${minMessages}`,
      {
        headers: {
          "x-api-key": process.env.INTERNAL_API_KEY || "",
        },
      }
    );
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching user sentiment analysis:", error);
    return NextResponse.json(
      { error: "Failed to fetch user sentiment analysis" },
      { status: 500 }
    );
  }
}
