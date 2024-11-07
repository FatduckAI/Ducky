import Together from "together-ai";
import type { AIProvider } from "../agent/types";

export class TogetherProvider implements AIProvider {
  type: "together" = "together";
  private client: Together;
  private static instance: TogetherProvider;

  config = {
    model: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    temperature: 0.7,
    maxTokens: 1024,
  };

  private constructor() {
    const apiKey = process.env.TOGETHER_API_KEY;
    if (!apiKey) {
      throw new Error("TOGETHER_API_KEY not found in environment variables");
    }

    this.client = new Together({
      apiKey,
    });
  }

  public static getInstance(): TogetherProvider {
    if (!TogetherProvider.instance) {
      TogetherProvider.instance = new TogetherProvider();
    }
    return TogetherProvider.instance;
  }

  async generateResponse(
    systemPrompt: string,
    userPrompt: string
  ): Promise<string> {
    try {
      const response = await this.client.chat.completions.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
        messages: [
          {
            role: "system",
            content: systemPrompt,
          },
          {
            role: "user",
            content: userPrompt,
          },
        ],
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error("No content in Together AI response");
      }

      return content;
    } catch (error) {
      console.error("Error generating response from Together AI:", error);
      throw error;
    }
  }
}

export const togetherProvider = TogetherProvider.getInstance();
