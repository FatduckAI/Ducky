// db/schema.ts
import {
  boolean,
  integer,
  pgTable,
  real,
  serial,
  text,
  timestamp,
  varchar,
} from "drizzle-orm/pg-core";

export const duckyAi = pgTable("ducky_ai", {
  id: serial("id").primaryKey(),
  content: text("content").notNull(),
  tweetId: text("tweet_id"),
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
  sentimentPositive: real("sentiment_positive"),
  sentimentNegative: real("sentiment_negative"),
  sentimentHelpful: real("sentiment_helpful"),
  sentimentSarcastic: real("sentiment_sarcastic"),
  duckyReply: text("ducky_reply"),
  content: text("content"),
  sentimentAnalyzed: boolean("sentiment_analyzed").default(false),
});

export const hitchikerConversations = pgTable("hitchiker_conversations", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp"),
  content: text("content"),
  summary: text("summary"),
  tweetUrl: text("tweet_url"),
});

export const narratives = pgTable("narratives", {
  id: serial("id").primaryKey(),
  timestamp: text("timestamp"),
  content: text("content"),
  summary: text("summary"),
});

export const telegramMessages = pgTable("telegram_messages", {
  messageId: text("message_id"),
  chatId: text("chat_id"),
  senderId: text("sender_id"),
  senderUsername: text("sender_username"),
  content: text("content"),
  replyToMessageId: text("reply_to_message_id"),
  forwardFromId: text("forward_from_id"),
  forwardFromName: text("forward_from_name"),
  mediaType: text("media_type"),
  mediaFileId: text("media_file_id"),
  timestamp: timestamp("timestamp"),
  editedTimestamp: timestamp("edited_timestamp"),
  isPinned: boolean("is_pinned"),
  sentimentPositive: real("sentiment_positive"),
  sentimentNegative: real("sentiment_negative"),
  sentimentHelpful: real("sentiment_helpful"),
  sentimentSarcastic: real("sentiment_sarcastic"),
  sentimentAnalyzed: boolean("sentiment_analyzed").default(false),
});

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  telegramId: varchar("telegram_id", { length: 255 }),
  telegramUsername: varchar("telegram_username", { length: 255 }),
  solanaAddress: varchar("solana_address", { length: 44 }),
  twitterUsername: varchar("twitter_username", { length: 15 }),
  twitterName: varchar("twitter_name", { length: 50 }),
  ethAddress: varchar("eth_address", { length: 42 }),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
  isActive: boolean("is_active").default(true),
});

export const edgelord = pgTable("edgelord", {
  id: serial("id").primaryKey(),
  content: text("content").notNull(),
  tweetId: text("tweet_id").unique(),
  timestamp: text("timestamp").notNull(),
});

export const edgelordOneoff = pgTable("edgelord_oneoff", {
  id: serial("id").primaryKey(),
  content: text("content").notNull(),
  tweetId: text("tweet_id").unique(),
  timestamp: text("timestamp").notNull(),
});

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
  mentionType: text("mention_type").notNull(),
  engagementScore: real("engagement_score"),
  sentimentScore: real("sentiment_score"),
  priorityScore: real("priority_score"),
  retryCount: integer("retry_count").notNull().default(0),
  lastRetryAt: timestamp("last_retry_at", { withTimezone: true }),
  deletedAt: timestamp("deleted_at", { withTimezone: true }),
  sentimentPositive: real("sentiment_positive"),
  sentimentNegative: real("sentiment_negative"),
  sentimentHelpful: real("sentiment_helpful"),
  sentimentSarcastic: real("sentiment_sarcastic"),
  duckyReply: text("ducky_reply"),
  content: text("content"),
  sentimentAnalyzed: boolean("sentiment_analyzed").default(false),
  inReplyToId: text("in_reply_to_id"),
  threadDepth: text("thread_depth").default("0"),
  skippedReason: text("skipped_reason"),
  conversationId: text("conversation_id"),
});

export type DuckyAi = typeof duckyAi.$inferSelect;
export type NewDuckyAi = typeof duckyAi.$inferInsert;
export type TweetReply = typeof tweetReplies.$inferSelect;
export type NewTweetReply = typeof tweetReplies.$inferInsert;
export type MentionedTweet = typeof mentionedTweets.$inferSelect;
export type NewMentionedTweet = typeof mentionedTweets.$inferInsert;
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type TelegramMessage = typeof telegramMessages.$inferSelect;
export type NewTelegramMessage = typeof telegramMessages.$inferInsert;
