import type { AIProvider } from "../agent/types";
import { anthropicProvider } from "./anthropic";
import { togetherProvider } from "./together";

export type ProviderType = "claude" | "together";

export const createProvider = (type: ProviderType): AIProvider => {
  switch (type) {
    case "claude":
      return anthropicProvider;
    case "together":
      return togetherProvider;
    default:
      throw new Error(`Unknown provider type: ${type}`);
  }
};
