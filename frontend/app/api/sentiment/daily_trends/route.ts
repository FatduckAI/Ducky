import { NextResponse } from "next/server";

export async function GET(request: Request) {
  console.log("Fetching daily trends", process.env.API_URL);
  try {
    const { searchParams } = new URL(request.url);
    const days = searchParams.get("days") || "30";

    const response = await fetch(
      `${process.env.API_URL}/daily_trends?days=${days}`,
      {
        headers: {
          "x-api-key": process.env.INTERNAL_API_KEY || "",
        },
      }
    );
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching daily trends:", error);
    return NextResponse.json(
      { error: "Failed to fetch daily sentiment trends" },
      { status: 500 }
    );
  }
}
