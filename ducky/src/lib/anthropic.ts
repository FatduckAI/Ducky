// anthropicService.ts
import Anthropic from "@anthropic-ai/sdk";

interface AnthropicConfig {
  apiKey: string;
  model: string;
  maxTokens: number;
}

const defaultConfig: AnthropicConfig = {
  apiKey: process.env.ANTHROPIC_API_KEY || "",
  model: "claude-3-5-sonnet-20241022",
  maxTokens: 1024,
};

let anthropicInstance: Anthropic | null = null;

export const getAnthropicClient = (): Anthropic => {
  if (!anthropicInstance) {
    anthropicInstance = new Anthropic({
      apiKey: defaultConfig.apiKey,
    });
  }
  return anthropicInstance;
};

export const generateClaudeResponse = async (
  systemPrompt: string,
  userPrompt: string
): Promise<string> => {
  const client = getAnthropicClient();

  const response = await client.messages.create({
    model: defaultConfig.model,
    max_tokens: defaultConfig.maxTokens,
    system: [{ type: "text", text: systemPrompt }],
    messages: [
      {
        role: "user",
        content: userPrompt,
      },
    ],
  });

  const textContent = response.content.find((block) => block.type === "text");
  return textContent && "text" in textContent ? textContent.text : "";
};

interface SentimentAnalysis {
  sentiment_scores: {
    positive: number;
    negative: number;
    helpful: number;
    sarcastic: number;
  };
  confidence: number;
  analysis_timestamp: string;
}

export async function analyzeSentiment(text: string): Promise<number[]> {
  try {
    // Pre-fill the exact JSON structure we want
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

    const message = await getAnthropicClient().messages.create({
      model: "claude-3-sonnet-20240229",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: `Analyze the sentiment of this text. Return ONLY a JSON object matching this EXACT structure, with no additional text or explanation:

${JSON.stringify(jsonTemplate, null, 2)}

Rules:
- All sentiment scores must be numbers between 0 and 1
- Confidence must be between 0 and 1
- Do not include any explanatory text
- Do not modify the JSON structure
- Use the current timestamp

Sentiment Rules:
- messages about check dms are not helpful, nor positive, they should have a low negative score
- messages that are obvious spam should have a low positive score and high negative score
- messages that are obviously sarcastic should have a high sarcastic score
- messages that are helpful should have a high helpful score



Text to analyze: "${text}"`,
        },
      ],
    });

    // Get the response content and check for text content
    const responseContent = message.content[0];
    if (!isTextBlock(responseContent)) {
      throw new Error("Unexpected response type from Claude");
    }

    const responseText = responseContent.text; // Use 'text' instead of 'value'
    if (!responseText) {
      throw new Error("No text content in response");
    }

    // Parse and validate the JSON
    const analysis = JSON.parse(responseText) as SentimentAnalysis;

    // Validate the structure matches our template
    if (!validateSentimentAnalysis(analysis)) {
      throw new Error("Invalid sentiment analysis structure");
    }

    // Validate the structure matches our template
    if (!validateSentimentAnalysis(analysis)) {
      throw new Error("Invalid sentiment analysis structure");
    }
    // Extract just the scores in our expected order
    return [
      analysis.sentiment_scores.positive,
      analysis.sentiment_scores.negative,
      analysis.sentiment_scores.helpful,
      analysis.sentiment_scores.sarcastic,
    ];
  } catch (error) {
    console.error("Error analyzing sentiment:", error);
    console.error("Problematic text:", text);
    // Return neutral scores in case of error
    return [0.5, 0.5, 0.5, 0.5];
  }
}

// Add type guard for response content
function isTextBlock(content: any): content is { type: "text"; text: string } {
  return (
    typeof content === "object" &&
    content !== null &&
    content.type === "text" &&
    typeof content.text === "string"
  );
}

// Type guard to validate the sentiment analysis structure
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

// Quick Test
/* const a = await analyzeSentiment("I love this product");
const b = await analyzeSentiment("I hate this product");
const c = await analyzeSentiment("This product is okay.");
const d = await analyzeSentiment("talk back duck");
const e = await analyzeSentiment("will DuckAI moon");

console.log([
  {
    text: "I love this product",
    sentiment: a,
  },
  {
    text: "I hate this product",
    sentiment: b,
  },
  {
    text: "This product is okay.",
    sentiment: c,
  },
  {
    text: "talk back duck",
    sentiment: d,
  },
  {
    text: "will DuckAI moon",
    sentiment: e,
  },
]);
 */
