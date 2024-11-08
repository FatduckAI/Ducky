// telegramImageHandler.ts
import { Context } from "telegraf";
import { ImageService } from "../services/imageGen";

export class ImageHandler {
  /**
   * Handles the /img command for the Telegram bot
   */
  async handleImageGeneration(ctx: Context) {
    try {
      if (!ctx.message || !("text" in ctx.message)) {
        await ctx.reply("Please send a text message.");
        return;
      }

      const text = ctx.message.text.replace(/^\/img\s*/, "").trim();
      console.log("text", text);
      if (!text) {
        await ctx.reply("Please provide a description after the /img command.");
        return;
      }

      // Moderate content
      const moderationResult = await ImageService.moderateContent(text);

      if (!moderationResult.isAppropriate) {
        await ctx.reply(
          `Sorry, I cannot generate this image. Reason: ${moderationResult.reason}`
        );
        return;
      }

      await ctx.reply("🎨 Generating...");

      // Generate image
      const imageResult = await ImageService.generateImage(text);

      if (imageResult.success && imageResult.url) {
        await ctx.replyWithPhoto(imageResult.url);
      } else {
        throw new Error(imageResult.error || "Unknown error");
      }
    } catch (error) {
      console.error("Error in handleImageGeneration:", error);
      await ctx.reply(
        "Sorry, there was an error generating your image. Please try again later."
      );
    }
  }
}
