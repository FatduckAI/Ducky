import {
  getDuckyAiForTweetGenerationCleo,
  getDuckyAiForTweetGenerationTweets,
} from "@/db/utils";
import { TwitterDeliveryService } from "../delivery/twitter";
import { ServiceInitializer } from "../delivery/twitter.init";
import { ducky, generatePrompt } from "../ducky/character";
import { anthropicProvider } from "../providers/anthropic";
import { Agent } from "./Agent";
import type { AgentTask } from "./types";

async function main() {
  const isTestMode = process.argv.includes("--test");
  // Initialize Twitter services
  const scraper = await ServiceInitializer.initialize();
  const twitterDelivery = TwitterDeliveryService.getInstance(scraper);

  const agent = new Agent({ name: "ducky-bot", isTestMode });

  // Hot Takes
  const hotTakeTask: AgentTask = {
    name: "hot-take",
    description: "Generate and post hot take",
    cronPattern: "10 * * * *", // At 10 minutes past the hour
    provider: anthropicProvider,
    delivery: twitterDelivery,
    prompt: async () => {
      const tweets = await getDuckyAiForTweetGenerationTweets();
      return generatePrompt.forTweet(tweets.map((t) => t.content));
    },
    systemPrompt: ducky.prompts.tweet.user,
  };

  // More distinct tweets
  const distinctTweetTask: AgentTask = {
    name: "distinct-tweet",
    description: "Generate and post distinct tweet",
    cronPattern: "50 * * * *", // At 50 minutes past the hour
    provider: anthropicProvider,
    delivery: twitterDelivery,
    prompt: async () => {
      const tweets = await getDuckyAiForTweetGenerationCleo();
      return generatePrompt.forTweet(tweets.map((t) => t.content));
    },
    systemPrompt: ducky.prompts.tweet.user,
  };

  // Add tasks to agent
  await agent.addTask(hotTakeTask);
  await agent.addTask(distinctTweetTask);
  agent.startAll();
  agent.startServer(3000);
}

main().catch(console.error);
