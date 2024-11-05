import { Context } from "telegraf";
import type { Message } from "telegraf/types";
import { db } from "../../db";
import { telegramMessages } from "../../db/schema";
import { analyzeSentiment } from "../lib/anthropic";

interface MessageHandler {
  saveMessage(ctx: Context): Promise<void>;
}

export class EngagementMessageHandler implements MessageHandler {
  private readonly IGNORE_SENDER_IDS = new Set([
    5976408419, 609517172, 7804337971, 6868734170,
  ]);
  private db: any;

  constructor(db: any) {
    this.db = db;
  }

  async saveMessage(ctx: Context): Promise<void> {
    try {
      if (!ctx.message) return;

      const message = ctx.message as Message;
      const senderId = message.from?.id;

      // Skip if sender is in ignore list
      if (senderId && this.IGNORE_SENDER_IDS.has(senderId)) {
        return;
      }

      if (message.chat.id !== -1002319354943) {
        return;
      }

      // Get message content
      const content =
        "text" in message
          ? message.text
          : "caption" in message
          ? message.caption
          : "";

      const sentimentScores = await analyzeSentiment(content || "");

      // Prepare insert data
      const messageData = {
        messageId: message.message_id.toString(),
        chatId: message.chat.id.toString(),
        senderId: senderId?.toString() || null,
        senderUsername: message.from?.username || null,
        content: content,
        replyToMessageId:
          "reply_to_message" in message
            ? message.reply_to_message?.message_id?.toString()
            : null,
        mediaType: null,
        mediaFileId: null,
        timestamp: new Date(message.date * 1000),
        isPinned: "pinned_message" in message,
        // Add sentiment scores if implemented
        sentimentPositive: sentimentScores[0],
        sentimentNegative: sentimentScores[1],
        sentimentHelpful: sentimentScores[2],
        sentimentSarcastic: sentimentScores[3],
      };

      // Insert or update message
      await db
        .insert(telegramMessages)
        .values(messageData)
        .onConflictDoUpdate({
          target: telegramMessages.messageId,
          set: {
            content: messageData.content,
            mediaType: messageData.mediaType,
            mediaFileId: messageData.mediaFileId,
          },
        });
    } catch (error) {
      console.error("Error saving message:", error);
    }
  }
}
