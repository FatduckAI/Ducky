import { NextResponse } from "next/server";

// app/api/narrative/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.API_URL}/narrative`, {
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching narrative:", error);
    return NextResponse.json(
      { error: "Failed to fetch narrative" },
      { status: 500 }
    );
  }
}
