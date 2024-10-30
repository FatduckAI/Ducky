import {
  Conversation,
  HandlerStats,
  MessageHandlerConfig,
  MessageHandlerError,
  MessagePlatform,
  MessagePriority,
  MessageResponse,
  MessagesResponse,
  PaginatedConversations,
} from "./types";
import { toCamelCaseKeys, toSnakeCaseKeys } from "./utils";

/**
 * Main SDK class
 */
export class MessageHandlerSDK {
  private baseUrl: string;
  private apiKey?: string;
  private defaultPriority: MessagePriority;
  private defaultPlatform: MessagePlatform;

  constructor(config: MessageHandlerConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, "");
    this.apiKey = config.apiKey;
    this.defaultPriority = config.defaultPriority || "normal";
    this.defaultPlatform = config.defaultPlatform || "web";
  }

  private createHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.createHeaders(),
      ...options.headers,
    };

    if (options.body) {
      options.body = JSON.stringify(
        toSnakeCaseKeys(JSON.parse(options.body as string))
      );
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new MessageHandlerError(
          error.message || "Request failed",
          response.status,
          error
        );
      }

      const data = await response.json();
      return toCamelCaseKeys(data) as T;
    } catch (error) {
      if (error instanceof MessageHandlerError) {
        throw error;
      }
      throw new MessageHandlerError("Request failed", 500, error);
    }
  }

  /**
   * Send a message to be processed by the handler
   */
  async sendMessage(input: {
    userId: string;
    content: string;
    platform?: MessagePlatform;
    priority?: MessagePriority;
    metadata?: Record<string, any>;
    threadId?: string;
  }): Promise<MessageResponse> {
    const message = {
      userId: input.userId,
      content: input.content,
      platform: input.platform || this.defaultPlatform,
      priority: input.priority || this.defaultPriority,
      metadata: input.metadata || {},
      threadId: input.threadId,
    };

    return this.fetch("/messages", {
      method: "POST",
      body: JSON.stringify(message),
    });
  }

  /**
   * Get a specific conversation by ID
   */
  async getConversation(conversationId: string): Promise<Conversation | null> {
    return this.fetch(`/conversations/${conversationId}`);
  }

  /**
   * List conversations for a user with pagination
   */
  async listConversations(params: {
    userId: string;
    includeInactive?: boolean;
    pageSize?: number;
    page?: number;
    platform?: MessagePlatform;
  }): Promise<PaginatedConversations> {
    const searchParams = new URLSearchParams(
      toSnakeCaseKeys({
        userId: params.userId,
        includeInactive: !!params.includeInactive,
        pageSize: params.pageSize || 20,
        page: params.page || 0,
        ...(params.platform && { platform: params.platform }),
      })
    );

    return this.fetch(`/conversations?${searchParams.toString()}`);
  }

  /**
   * Get messages for a conversation
   */
  async getConversationMessages(params: {
    conversationId: string;
    offset?: number;
    limit?: number;
  }): Promise<MessagesResponse> {
    console.log(params);
    const searchParams = new URLSearchParams(
      toSnakeCaseKeys({
        offset: params.offset,
        limit: params.limit || 20,
      })
    );
    console.log(
      `/conversations/${
        params.conversationId
      }/messages?${searchParams.toString()}`
    );
    return this.fetch(
      `/conversations/${
        params.conversationId
      }/messages?${searchParams.toString()}`
    );
  }

  /**
   * Get current handler statistics
   */
  async getStats(): Promise<HandlerStats> {
    return this.fetch("/stats");
  }
}

/**
 * Helper function to create SDK configuration
 */
export function createSdkConfig(
  baseUrl: string,
  options: Omit<MessageHandlerConfig, "baseUrl"> = {}
): MessageHandlerConfig {
  return {
    baseUrl,
    apiKey: options.apiKey,
    defaultPriority: options.defaultPriority || "normal",
    defaultPlatform: options.defaultPlatform || "web",
  };
}

// Example usage:
/*
const sdk = new MessageHandlerSDK(createSdkConfig(
  'https://api.example.com',
  { 
    apiKey: 'optional-api-key',
    defaultPlatform: 'discord',
    defaultPriority: 'normal'
  }
));

// Send a message
const result = await sdk.sendMessage({
  userId: 'user123',
  content: 'Hello!',
  metadata: {
    channelId: 'channel123',
    source: 'direct_message'
  }
});

// Get a conversation
const conversation = await sdk.getConversation('conversation-id');

// List conversations
const conversations = await sdk.listConversations({
  userId: 'user123',
  pageSize: 20,
  page: 0,
  platform: 'discord'
});

// Update conversation state
await sdk.updateConversationState('conversation-id', {
  messageCount: 5,
  lastAction: AgentAction.Continue
});
*/
