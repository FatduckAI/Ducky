import { Turnkey } from "@turnkey/sdk-server";
import * as dotenv from "dotenv";

dotenv.config();

// Validate environment variables
export function validateEnvironment() {
  const required = [
    "API_PUBLIC_KEY",
    "API_PRIVATE_KEY",
    "BASE_URL",
    "ORGANIZATION_ID",
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}`
    );
  }
}

export const turnkeyClient = new Turnkey({
  apiBaseUrl: process.env.BASE_URL!,
  apiPrivateKey: process.env.API_PRIVATE_KEY!,
  apiPublicKey: process.env.API_PUBLIC_KEY!,
  defaultOrganizationId: process.env.ORGANIZATION_ID!,
});
