import { NextResponse } from "next/server";

// app/api/tweets/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/api/tweets`, {
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching tweets:", error);
    return NextResponse.json(
      { error: "Failed to fetch tweets" },
      { status: 500 }
    );
  }
}
