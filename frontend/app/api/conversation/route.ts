import { MessageHandlerSDK, createSdkConfig } from "@/lib/sdk";
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const QuerySchema = z.object({
  userId: z.string().min(1),
  includeInactive: z.coerce.boolean().default(false),
  page: z.coerce.number().min(0).default(0),
  pageSize: z.coerce.number().min(1).max(100).default(20),
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

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = request.nextUrl;
    const query = QuerySchema.parse({
      userId: searchParams.get("user_id"),
      includeInactive: searchParams.get("include_inactive"),
      page: searchParams.get("page"),
      pageSize: searchParams.get("page_size"),
    });

    const conversations = await sdk.listConversations({
      userId: query.userId,
      includeInactive: query.includeInactive,
      page: query.page,
      pageSize: query.pageSize,
    });

    return NextResponse.json(conversations);
  } catch (error) {
    console.error("Error processing conversation request:", error);
    return handleApiError(error);
  }
}

// Shared error handling
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
