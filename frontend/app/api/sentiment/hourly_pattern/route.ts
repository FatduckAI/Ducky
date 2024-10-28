// app/api/sentiment/hourly_pattern/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/hourly_pattern`, {
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching hourly pattern:", error);
    return NextResponse.json(
      { error: "Failed to fetch hourly sentiment pattern" },
      { status: 500 }
    );
  }
}
