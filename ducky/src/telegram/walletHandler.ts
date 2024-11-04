import { eq } from "drizzle-orm";
import { DrizzleError } from "drizzle-orm/errors";
import { Context, Telegraf } from "telegraf";
import type { Message } from "telegraf/types";
import { users } from "../../db/schema";

export class WalletHandlers {
  private bot: Telegraf;
  private db: any;

  constructor(bot: Telegraf, db: any) {
    this.bot = bot;
    this.db = db;
  }

  public async registerWallet(ctx: Context): Promise<void> {
    try {
      // Check if this is a private chat
      if (ctx.chat?.type !== "private") {
        await ctx.reply(
          "🔒 For security reasons, please register your wallet address in private chat.\n" +
            "Click the button below to start a private chat.",
          {
            reply_markup: {
              inline_keyboard: [
                [
                  {
                    text: "Register Privately",
                    url: `https://t.me/${ctx.botInfo.username}?start=register`,
                  },
                ],
              ],
            },
          }
        );
        return;
      }

      const user = ctx.from;
      if (!user) {
        throw new Error("User information not available");
      }

      const telegramId = user.id.toString();
      const telegramUsername = user.username;

      // Get the Solana address from command arguments
      const args = (ctx.message as Message.TextMessage).text
        .split(" ")
        .slice(1);
      if (args.length === 0) {
        await ctx.reply(
          "❌ Please provide your Solana wallet address.\n\n" +
            "Usage: /register <solana_address>\n" +
            "Example: /register 7PoGwU6HuWuqpqR1YtRoXKphvhXw8MKaWMWkVgEhgP7n"
        );
        return;
      }

      const solanaAddress = args[0];
      if (solanaAddress.length < 32 || solanaAddress.length > 44) {
        await ctx.reply(
          "❌ Invalid Solana address format. Please check your address and try again."
        );
        return;
      }

      try {
        // Check if user exists
        const [existingUser] = await this.db
          .select()
          .from(users)
          .where(eq(users.telegramId, telegramId))
          .limit(1);

        if (!existingUser) {
          await this.db.insert(users).values({
            telegramId,
            telegramUsername,
            solanaAddress,
            updatedAt: new Date(),
          });

          console.log(`Created new user account for ${telegramId}`);
        } else {
          await this.db
            .update(users)
            .set({
              solanaAddress,
              telegramUsername,
              updatedAt: new Date(),
            })
            .where(eq(users.telegramId, telegramId));
        }

        const successMessage =
          `✅ Registration successful!\n\n` +
          `Telegram: @${telegramUsername}\n` +
          `Solana Address: ${solanaAddress}\n\n` +
          `Your wallet has been securely registered.`;

        await ctx.reply(successMessage);

        console.log(
          `User ${telegramId} registered with Solana address ${solanaAddress}`
        );
      } catch (error) {
        if (error instanceof DrizzleError) {
          console.log("Database error while registering user:", error);
          await ctx.reply(
            "❌ Sorry, there was an error saving your information. Please try again later."
          );
          return;
        }
        throw error;
      }
    } catch (error) {
      console.log("Error in registerWallet:", error);
      await ctx.reply(
        "❌ An error occurred while processing your registration. Please try again later."
      );
    }
  }

  public async getMyInfo(ctx: Context): Promise<void> {
    try {
      const user = ctx.from;
      if (!user) {
        throw new Error("User information not available");
      }

      const telegramId = user.id.toString();
      const telegramUsername = user.username;

      try {
        // Get or create user
        const [userInfo] = await this.db
          .select()
          .from(users)
          .where(eq(users.telegramId, telegramId))
          .limit(1);

        if (!userInfo) {
          const [newUser] = await this.db
            .insert(users)
            .values({
              telegramId,
              telegramUsername,
              updatedAt: new Date(),
            })
            .returning();

          let groupResponse =
            "✅ Information has been sent to you in a private message!\n📝 You haven't registered any addresses yet.";
          await ctx.reply(groupResponse);
          return;
        }

        // Send full details in DM
        try {
          let dmResponse = "🔍 Your registered information:\n\n";
          if (userInfo.telegramUsername) {
            dmResponse += `Telegram: @${userInfo.telegramUsername}\n`;
          }
          if (userInfo.solanaAddress) {
            dmResponse += `Solana: ${userInfo.solanaAddress}\n`;
          }
          if (userInfo.ethAddress) {
            dmResponse += `Ethereum: ${userInfo.ethAddress}\n`;
          }
          if (userInfo.twitterUsername) {
            dmResponse += `Twitter: @${userInfo.twitterUsername}\n`;
          }
          if (userInfo.twitterName) {
            dmResponse += `Twitter Name: ${userInfo.twitterName}\n`;
          }

          if (
            !userInfo.solanaAddress &&
            !userInfo.ethAddress &&
            !userInfo.twitterUsername
          ) {
            dmResponse +=
              "\n📝 You haven't registered any addresses yet.\nUse /register <solana_address> to register your Solana address.";
          }

          await this.bot.telegram.sendMessage(user.id, dmResponse);

          // Send limited info response in group
          let groupResponse =
            "✅ Information has been sent to you in a private message!";
          if (
            !userInfo.solanaAddress &&
            !userInfo.ethAddress &&
            !userInfo.twitterUsername
          ) {
            groupResponse += "\n📝 You haven't registered any addresses yet.";
          }

          await ctx.reply(groupResponse);
        } catch (dmError) {
          console.log("Failed to send DM:", dmError);
          await ctx.reply(
            "❌ Failed to send private message. Please start a chat with the bot first."
          );
        }
      } catch (error) {
        if (error instanceof DrizzleError) {
          console.log("Database error while fetching user info:", error);
          await ctx.reply(
            "❌ Sorry, there was an error retrieving your information. Please try again later."
          );
          return;
        }
        throw error;
      }
    } catch (error) {
      console.log("Error in getMyInfo:", error);
      await ctx.reply(
        "❌ An error occurred while fetching your information. Please try again later."
      );
    }
  }
}
