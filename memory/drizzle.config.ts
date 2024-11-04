import type { Config } from "drizzle-kit";

export default {
  schema: "./schema",
  dialect: "postgresql",
  out: "./migrations",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
} satisfies Config;
