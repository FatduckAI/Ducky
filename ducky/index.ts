import { Scraper } from "agent-twitter-client";
import { Agent } from "./src/agent/Agent";
import { TwitterDeliveryService } from "./src/delivery/TwitterDeliveryService";
import { anthropicProvider } from "./src/providers/AnthropicProvider";

// Initialize services
const scraper = new Scraper(/* your config */);
const twitterDelivery = TwitterDeliveryService.getInstance(scraper);

// Create an agent
const agent = new Agent({ name: "twitter-bot" });

// Create a tasks
const tweetTask = {
  name: "daily-tweet",
  cronPattern: "0 12 * * *", // Run at noon every day
  systemPrompt: "You are a friendly and engaging Twitter bot...",
  provider: anthropicProvider,
  delivery: twitterDelivery,
  prompt: async () => {
    return "Generate an engaging tweet about...";
  },
};

// Add and start the task
await agent.addTask(tweetTask);
agent.startAll();
