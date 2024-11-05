import { Telegraf } from "telegraf";
import { db } from "../../db";
import { EngagementMessageHandler } from "./engagementMessageHandler";
import { WalletHandlers } from "./walletHandler";

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN!);
const walletHandlers = new WalletHandlers(bot, db);
const messageHandler = new EngagementMessageHandler(db);

// Add this to your bot setup
bot.command("register", (ctx) => walletHandlers.registerWallet(ctx));
bot.command("myinfo", (ctx) => walletHandlers.getMyInfo(ctx));
bot.on("message", (ctx) => messageHandler.saveMessage(ctx));

bot.launch();
