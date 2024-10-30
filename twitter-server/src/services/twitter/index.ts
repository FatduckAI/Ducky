let twitterServiceInstance: TwitterService | null = null;

export async function getTwitterService(): Promise<TwitterService> {
  if (!twitterServiceInstance) {
    twitterServiceInstance = new TwitterService();
    await twitterServiceInstance.initialize();
  }
  return twitterServiceInstance;
}

export { SearchMode, TwitterService };
export type { TweetResponse, TwitterReply };
