import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import { Telegraf } from "telegraf";
import { WalletHandlers } from "./walletHandler";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const db = drizzle(pool);

const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN!);
const walletHandlers = new WalletHandlers(bot, db);

bot.command("register", (ctx) => walletHandlers.registerWallet(ctx));
bot.command("myinfo", (ctx) => walletHandlers.getMyInfo(ctx));

bot.launch();
