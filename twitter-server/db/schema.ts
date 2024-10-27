// db/schema.ts
import {
  boolean,
  integer,
  pgTable,
  serial,
  text,
  timestamp,
} from "drizzle-orm/pg-core";

export const duckyAi = pgTable("ducky_ai", {
  id: serial("id").primaryKey(),
  content: text("content").notNull(),
  tweetId: text("tweet_id").unique(),
  postTime: text("posttime"),
  posted: boolean("posted").default(false),
  timestamp: text("timestamp").notNull(),
  conversationId: text("conversation_id"),
  speaker: text("speaker"),
});

export const tweetReplies = pgTable("tweet_replies", {
  id: text("id").primaryKey(),
  parentTweetId: text("parent_tweet_id").notNull(),
  author: text("author").notNull(),
  text: text("text").notNull(),
  createdAt: timestamp("created_at").notNull(),
  likes: integer("likes").default(0),
  retweets: integer("retweets").default(0),
  authorFollowers: integer("author_followers").default(0),
  authorVerified: boolean("author_verified").default(false),
  processed: boolean("processed").default(false),
  responseTweetId: text("response_tweet_id"),
  processedAt: timestamp("processed_at"),
  createdTimestamp: timestamp("created_timestamp").defaultNow(),
});

export type DuckyAi = typeof duckyAi.$inferSelect;
export type NewDuckyAi = typeof duckyAi.$inferInsert;
export type TweetReply = typeof tweetReplies.$inferSelect;
export type NewTweetReply = typeof tweetReplies.$inferInsert;
