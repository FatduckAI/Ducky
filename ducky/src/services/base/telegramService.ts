// src/services/notification/TelegramService.ts
import axios from "axios";
import { BaseService } from "./BaseService";

export class TelegramService extends BaseService {
  private botToken: string;
  private channelId: string;

  constructor(botToken?: string, channelId?: string) {
    super();
    this.botToken = botToken || process.env.TELEGRAM_BOT_TOKEN || "";
    this.channelId = channelId || process.env.TARGET_CHANNEL_ID || "";

    if (!this.botToken || !this.channelId) {
      this.logDebug("Missing Telegram credentials");
    }
  }

  async sendNotification(
    content: string,
    url: string,
    replyUrl?: string
  ): Promise<void> {
    if (!this.botToken || !this.channelId) return;

    const message = replyUrl
      ? `🦆 Replying...\n\n'${content}'\n\n${url}\n\n`
      : `🦆 Tweeting...\n\n'${content}'\n\n${url}`;

    try {
      await axios.post(
        `https://api.telegram.org/bot${this.botToken}/sendMessage`,
        {
          chat_id: this.channelId,
          text: message,
          disable_web_page_preview: false,
        }
      );
    } catch (error) {
      this.logError("Error sending Telegram notification", error);
    }
  }
}
