import { NextResponse } from "next/server";

// app/api/chat/route.ts
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const response = await fetch(`${process.env.API_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.INTERNAL_API_KEY || "",
      },
      body: JSON.stringify(body),
    });

    // Handle streaming response
    const reader = response.body?.getReader();
    const encoder = new TextEncoder();

    return new Response(
      new ReadableStream({
        async start(controller) {
          try {
            while (true) {
              const { done, value } = await reader!.read();
              if (done) break;
              controller.enqueue(encoder.encode(`data: ${value}\n\n`));
            }
          } catch (error) {
            controller.error(error);
          } finally {
            controller.close();
          }
        },
      }),
      {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      }
    );
  } catch (error) {
    console.error("Error in chat:", error);
    return NextResponse.json({ error: "Chat error occurred" }, { status: 500 });
  }
}
