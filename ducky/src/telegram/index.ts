import { Telegraf } from "telegraf";
import { db } from "../../db";
import { EngagementMessageHandler } from "./engagementMessageHandler";
import { ImageHandler } from "./imageHandler";
import { WalletHandlers } from "./walletHandler";

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN!);
const walletHandlers = new WalletHandlers(bot, db);
const messageHandler = new EngagementMessageHandler(db);
const imageHandler = new ImageHandler();

// Add this to your bot setup
bot.command("register", (ctx) => walletHandlers.registerWallet(ctx));
bot.command("myinfo", (ctx) => walletHandlers.getMyInfo(ctx));
bot.command("img", (ctx) => imageHandler.handleImageGeneration(ctx));
bot.on("message", (ctx) => messageHandler.saveMessage(ctx));

bot.launch();
