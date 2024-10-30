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
  id: string;
  userId: string;
  content: string;
  threadId?: string;
  platform: MessagePlatform;
  priority: MessagePriority;
  metadata: Record<string, any>;
  timestamp: number;
  retryCount: number;
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
  state: ConversationState;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  isActive: boolean;
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
