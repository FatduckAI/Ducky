import { Telegraf } from "telegraf";
import { db } from "../../db";
import { WalletHandlers } from "./walletHandler";

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN!);
const walletHandlers = new WalletHandlers(bot, db);

bot.command("register", (ctx) => walletHandlers.registerWallet(ctx));
bot.command("myinfo", (ctx) => walletHandlers.getMyInfo(ctx));

bot.launch();
