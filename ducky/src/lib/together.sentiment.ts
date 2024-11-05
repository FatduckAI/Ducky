import Together from "together-ai";
import { defaultConfig } from "./together";

const BASE_PROMPT = `Rules:
- All sentiment scores must be numbers between 0 and 1
- Confidence must be between 0 and 1
- Do not include any explanatory text
- Do not modify the JSON structure
- Use the current timestamp

Sentiment Rules:
- the messages are from a telegram chat amoungst web3 and crypto people, tailor the scores to that lexicon
- messages about direct messages, dms, pms etc. are not helpful, nor positive, they should have a low negative score
- messages that are obvious spam should have a low positive score and high negative score
- messages that are obviously sarcastic should have a high sarcastic score
- messages including the terms raid are helpful
`;

let togetherInstance: Together | null = null;

export const getTogetherClient = (): Together => {
  if (!togetherInstance) {
    togetherInstance = new Together({
      apiKey: defaultConfig.apiKey,
    });
  }
  return togetherInstance;
};

interface SentimentScores {
  positive: number;
  negative: number;
  helpful: number;
  sarcastic: number;
}

interface SentimentAnalysis {
  sentiment_scores: SentimentScores;
  confidence: number;
  analysis_timestamp: string;
}

// Single text analysis
export async function analyzeSentiment(text: string): Promise<number[]> {
  try {
    const client = getTogetherClient();

    const jsonTemplate = {
      sentiment_scores: {
        positive: 0,
        negative: 0,
        helpful: 0,
        sarcastic: 0,
      },
      confidence: 0,
      analysis_timestamp: new Date().toISOString(),
    };

    const messages = [
      {
        role: "system" as const,
        content:
          "You are a sentiment analysis expert. Return ONLY a JSON object with sentiment analysis. No additional text or explanation.",
      },
      {
        role: "user" as const,
        content: `Return ONLY a JSON object matching this structure:

${JSON.stringify(jsonTemplate, null, 2)}

${BASE_PROMPT}

Text to analyze: "${text}"`,
      },
    ];

    const completion = await client.chat.completions.create({
      model: defaultConfig.model,
      messages: messages,
      max_tokens: defaultConfig.maxTokens,
      temperature: 0.1,
    });

    const responseText = completion.choices[0]?.message?.content;
    if (!responseText) {
      throw new Error("No content in response");
    }

    // Extract JSON from the response
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error("No JSON found in response");
    }

    const analysis = JSON.parse(jsonMatch[0]) as SentimentAnalysis;

    // Validate the structure
    if (!validateSentimentAnalysis(analysis)) {
      throw new Error("Invalid sentiment analysis structure");
    }

    return [
      analysis.sentiment_scores.positive,
      analysis.sentiment_scores.negative,
      analysis.sentiment_scores.helpful,
      analysis.sentiment_scores.sarcastic,
    ];
  } catch (error) {
    console.error("Error analyzing sentiment:", error);
    if (error instanceof Error) {
      console.error("Error message:", error.message);
    }
    console.error("Text:", text);
    return [0.5, 0.5, 0.5, 0.5];
  }
}

function validateSentimentAnalysis(data: any): data is SentimentAnalysis {
  try {
    return (
      typeof data === "object" &&
      data !== null &&
      typeof data.confidence === "number" &&
      data.confidence >= 0 &&
      data.confidence <= 1 &&
      typeof data.analysis_timestamp === "string" &&
      typeof data.sentiment_scores === "object" &&
      data.sentiment_scores !== null &&
      typeof data.sentiment_scores.positive === "number" &&
      data.sentiment_scores.positive >= 0 &&
      data.sentiment_scores.positive <= 1 &&
      typeof data.sentiment_scores.negative === "number" &&
      data.sentiment_scores.negative >= 0 &&
      data.sentiment_scores.negative <= 1 &&
      typeof data.sentiment_scores.helpful === "number" &&
      data.sentiment_scores.helpful >= 0 &&
      data.sentiment_scores.helpful <= 1 &&
      typeof data.sentiment_scores.sarcastic === "number" &&
      data.sentiment_scores.sarcastic >= 0 &&
      data.sentiment_scores.sarcastic <= 1
    );
  } catch {
    return false;
  }
}

interface BatchOptions {
  maxRequestsPerMinute?: number;
  logProgress?: boolean;
}

/**
 * Process an array of texts in batches while respecting rate limits
 */
export async function processSentimentBatch(
  texts: string[],
  options: BatchOptions = {}
) {
  const {
    maxRequestsPerMinute = 55, // Leave some buffer below 60
    logProgress = true,
  } = options;

  const results: number[][] = [];
  const errors: { index: number; error: any }[] = [];

  // Calculate timing
  const minDelayBetweenRequests = (60 * 1000) / maxRequestsPerMinute;
  let lastRequestTime = 0;

  for (let i = 0; i < texts.length; i++) {
    // Ensure we don't exceed rate limit
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    if (timeSinceLastRequest < minDelayBetweenRequests) {
      await new Promise((resolve) =>
        setTimeout(resolve, minDelayBetweenRequests - timeSinceLastRequest)
      );
    }

    try {
      lastRequestTime = Date.now();
      const result = await analyzeSentiment(texts[i]);
      results[i] = result;

      if (logProgress && (i + 1) % 10 === 0) {
        const progress = (((i + 1) / texts.length) * 100).toFixed(1);
        console.log(`Progress: ${i + 1}/${texts.length} (${progress}%)`);
      }
    } catch (error) {
      errors.push({ index: i, error });
      results[i] = [0.5, 0.5, 0.5, 0.5]; // Default scores for errors
    }
  }

  if (errors.length > 0) {
    console.error(`Completed with ${errors.length} errors`);
  }

  return {
    results,
    errors,
    total: texts.length,
    successful: texts.length - errors.length,
  };
}

/**
 * Process texts with support for previous scores comparison
 */
export async function processSentimentBatchWithComparison(
  texts: string[],
  previousScores?: Array<[number, number, number, number]>,
  options: BatchOptions = {}
) {
  const { results, errors, total, successful } = await processSentimentBatch(
    texts,
    options
  );

  const changes: Array<{
    index: number;
    text: string;
    previous?: number[];
    new: number[];
    changed: boolean;
  }> = [];

  results.forEach((scores, index) => {
    const previous = previousScores?.[index];
    const hasChanged = previous && hasSignificantChange(previous, scores);

    if (hasChanged) {
      changes.push({
        index,
        text: texts[index],
        previous,
        new: scores,
        changed: true,
      });
      console.log(`\nScore change detected for text [${index}]:`);
      console.log(
        `Text: "${texts[index].substring(0, 100)}${
          texts[index].length > 100 ? "..." : ""
        }"`
      );
      if (previous) {
        console.log(
          `Previous: [pos: ${previous[0].toFixed(
            2
          )}, neg: ${previous[1].toFixed(2)}, help: ${previous[2].toFixed(
            2
          )}, sarc: ${previous[3].toFixed(2)}]`
        );
      }
      console.log(
        `New:      [pos: ${scores[0].toFixed(2)}, neg: ${scores[1].toFixed(
          2
        )}, help: ${scores[2].toFixed(2)}, sarc: ${scores[3].toFixed(2)}]`
      );
    }
  });

  return {
    results,
    errors,
    changes,
    total,
    successful,
  };
}

function hasSignificantChange(
  previous: number[],
  current: number[],
  threshold = 0.1
): boolean {
  return previous.some(
    (value, index) => Math.abs(value - current[index]) > threshold
  );
}
