import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";
import { and, asc, desc, eq, gt } from "drizzle-orm";
import { db } from ".";
import {
  btcPriceData,
  duckyAi,
  finetuneTweets,
  genericData,
  githubPRAnalysis,
  users,
} from "./schema";

dayjs.extend(utc);
dayjs.extend(timezone);

const EST_TIMEZONE = "America/New_York";

export const getCurrentEstTime = () => {
  return dayjs().tz(EST_TIMEZONE);
};

export const formatEstTime = (date: Date) => {
  return dayjs(date).tz(EST_TIMEZONE).format();
};

export const saveMessageToDb = async (
  content: string,
  speaker: string,
  conversationIndex: number,
  conversationId?: string
) => {
  const timestamp = formatEstTime(getCurrentEstTime().toDate());
  const messageId = `${speaker.toLowerCase()}_${timestamp}_${conversationIndex}`;

  await db.insert(duckyAi).values({
    content,
    tweetId: messageId,
    timestamp,
    posted: false,
    speaker,
    conversationId,
  });
};

export const saveTweetToDbScheduled = async (
  tweetContent: string,
  conversationId: string,
  conversationIndex: number
) => {
  const timestamp = formatEstTime(getCurrentEstTime().toDate());
  const currentTime = getCurrentEstTime();

  // Round up to next hour
  const baseHour = currentTime.add(1, "hour").startOf("hour");

  // Add hours based on conversation index
  const scheduledTime = baseHour.add(conversationIndex, "hour");

  const tweetId = `ducky_reflection_${scheduledTime.format("YYYYMMDD_HHmmss")}`;
  const cleanContent = tweetContent.replace(/^"|"$/g, "");

  await db.insert(duckyAi).values({
    content: cleanContent,
    tweetId,
    timestamp,
    posted: false,
    postTime: formatEstTime(scheduledTime.toDate()),
    speaker: "Ducky",
    conversationId,
  });

  return scheduledTime.toDate();
};

export const getDuckyAiTweets = async () => {
  return await db
    .select({
      id: duckyAi.id,
      content: duckyAi.content,
      tweetId: duckyAi.tweetId,
      timestamp: duckyAi.timestamp,
      speaker: duckyAi.speaker,
    })
    .from(duckyAi)
    .where(
      and(
        gt(
          duckyAi.timestamp,
          formatEstTime(dayjs().subtract(3, "hours").toDate())
        ),
        eq(duckyAi.posted, true)
      )
    )
    .orderBy(desc(duckyAi.timestamp))
    .limit(50);
};

export const getDuckyAiTweetsByConversationId = async (
  conversationId: string
) => {
  const res = await db
    .select()
    .from(duckyAi)
    .where(eq(duckyAi.tweetId, conversationId));
  return res.length > 0;
};

export const getDuckyAiForTweetGenerationTweets = async () => {
  return await db
    .select({
      id: duckyAi.id,
      content: duckyAi.content,
      tweetId: duckyAi.tweetId,
      timestamp: duckyAi.timestamp,
      speaker: duckyAi.speaker,
    })
    .from(duckyAi)
    .where(and(eq(duckyAi.speaker, "Ducky"), eq(duckyAi.posted, true)))
    .orderBy(desc(duckyAi.timestamp))
    .limit(50);
};

export const getTweetsFromFinetune = async () => {
  return await db.select().from(finetuneTweets).limit(150);
};

export const getGenericData = async () => {
  return await db.select().from(genericData);
};

export const getGithubPRAnalysis = async () => {
  return await db.select().from(githubPRAnalysis);
};

export const getDuckyAiForTweetGenerationCleo = async () => {
  return await db
    .select({
      id: duckyAi.id,
      content: duckyAi.content,
      tweetId: duckyAi.tweetId,
      timestamp: duckyAi.timestamp,
      speaker: duckyAi.speaker,
    })
    .from(duckyAi)
    .where(and(eq(duckyAi.speaker, "Ducky"), eq(duckyAi.posted, false)))
    .orderBy(asc(duckyAi.timestamp))
    .limit(50);
};

export const saveTweetToDbPosted = async (
  content: string,
  tweetUrl: string
) => {
  const timestamp = formatEstTime(getCurrentEstTime().toDate());

  await db.insert(duckyAi).values({
    content,
    posted: true,
    timestamp,
    tweetId: tweetUrl,
    postTime: timestamp,
    speaker: "Ducky",
  });
};

export const saveTweetToDbNotPosted = async (content: string) => {
  const timestamp = formatEstTime(getCurrentEstTime().toDate());
  const tweetId = `ducky_reflection_${timestamp}`;

  await db.insert(duckyAi).values({
    content,
    posted: false,
    timestamp,
    tweetId,
    postTime: timestamp,
    speaker: "Ducky",
  });
};

export const getUserByUsername = async (username: string) => {
  const res = await db
    .select()
    .from(users)
    .where(eq(users.telegramUsername, username));
  return res[0];
};

export async function checkPRAnalysisExists(
  prNumber: number,
  repoOwner: string,
  repoName: string
): Promise<boolean> {
  const existing = await db
    .select({ id: githubPRAnalysis.id })
    .from(githubPRAnalysis)
    .where(
      and(
        eq(githubPRAnalysis.prNumber, prNumber),
        eq(githubPRAnalysis.repoOwner, repoOwner),
        eq(githubPRAnalysis.repoName, repoName)
      )
    )
    .limit(1);

  return existing.length > 0;
}

export async function savePRAnalysis(analysisData: {
  prNumber: number;
  prTitle: string;
  prAuthor: string;
  repoOwner: string;
  repoName: string;
  mergeSha: string;
  analysis: string;
  fileCount: number;
  additions: number;
  deletions: number;
  tweetId?: string;
}) {
  return db.insert(githubPRAnalysis).values({
    ...analysisData,
    posted: !!analysisData.tweetId,
  });
}

export const getLatestBTCPrice = async () => {
  const res = await db
    .select()
    .from(btcPriceData)
    .orderBy(desc(btcPriceData.timestamp))
    .limit(1);
  return res[0];
};
