// influencerBot.ts
import { config } from "dotenv";
import { saveMessageToDb } from "../../db/utils";
import type { AnalysisResponse } from "../../types";
import { ducky, generatePrompt } from "../ducky/character";
import { generateClaudeResponse } from "../lib/anthropic";
import { getTwitterService } from "./";

if (!process.env.RAILWAY_ENVIRONMENT) {
  config();
}

interface InfluencerTweet {
  author: string;
  text: string;
  engagement: number;
  tweetId: string;
  followers?: number;
}

// List of crypto/web3 influencers to monitor
const INFLUENCERS = [
  "VitalikButerin",
  "cz_binance",
  "ethereumJoseph",
  "cdixon",
  "naval",
  "punk6529",
  "cobie",
  "CryptoKaleo",
  "RaoulGMI",
  "sassal0x",
];

export const getRecentInfluencerTweets = async (): Promise<
  InfluencerTweet[]
> => {
  const twitterService = await getTwitterService();
  const tweets: InfluencerTweet[] = [];

  for (const influencer of INFLUENCERS) {
    try {
      // Get influencer's profile first to check followers
      const profile = await twitterService.getProfile(influencer);
      if (!profile) continue;

      // Get their most recent tweet
      const recentTweets = await twitterService.searchTweets(influencer, 1);
      if (recentTweets.length > 0) {
        const tweet = recentTweets[0];
        tweets.push({
          author: influencer,
          text: tweet.text,
          engagement: tweet.likes + tweet.retweets,
          tweetId: tweet.id,
          followers: profile.followersCount,
        });

        // Log for monitoring
        await saveMessageToDb(
          `Found tweet from ${influencer} with ${tweet.likes} likes and ${tweet.retweets} retweets`,
          "System",
          0
        );
      }
    } catch (error) {
      console.error(`Error fetching tweets for ${influencer}:`, error);
      await saveMessageToDb(
        `Error fetching tweets for ${influencer}: ${error}`,
        "System",
        0
      );
    }

    // Add delay between requests to avoid rate limits
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  return tweets;
};

export const analyzeTweets = async (
  tweets: InfluencerTweet[]
): Promise<AnalysisResponse> => {
  // Sort tweets by engagement and followers for better analysis
  const sortedTweets = tweets.sort((a, b) => {
    const scoreA = a.engagement * 0.7 + (a.followers || 0) * 0.3;
    const scoreB = b.engagement * 0.7 + (b.followers || 0) * 0.3;
    return scoreB - scoreA;
  });

  const analysisPrompt = generatePrompt.forTweetAnalysis(sortedTweets);
  const analysisResponse = await generateClaudeResponse(
    analysisPrompt,
    ducky.prompts.tweetAnalysis.user
  );

  return JSON.parse(analysisResponse);
};

export const generateResponse = async (
  tweet: InfluencerTweet
): Promise<string> => {
  const responsePrompt = generatePrompt.forInfluencerResponse({
    author: tweet.author,
    text: tweet.text,
  });

  return await generateClaudeResponse(
    responsePrompt,
    ducky.prompts.influencerResponse.user
  );
};

export const influencerResponseJob = async (): Promise<void> => {
  try {
    console.log("Starting influencer response job");
    await saveMessageToDb("Starting influencer response job", "System", 0);

    // Get recent tweets from influencers
    const tweets = await getRecentInfluencerTweets();
    if (tweets.length === 0) {
      throw new Error("No suitable tweets found");
    }

    // Log found tweets
    await saveMessageToDb(
      `Found ${tweets.length} tweets from influencers to analyze`,
      "System",
      0
    );

    // Analyze and select the best tweet to respond to
    const analysis = await analyzeTweets(tweets);
    await saveMessageToDb(
      `Selected tweet from ${analysis.selectedTweet.author}: ${analysis.selectedTweet.text}`,
      "System",
      0
    );
    await saveMessageToDb(`Reasoning: ${analysis.reasoning}`, "System", 0);

    // Generate and post response
    const selectedTweet = tweets.find(
      (t) =>
        t.author === analysis.selectedTweet.author &&
        t.text === analysis.selectedTweet.text
    );

    if (selectedTweet) {
      const response = await generateResponse(selectedTweet);
      const twitterService = await getTwitterService();
      const result = await twitterService.sendReply(
        response,
        selectedTweet.tweetId
      );

      if (result.success) {
        await saveMessageToDb(
          `Successfully replied to ${selectedTweet.author} with: ${response}`,
          "System",
          0
        );
      } else {
        throw new Error(result.error || "Failed to post reply");
      }
    }
  } catch (error) {
    console.error("Error in influencer response job:", error);
    await saveMessageToDb(
      `Error in influencer response job: ${error}`,
      "System",
      0
    );
    throw error;
  }
};

influencerResponseJob()
  .then(() => console.log("Completed influencer response job"))
  .catch(console.error);
