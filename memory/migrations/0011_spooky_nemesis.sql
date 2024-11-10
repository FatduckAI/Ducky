CREATE TABLE IF NOT EXISTS "finetune_tweets" (
	"id" serial PRIMARY KEY NOT NULL,
	"content" text NOT NULL,
	"tweet_id" text,
	"user_id" text NOT NULL,
	"timestamp" text NOT NULL,
	CONSTRAINT "finetune_tweets_tweet_id_unique" UNIQUE("tweet_id")
);
