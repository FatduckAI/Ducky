export interface AgentConfig {
  name: string;
  provider: AIProvider;
  delivery: DeliverySystem;
  prompt: PromptTemplate;
  rag?: RAGSystem;
  isTestMode?: boolean;
}

export interface AIProvider {
  type: string;
  generateResponse: (
    systemPrompt: string,
    userPrompt: string
  ) => Promise<string>;
  analyzeSentiment?: (text: string) => Promise<number[]>;
}

export interface DeliverySystem {
  type: string;
  send: (content: string, replyToId?: string) => Promise<void>;
  getRecentMessages?: () => Promise<string[]>;
}

export interface AgentTask {
  name: string;
  description?: string;
  cronPattern?: string;
  systemPrompt: string;
  prompt: () => Promise<string>;
  provider: AIProvider;
  delivery: DeliverySystem;
}

export interface PromptContext {
  recentTweets?: string[];
  replyToTweet?: string;
  conversation?: string;
  humanInput?: string;
  tweets?: Array<{ author: string; text: string; engagement: number }>;
}

export interface PromptTemplate {
  generate: (context?: PromptContext) => PromptOutput;
}

export interface PromptOutput {
  systemPrompt: string;
  userPrompt: string;
}

export interface RAGSystem {
  getContext: () => Promise<any>;
  processContext?: (context: any) => any;
}
