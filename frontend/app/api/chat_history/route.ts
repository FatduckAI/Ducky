import { NextResponse } from "next/server";

// app/api/chat_history/route.ts
export async function GET() {
  try {
    console.log("Fetching chat history", process.env.API_URL);
    const response = await fetch(`${process.env.API_URL}/chat_history`, {
      method: "GET",
      headers: {
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching chat history:", error);
    return NextResponse.json(
      { error: "Failed to fetch chat history" },
      { status: 500 }
    );
  }
}
