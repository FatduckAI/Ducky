import { NextResponse } from "next/server";

// app/api/ducky_ai_tweets/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/ducky_ai_tweets`, {
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching Ducky AI tweets:", error);
    return NextResponse.json(
      { error: "Failed to fetch Ducky AI tweets" },
      { status: 500 }
    );
  }
}
