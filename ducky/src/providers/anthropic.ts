import Anthropic from "@anthropic-ai/sdk";
import type { AIProvider } from "../agent/types";

interface SentimentAnalysis {
  sentiment_scores: {
    positive: number;
    negative: number;
    helpful: number;
    sarcastic: number;
  };
  confidence: number;
  analysis_timestamp: string;
}

export class AnthropicProvider implements AIProvider {
  type: "claude" = "claude";
  private client: Anthropic;
  private static instance: AnthropicProvider;

  config = {
    model: "claude-3-5-sonnet-20241022",
    temperature: 0.7,
    maxTokens: 1024,
  };

  private constructor() {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY not found in environment variables");
    }

    this.client = new Anthropic({
      apiKey,
    });
  }

  public static getInstance(): AnthropicProvider {
    if (!AnthropicProvider.instance) {
      AnthropicProvider.instance = new AnthropicProvider();
    }
    return AnthropicProvider.instance;
  }

  async generateResponse(
    systemPrompt: string,
    userPrompt: string
  ): Promise<string> {
    try {
      const response = await this.client.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        system: [{ type: "text", text: systemPrompt }],
        messages: [
          {
            role: "user",
            content: userPrompt,
          },
        ],
      });

      const textContent = response.content.find((block) =>
        this.isTextBlock(block)
      );
      return textContent && "text" in textContent ? textContent.text : "";
    } catch (error) {
      console.error("Error generating response:", error);
      throw error;
    }
  }

  async analyzeSentiment(text: string): Promise<number[]> {
    try {
      const jsonTemplate = {
        sentiment_scores: {
          positive: 0,
          negative: 0,
          helpful: 0,
          sarcastic: 0,
        },
        confidence: 0,
        analysis_timestamp: new Date().toISOString(),
      };

      const message = await this.client.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        messages: [
          {
            role: "user",
            content: `Analyze the sentiment of this text. Return ONLY a JSON object matching this EXACT structure, with no additional text or explanation:

${JSON.stringify(jsonTemplate, null, 2)}

Rules:
- All sentiment scores must be numbers between 0 and 1
- Confidence must be between 0 and 1
- Do not include any explanatory text
- Do not modify the JSON structure
- Use the current timestamp

Sentiment Rules:
- messages about check dms are not helpful, nor positive, they should have a low negative score
- messages that are obvious spam should have a low positive score and high negative score
- messages that are obviously sarcastic should have a high sarcastic score
- messages that are helpful should have a high helpful score

Text to analyze: "${text}"`,
          },
        ],
      });

      const responseContent = message.content[0];
      if (!this.isTextBlock(responseContent)) {
        throw new Error("Unexpected response type from Claude");
      }

      const analysis = JSON.parse(responseContent.text) as SentimentAnalysis;

      if (!this.validateSentimentAnalysis(analysis)) {
        throw new Error("Invalid sentiment analysis structure");
      }

      return [
        analysis.sentiment_scores.positive,
        analysis.sentiment_scores.negative,
        analysis.sentiment_scores.helpful,
        analysis.sentiment_scores.sarcastic,
      ];
    } catch (error) {
      console.error("Error analyzing sentiment:", error);
      console.error("Problematic text:", text);
      return [0.5, 0.5, 0.5, 0.5];
    }
  }

  private isTextBlock(content: any): content is { type: "text"; text: string } {
    return (
      typeof content === "object" &&
      content !== null &&
      content.type === "text" &&
      typeof content.text === "string"
    );
  }

  private validateSentimentAnalysis(data: any): data is SentimentAnalysis {
    try {
      return (
        typeof data === "object" &&
        data !== null &&
        typeof data.confidence === "number" &&
        data.confidence >= 0 &&
        data.confidence <= 1 &&
        typeof data.analysis_timestamp === "string" &&
        typeof data.sentiment_scores === "object" &&
        data.sentiment_scores !== null &&
        typeof data.sentiment_scores.positive === "number" &&
        data.sentiment_scores.positive >= 0 &&
        data.sentiment_scores.positive <= 1 &&
        typeof data.sentiment_scores.negative === "number" &&
        data.sentiment_scores.negative >= 0 &&
        data.sentiment_scores.negative <= 1 &&
        typeof data.sentiment_scores.helpful === "number" &&
        data.sentiment_scores.helpful >= 0 &&
        data.sentiment_scores.helpful <= 1 &&
        typeof data.sentiment_scores.sarcastic === "number" &&
        data.sentiment_scores.sarcastic >= 0 &&
        data.sentiment_scores.sarcastic <= 1
      );
    } catch {
      return false;
    }
  }
}

export const anthropicProvider = AnthropicProvider.getInstance();
