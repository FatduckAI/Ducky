// anthropicService.ts
import Anthropic from "@anthropic-ai/sdk";

interface AnthropicConfig {
  apiKey: string;
  model: string;
  maxTokens: number;
}

const defaultConfig: AnthropicConfig = {
  apiKey: process.env.ANTHROPIC_API_KEY || "",
  model: "claude-3-5-sonnet-20241022",
  maxTokens: 1024,
};

let anthropicInstance: Anthropic | null = null;

export const getAnthropicClient = (): Anthropic => {
  if (!anthropicInstance) {
    anthropicInstance = new Anthropic({
      apiKey: defaultConfig.apiKey,
    });
  }
  return anthropicInstance;
};

export const generateClaudeResponse = async (
  systemPrompt: string,
  userPrompt: string
): Promise<string> => {
  const client = getAnthropicClient();

  const response = await client.messages.create({
    model: defaultConfig.model,
    max_tokens: defaultConfig.maxTokens,
    system: [{ type: "text", text: systemPrompt }],
    messages: [
      {
        role: "user",
        content: userPrompt,
      },
    ],
  });

  const textContent = response.content.find((block) => block.type === "text");
  return textContent && "text" in textContent ? textContent.text : "";
};
