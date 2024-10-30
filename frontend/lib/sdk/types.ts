/**
 * Message priority and platform types
 */
export type MessagePriority = "low" | "normal" | "high" | "urgent";
export type MessagePlatform =
  | "discord"
  | "twitter"
  | "telegram"
  | "web"
  | "api";

/**
 * Agent action types
 */
export const AgentAction = {
  Ignore: "ignore",
  Continue: "continue",
  SwapToken: "swap_token",
} as const;

export type AgentAction = (typeof AgentAction)[keyof typeof AgentAction];

/**
 * Core interfaces
 */
export interface Message {
  content: string;
  conversationId: string;
  createdAt: string;
  id: string;
  metadata: Record<string, any>;
  threadId?: string;
  userId: string;
}

export interface ConversationState {
  platform: MessagePlatform;
  lastAction: AgentAction;
  messageCount: number;
  active: boolean;
  threadId?: string;
  lastActivity: number;
  retryAttempts: number;
}

export interface Conversation {
  id: string;
  userId: string;
  platform: MessagePlatform;
  startedAt: string;
  endedAt: string | null;
  isActive: boolean;
  metadata: Record<string, any>;
}

export interface PaginatedConversations {
  success: boolean;
  data: {
    conversations: Conversation[];
    totalCount: number;
    hasMore: boolean;
  };
}

export interface MessagesResponse {
  success: boolean;
  data: {
    messages: Message[];
    hasMore: boolean;
  };
  timestamp: number;
}

export interface HandlerStats {
  queueSize: number;
  activeConversations: number;
  messagesProcessed: number;
  errorCount: number;
  uptimeSeconds: number;
}

export interface PaginatedConversations {
  conversations: Conversation[];
  totalCount: number;
  hasMore: boolean;
}

export interface MessageHandlerConfig {
  baseUrl: string;
  apiKey?: string;
  defaultPriority?: MessagePriority;
  defaultPlatform?: MessagePlatform;
}

export interface MessageResponse {
  messages: Array<{
    id: string;
    userId: string;
    content: string;
    role: "user" | "assistant";
    timestamp: number;
  }>;
  hasMore: boolean;
  nextCursor?: string;
}

/**
 * Custom error class
 */
export class MessageHandlerError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "MessageHandlerError";
  }

  static isApiError(error: unknown): error is MessageHandlerError {
    return error instanceof MessageHandlerError;
  }
}
