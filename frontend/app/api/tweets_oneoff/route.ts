import { NextResponse } from "next/server";

// app/api/tweets_oneoff/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/api/tweets_oneoff`, {
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching one-off tweets:", error);
    return NextResponse.json(
      { error: "Failed to fetch one-off tweets" },
      { status: 500 }
    );
  }
}
