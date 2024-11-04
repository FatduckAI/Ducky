CREATE TABLE IF NOT EXISTS "ducky_ai" (
	"id" serial PRIMARY KEY NOT NULL,
	"content" text NOT NULL,
	"tweet_id" text,
	"posttime" text,
	"posted" boolean DEFAULT false,
	"timestamp" text NOT NULL,
	"conversation_id" text,
	"speaker" text
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "edgelord" (
	"id" serial PRIMARY KEY NOT NULL,
	"content" text NOT NULL,
	"tweet_id" text,
	"timestamp" text NOT NULL,
	CONSTRAINT "edgelord_tweet_id_unique" UNIQUE("tweet_id")
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "edgelord_oneoff" (
	"id" serial PRIMARY KEY NOT NULL,
	"content" text NOT NULL,
	"tweet_id" text,
	"timestamp" text NOT NULL,
	CONSTRAINT "edgelord_oneoff_tweet_id_unique" UNIQUE("tweet_id")
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "hitchiker_conversations" (
	"id" serial PRIMARY KEY NOT NULL,
	"timestamp" text,
	"content" text,
	"summary" text,
	"tweet_url" text
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "narratives" (
	"id" serial PRIMARY KEY NOT NULL,
	"timestamp" text,
	"content" text,
	"summary" text
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "telegram_messages" (
	"message_id" text,
	"chat_id" text,
	"sender_id" text,
	"sender_username" text,
	"content" text,
	"reply_to_message_id" text,
	"forward_from_id" text,
	"forward_from_name" text,
	"media_type" text,
	"media_file_id" text,
	"timestamp" timestamp,
	"edited_timestamp" timestamp,
	"is_pinned" boolean,
	"sentiment_positive" real,
	"sentiment_negative" real,
	"sentiment_helpful" real,
	"sentiment_sarcastic" real,
	"sentiment_analyzed" boolean DEFAULT false
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "tweet_replies" (
	"id" text PRIMARY KEY NOT NULL,
	"parent_tweet_id" text NOT NULL,
	"author" text NOT NULL,
	"text" text NOT NULL,
	"created_at" timestamp NOT NULL,
	"likes" integer DEFAULT 0,
	"retweets" integer DEFAULT 0,
	"author_followers" integer DEFAULT 0,
	"author_verified" boolean DEFAULT false,
	"processed" boolean DEFAULT false,
	"response_tweet_id" text,
	"processed_at" timestamp,
	"created_timestamp" timestamp DEFAULT now(),
	"sentiment_positive" real,
	"sentiment_negative" real,
	"sentiment_helpful" real,
	"sentiment_sarcastic" real,
	"ducky_reply" text,
	"content" text
);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS "users" (
	"id" serial PRIMARY KEY NOT NULL,
	"telegram_id" varchar(255),
	"telegram_username" varchar(255),
	"solana_address" varchar(44),
	"twitter_username" varchar(15),
	"twitter_name" varchar(50),
	"eth_address" varchar(42),
	"created_at" timestamp DEFAULT now(),
	"updated_at" timestamp DEFAULT now(),
	"is_active" boolean DEFAULT true
);
