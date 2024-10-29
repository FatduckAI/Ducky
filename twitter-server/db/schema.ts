// db/schema.ts
import {
  boolean,
  integer,
  pgEnum,
  pgTable,
  real,
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

const mentionType = pgEnum("mention_type", ["username", "token", "keyword"]);

export const mentionedTweets = pgTable("mentioned_tweets", {
  id: text("id").primaryKey(),
  text: text("text").notNull(),
  author: text("author").notNull(),
  authorUsername: text("author_username").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull(),
  likes: integer("likes").notNull().default(0),
  retweets: integer("retweets").notNull().default(0),
  authorFollowers: integer("author_followers").notNull().default(0),
  authorVerified: boolean("author_verified").notNull().default(false),
  processed: boolean("processed").notNull().default(false),
  processedAt: timestamp("processed_at", { withTimezone: true }),
  createdTimestamp: timestamp("created_timestamp", { withTimezone: true })
    .notNull()
    .defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow(),
  responseTweetId: text("response_tweet_id"),
  responseText: text("response_text"),
  responseError: text("response_error"),
  searchQuery: text("search_query").notNull(),
  mentionType: mentionType("mention_type").notNull(),
  engagementScore: real("engagement_score"),
  sentimentScore: real("sentiment_score"),
  priorityScore: real("priority_score"),
  retryCount: integer("retry_count").notNull().default(0),
  lastRetryAt: timestamp("last_retry_at", { withTimezone: true }),
  deletedAt: timestamp("deleted_at", { withTimezone: true }),
});

export type DuckyAi = typeof duckyAi.$inferSelect;
export type NewDuckyAi = typeof duckyAi.$inferInsert;
export type TweetReply = typeof tweetReplies.$inferSelect;
export type NewTweetReply = typeof tweetReplies.$inferInsert;
