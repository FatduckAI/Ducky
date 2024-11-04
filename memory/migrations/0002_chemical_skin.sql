ALTER TABLE "mentioned_tweets" ADD COLUMN "sentiment_analyzed" boolean DEFAULT false;--> statement-breakpoint
ALTER TABLE "tweet_replies" ADD COLUMN "sentiment_analyzed" boolean DEFAULT false;