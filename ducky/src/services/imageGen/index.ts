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
              "You are a content moderator. Analyze the following text for inappropriate content including: explicit material, violence, hate speech, or other unsafe content. Respond with a JSON object containing 'isAppropriate' (boolean) and 'reason' (string if inappropriate).",
          },
          {
            role: "user",
            content: text,
          },
        ],
        response_format: { type: "json_object" },
      });

      const result = JSON.parse(completion.choices[0].message.content ?? "");
      return {
        isAppropriate: result.isAppropriate,
        reason: result.reason,
      };
    } catch (error) {
      console.error("Error in content moderation:", error);
      return {
        isAppropriate: false,
        reason: "Error during content moderation",
      };
    }
  }

  /**
   * Generates an image based on the provided text
   */
  static async generateImage(text: string): Promise<ImageGenerationResult> {
    try {
      const response = await openai.images.generate({
        prompt: `${ducky.imageGen.description} and ${text}. In a ${ducky.imageGen.style}.`,
        model: "black-forest-labs/FLUX.1.1-pro",
        n: 1,
      });

      if (response.data[0]?.url) {
        return {
          success: true,
          url: response.data[0].url,
        };
      } else {
        return {
          success: false,
          error: "No image URL received",
        };
      }
    } catch (error) {
      console.error("Error generating image:", error);
      return {
        success: false,
        error: "Failed to generate image",
      };
    }
  }
}
