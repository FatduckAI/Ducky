import { PromptOutput, PromptTemplate } from "../agent/types";
import { ducky, DuckyCharacter, generatePrompt } from "./character";

export class DuckyPromptService implements PromptTemplate {
  private character: DuckyCharacter;

  constructor() {
    this.character = ducky;
  }

  generate(context?: {
    recentTweets?: string[];
    replyToTweet?: string;
  }): PromptOutput {
    if (context?.replyToTweet) {
      return this.generateReplyPrompt(context.replyToTweet);
    }
    return this.generateTweetPrompt(context?.recentTweets || []);
  }

  private generateTweetPrompt(recentTweets: string[]): PromptOutput {
    return {
      systemPrompt: this.character.prompts.tweet.system,
      userPrompt: generatePrompt.forTweet(recentTweets),
    };
  }

  private generateReplyPrompt(tweet: string): PromptOutput {
    return {
      systemPrompt: this.character.prompts.reply.system,
      userPrompt: generatePrompt.forReply(tweet),
    };
  }
}
