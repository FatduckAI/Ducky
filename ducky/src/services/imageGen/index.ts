// imageService.ts
import { ducky } from "@/src/ducky/character";
import dotenv from "dotenv";
import { OpenAI } from "openai";

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.TOGETHER_API_KEY,
  baseURL: "https://api.together.xyz/v1",
});

// Interfaces
export interface ModerationResult {
  isAppropriate: boolean;
  reason?: string;
}

export interface ImageGenerationResult {
  success: boolean;
  url?: string;
  error?: string;
}

export class ImageService {
  /**
   * Moderates content for inappropriate material
   */
  static async moderateContent(text: string): Promise<ModerationResult> {
    try {
      const completion = await openai.chat.completions.create({
        model: "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages: [
          {
            role: "system",
            content:
              'You are a content moderator. Analyze the following text for inappropriate content including: explicit material, violence, hate speech, or other unsafe content. Respond with a JSON object containing \'isAppropriate\' (boolean) and \'reason\' (string if inappropriate). Example response: {"isAppropriate": true} or {"isAppropriate": false, "reason": "Contains violent content"}',
          },
          {
            role: "user",
            content: text,
          },
        ],
        response_format: { type: "json_object" },
      });

      const content = completion.choices[0]?.message?.content;

      if (!content) {
        throw new Error("No content received from moderation API");
      }
      try {
        const result = JSON.parse(content);

        // Validate the response structure
        if (typeof result.isAppropriate !== "boolean") {
          throw new Error(
            "Invalid response format: missing isAppropriate boolean"
          );
        }

        return {
          isAppropriate: result.isAppropriate,
          reason: result.reason,
        };
      } catch (parseError: unknown) {
        console.error("Failed to parse moderation response:", content);
        const errorMessage =
          parseError instanceof Error
            ? parseError.message
            : "Unknown parsing error";
        throw new Error(`JSON parsing error: ${errorMessage}`);
      }
    } catch (error: unknown) {
      console.error("Error in content moderation:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      return {
        isAppropriate: false,
        reason: `Moderation check failed: ${errorMessage}`,
      };
    }
  }

  /**
   * Generates an image based on the provided text
   */
  static async generateImage(text: string): Promise<ImageGenerationResult> {
    try {
      // First moderate the content
      const moderationResult = await this.moderateContent(text);

      if (!moderationResult.isAppropriate) {
        return {
          success: false,
          error: `Content moderation failed: ${moderationResult.reason}`,
        };
      }

      // Construct a safe prompt
      const safePrompt =
        `${ducky.imageGen.description} and ${text}. In a ${ducky.imageGen.style}`.trim();

      const response = await openai.images.generate({
        prompt: safePrompt,
        model: "black-forest-labs/FLUX.1.1-pro",
        n: 1,
      });

      const imageUrl = response.data[0]?.url;

      if (!imageUrl) {
        throw new Error("No image URL received from API");
      }

      return {
        success: true,
        url: imageUrl,
      };
    } catch (error: unknown) {
      console.error("Error generating image:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      return {
        success: false,
        error: `Image generation failed: ${errorMessage}`,
      };
    }
  }
}
