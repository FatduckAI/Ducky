import { NextResponse } from "next/server";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const days = searchParams.get("days") || "30";

    const response = await fetch(
      `${process.env.API_URL}/api/sentiment_stats?days=${days}`,
      {
        headers: {
          "x-api-key": process.env.INTERNAL_API_KEY || "",
        },
      }
    );
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching sentiment stats:", error);
    return NextResponse.json(
      { error: "Failed to fetch sentiment statistics" },
      { status: 500 }
    );
  }
}
