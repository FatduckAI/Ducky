import { NextResponse } from "next/server";
import { z } from "zod";

const QuerySchema = z.object({
  page: z.string().transform(Number).default("1"),
  limit: z.string().transform(Number).default("10"),
});

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const { page, limit } = QuerySchema.parse(Object.fromEntries(searchParams));

    const response = await fetch(
      `${process.env.API_URL}/conversations?page=${page}&limit=${limit}`,
      {
        headers: {
          "x-api-key": process.env.INTERNAL_API_KEY || "",
        },
      }
    );
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching conversations:", error);
    return NextResponse.json(
      { error: "Failed to fetch conversations" },
      { status: 500 }
    );
  }
}
