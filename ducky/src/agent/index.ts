import {
  getDuckyAiForTweetGenerationCleo,
  getDuckyAiForTweetGenerationTweets,
} from "@/db/utils";
import { ConsoleDeliveryService } from "../delivery/console";
import { TwitterDeliveryService } from "../delivery/twitter";
import { ServiceInitializer } from "../delivery/twitter.init";
import { ducky, generatePrompt } from "../ducky/character";
import { anthropicProvider } from "../providers/anthropic";
import { fetchBTCPriceData } from "../services/coingecko/price";
import { createGitHubService } from "../services/github";
import { Agent } from "./Agent";
import type { AgentTask } from "./types";

async function main() {
  const isTestMode = process.argv.includes("--test");

  const agent = new Agent({ name: "ducky-bot", isTestMode });
  // Initialize Twitter services
  const scraper = await ServiceInitializer.initialize();
  const twitterDelivery = TwitterDeliveryService.getInstance(
    scraper,
    process.env.TELEGRAM_BOT_TOKEN!,
    process.env.TARGET_CHANNEL_ID!
  );
  // Initialize GitHub service with the agent
  const githubService = createGitHubService(process.env.GITHUB_TOKEN!);

  // Hot Takes
  const hotTakeTask: AgentTask = {
    name: "hot-take",
    description: "Generate and post hot take",
    ai: true,
    cronPattern: "10 * * * *", // At 10 minutes past the hour
    provider: anthropicProvider,
    delivery: twitterDelivery,
    prompt: async () => {
      const tweets = await getDuckyAiForTweetGenerationTweets();
      return await generatePrompt.forTweet(tweets.map((t) => t.content));
    },
    systemPrompt: ducky.prompts.tweet.user,
    production: true,
  };

  // More distinct tweets
  const distinctTweetTask: AgentTask = {
    name: "distinct-tweet",
    description: "Generate and post distinct tweet",
    ai: true,
    cronPattern: "50 * * * *", // At 50 minutes past the hour
    provider: anthropicProvider,
    delivery: twitterDelivery,
    prompt: async () => {
      const tweets = await getDuckyAiForTweetGenerationCleo();
      return await generatePrompt.forTweet(tweets.map((t) => t.content));
    },
    systemPrompt: ducky.prompts.tweet.user,
    production: true,
  };

  // Create base PR Analysis Task
  const prAnalysisTask: AgentTask = {
    name: "pr-analysis",
    description: "Analyze merged pull requests",
    ai: true,
    cronPattern: "*/10 * * * *", // Every 10 minutes
    provider: anthropicProvider,
    delivery: twitterDelivery,
    prompt: async () => {
      // Only get the prompt here, don't set the callback
      const { prompt } = await githubService.getNextPRAnalysis();
      return prompt;
    },
    // Set the callback here at the task level
    onComplete: async (content: string, tweetId: string) => {
      await githubService.savePRAnalysis(content, tweetId);
    },
    systemPrompt: ducky.prompts.prAnalysis.system,
    production: true,
  };

  const priceTrackerTask: AgentTask = {
    ai: false,
    name: "btc-price-tracker",
    description: "Track BTC price changes daily",
    cronPattern: "0 0 * * *", // Run at midnight every day
    provider: anthropicProvider,
    production: true,
    systemPrompt: "",
    delivery: new ConsoleDeliveryService(),
    prompt: async () => {
      const priceData = await fetchBTCPriceData();
      return `Current BTC price: $${priceData.currentPrice.toFixed(2)}`;
    },
  };

  // Add tasks to agent
  await agent.addTask(hotTakeTask);
  await agent.addTask(distinctTweetTask);
  await agent.addTask(prAnalysisTask);
  await agent.addTask(priceTrackerTask);
  if (!isTestMode) {
    // Handle shutdown of webhook server
    process.on("SIGINT", () => {
      agent.stopAll();
      process.exit(0);
    });
  }

  agent.startAll();
  agent.startServer(3000);
}

main().catch(console.error);
