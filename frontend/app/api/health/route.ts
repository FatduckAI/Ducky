import { NextResponse } from "next/server";

// app/api/health/route.ts
export async function GET() {
  return NextResponse.json({ status: "ok" });
}
