import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error("DATABASE_URL environment variable is not set");
}

// Create the connection
const client = postgres(connectionString);
export const db = drizzle(client, { schema });

// Export a function to test the connection
export async function testConnection() {
  try {
    // Try a simple query
    const result = await db.select().from(schema.duckyAi).limit(1);
    console.log("Database connection successful");
    return true;
  } catch (error) {
    console.error("Database connection failed:", error);
    return false;
  }
}
