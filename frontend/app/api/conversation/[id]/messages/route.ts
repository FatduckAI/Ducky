import { MessageHandlerSDK, createSdkConfig } from "@/lib/sdk";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const QuerySchema = z.object({
  limit: z.coerce.number().min(1).max(100).default(50),
  offset: z.coerce.number().optional(),
});

const env = z
  .object({
    RUST_SERVER_URL: z.string().url(),
  })
  .parse({
    RUST_SERVER_URL: process.env.RUST_SERVER_URL,
  });

// Initialize SDK
const sdk = new MessageHandlerSDK(createSdkConfig(env.RUST_SERVER_URL));

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const conversationId = z.string().uuid().parse(params.id);
    const { searchParams } = request.nextUrl;
    const query = QuerySchema.parse({
      limit: searchParams.get("limit"),
      offset: searchParams.get("offset"),
    });
    console.log(query);
    const messages = await sdk.getConversationMessages({
      conversationId,
      limit: query.limit,
      offset: query.offset,
    });
    console.log(messages);
    return NextResponse.json(messages);
  } catch (error) {
    console.error("Error fetching conversation messages:", error);
    return handleApiError(error);
  }
}

function handleApiError(error: unknown) {
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      { error: "Invalid request format", details: error.errors },
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
}
