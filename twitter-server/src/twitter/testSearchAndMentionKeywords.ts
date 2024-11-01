import { ducky, generatePrompt } from "../ducky/character";
import { generateClaudeResponse } from "../lib/anthropic";
import { getTwitterService } from "./";

async function testSearchAndMentionKeywords() {
  const twitter = await getTwitterService();
  const searchResults = await twitter.searchMentionsAndKeywords();

  /*   searchResults.tweets.map((tweet) => {
    console.log(`${tweet.author}: ${tweet.text}`);
  }); */

  searchResults.tweets.map(async (tweet) => {
    const prompt = generatePrompt.forMention(tweet.text);
    const response = await generateClaudeResponse(
      prompt,
      ducky.prompts.mention.user
    );
    console.log(`${tweet.author}: ${tweet.text}\nResponse: ${response}`);
  });
}

testSearchAndMentionKeywords();
