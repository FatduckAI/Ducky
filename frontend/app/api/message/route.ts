// app/api/message/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

// Message validation schema
const MessageSchema = z.object({
  user_id: z.string().min(1),
  id: z.string().min(1),
  conversation_id: z.string().uuid(),
  platform: z.enum(["twitter", "discord", "telegram"]),
  content: z.string().min(1),
  priority: z.enum(["Low", "Normal", "High", "Critical"]).default("Normal"),
  metadata: z.record(z.string()).optional(),
  thread_id: z.string().optional(),
  timestamp: z.number(),
  retry_count: z.number().default(0),
});

export type Message = z.infer<typeof MessageSchema>;

const env = z
  .object({
    RUST_SERVER_URL: z.string().url(),
  })
  .parse({
    RUST_SERVER_URL: process.env.RUST_SERVER_URL,
  });

const handleError = (error: unknown) => {
  console.error("Error processing message:", error);

  if (error instanceof z.ZodError) {
    return NextResponse.json(
      { error: "Invalid message format", details: error.errors },
      { status: 400 }
    );
  }

  if (error instanceof Error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(
    { error: "An unknown error occurred" },
    { status: 500 }
  );
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const message = MessageSchema.parse({
      ...body,
      timestamp: Date.now(),
    });

    const response = await fetch(`${env.RUST_SERVER_URL}/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(message),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to process message");
    }

    const data = await response.json();
    return NextResponse.json({ success: true, message: data }, { status: 200 });
  } catch (error) {
    return handleError(error);
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}
