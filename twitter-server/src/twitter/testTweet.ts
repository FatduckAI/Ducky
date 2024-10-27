import { getTwitterService } from "./";

async function testTweet() {
  console.log("Starting test tweet");

  try {
    // Get Twitter service instance
    const twitter = await getTwitterService();

    // Generate test content with timestamp for uniqueness
    const timestamp = new Intl.DateTimeFormat("en-US", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date());

    const testContent = `Test tweet at ${timestamp}`;
    console.log("Attempting to send tweet: ", testContent);

    // Attempt to send tweet
    const result = await twitter.sendTweet(testContent);

    if (result.success) {
      console.log("Tweet sent successfully!");
      console.log("Tweet URL:", result.url);
    } else {
      console.error("Failed to send tweet:", result.error);
      process.exit(1);
    }

    // Optional: Test reply functionality
    if (result.success && result.url) {
      const tweetId = result.url.match(/\/status\/(\d+)/)?.[1];
      if (tweetId) {
        console.log("\nTesting reply functionality...");
        const replyContent = `This is a test reply at ${timestamp}`;

        const replyResult = await twitter.sendReply(replyContent, tweetId);

        if (replyResult.success) {
          console.log("Reply sent successfully!");
          console.log("Reply URL:", replyResult.url);
        } else {
          console.error("Failed to send reply:", replyResult.error);
        }
      }
    }
  } catch (error) {
    console.error(
      "Test tweet failed with error:",
      error instanceof Error ? error.message : error
    );
    process.exit(1);
  }
}

// Run the test
testTweet().catch((error) => {
  console.error("Unhandled error in test:", error);
  process.exit(1);
});
