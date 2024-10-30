// src/handler.rs

//! Message handling and conversation management module.
//! 
//! This module provides the core message processing functionality, including:
//! - Message queue management
//! - Rate limiting
//! - Conversation state tracking
//! - Integration with the Claude AI service
//! - Database persistence
//! 
//! The main component is the `MessageHandler` which orchestrates all these features.

use std::sync::Arc;
use std::collections::HashMap;
use tokio::sync::RwLock;
use chrono::{DateTime, Utc};
use deadpool_postgres::Pool;
use tracing::{debug, error, info, instrument};
use serde::Serialize;
use serde_json::json;
use uuid::Uuid;
use warp::reject::Rejection;
use warp::reply::Reply;

use crate::models::{ConversationState, Message};
use crate::queue::MessageQueue;
use crate::error::ServiceError;
use crate::db::{self, queries, Conversation, StoredMessage};
use crate::services::ClaudeClient;

/// Maximum number of retry attempts for failed message processing
const MAX_RETRIES: u32 = 3;
/// Time window in seconds for rate limiting
const RATE_LIMIT_WINDOW: i64 = 60;
/// Maximum number of messages allowed per rate limit window
const RATE_LIMIT_MAX: u32 = 100;

/// Handles all message processing and conversation management.
#[derive(Debug)]
pub struct MessageHandler {
    /// Active conversation states indexed by user ID
    conversations: Arc<RwLock<HashMap<String, ConversationState>>>,
    /// Message processing queue
    queue: Arc<RwLock<MessageQueue>>,
    /// Database connection pool
    db_pool: Pool,
    /// Rate limiting state by user ID
    rate_limiter: Arc<RwLock<HashMap<String, (i64, u32)>>>,
    /// Claude API client
    claude_client: Arc<ClaudeClient>,
    /// Handler creation timestamp
    started_at: DateTime<Utc>,
}

/// Statistics about the message handler's operation
#[derive(Debug, Clone, Serialize)]
pub struct HandlerStats {
    /// Current number of messages in the queue
    pub queue_size: usize,
    /// Number of active conversations
    pub active_conversations: usize,
    /// Total messages processed since startup
    pub messages_processed: u64,
    /// Total errors encountered since startup
    pub error_count: u64,
    /// Uptime in seconds
    pub uptime_seconds: i64,
}

impl MessageHandler {
    /// Creates a new message handler with the specified queue size and database pool.
    /// 
    /// # Arguments
    /// * `queue_size` - Maximum number of messages that can be queued
    /// * `db_pool` - Database connection pool
    /// 
    /// # Errors
    /// Returns an error if the ANTHROPIC_API_KEY environment variable is not set
    pub fn new(queue_size: usize, db_pool: Pool) -> Result<Self, ServiceError> {
        let api_key = std::env::var("ANTHROPIC_API_KEY")
            .map_err(|_| ServiceError::ConfigError("ANTHROPIC_API_KEY not set".to_string()))?;

        Ok(Self {
            conversations: Arc::new(RwLock::new(HashMap::new())),
            queue: Arc::new(RwLock::new(MessageQueue::new(queue_size))),
            db_pool,
            rate_limiter: Arc::new(RwLock::new(HashMap::new())),
            claude_client: Arc::new(ClaudeClient::new(api_key)),
            started_at: Utc::now(),
        })
    }

    /// Handles an incoming message by validating it and adding it to the processing queue.
    /// 
    /// # Arguments
    /// * `message` - The message to handle
    /// 
    /// # Errors
    /// Returns an error if:
    /// - Rate limit is exceeded
    /// - Message validation fails
    /// - Queue is full
    #[instrument(skip(handler, message))]
    pub async fn handle_message(
        message: Message,
        handler: Arc<MessageHandler>,
    ) -> Result<impl Reply, Rejection> {
        info!("Received message: {:?}", message);
        
        // Clone needed values before moving message
        let message_id = message.id;
  
        let response = tokio::spawn(async move {
            handler.process_message(&message).await
        })
        .await
        .map_err(|e| {
            error!("Task join error: {:?}", e);
            warp::reject::custom(ServiceError::Internal("Task join failed".to_string()))
        })?
        .map_err(|e| {
            error!("Message processing error: {:?}", e);
            warp::reject::custom(ServiceError::ProcessingError(e.to_string()))
        })?;
  
        Ok(warp::reply::json(&json!({
            "success": true,
            "response": response,
            "message_id": message_id,
            "timestamp": chrono::Utc::now().timestamp()
        })))
    }

    /// Starts the message processing loop. This method runs indefinitely and should
    /// be spawned in its own task.
    pub async fn start_processing(self: Arc<Self>) {
        info!("Starting message processing loop");
        
        loop {
            if let Err(e) = self.process_next_message().await {
                error!("Error processing message: {:?}", e);
            }

            // Cleanup expired conversations every 5 minutes
            if Utc::now().timestamp() % 300 == 0 {
                if let Err(e) = self.cleanup_expired_conversations().await {
                    error!("Error cleaning up conversations: {:?}", e);
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        }
    }

    /// Processes a single message, managing the conversation state and interacting with Claude.
    /// 
    /// # Arguments
    /// * `message` - The message to process
    /// 
    /// # Returns
    /// The response from Claude
    #[instrument(skip(self, message))]
    pub async fn process_message(&self, message: &Message) -> Result<String, ServiceError> {
        let db_client = self.db_pool.get().await
            .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

        let conversation = match queries::find_active_conversation(&db_client, &message.user_id).await? {
            Some(conv) => conv,
            None => {
                debug!("Creating new conversation for user {}", message.user_id);
                queries::create_conversation(
                    &db_client,
                    &message.user_id,
                    message.platform.clone(),
                    json!(message.metadata),
                ).await?
            }
        };

        queries::save_message(
            &db_client,
            conversation.id,
            &message.user_id,
            &message.content,
            message.thread_id.as_deref(),
            message.platform.clone(),
            json!(message.metadata),
        ).await?;

        let context: Vec<db::models::StoredMessage> = queries::get_recent_messages(&db_client, &message.user_id, 5_i64).await?;
        let prompt = self.build_prompt(message, &context)?;
        let response = self.claude_client.get_response(&prompt).await?;

        // Save Claude's response
        queries::save_message(
            &db_client,
            conversation.id,
            "claude",
            &response,
            message.thread_id.as_deref(),
            message.platform.clone(),
            json!(message.metadata),
        ).await?;

        Ok(response)
    }

    /// Retrieves current handler statistics
    pub fn get_stats(&self) -> HandlerStats {
        HandlerStats {
            queue_size: self.queue.try_read().map(|q| q.len()).unwrap_or(0),
            active_conversations: self.conversations.try_read().map(|c| c.len()).unwrap_or(0),
            messages_processed: 0, // TODO: Implement counter
            error_count: 0,        // TODO: Implement counter
            uptime_seconds: (Utc::now() - self.started_at).num_seconds(),
        }
    }

    // Private helper methods
    async fn process_next_message(&self) -> Result<(), ServiceError> {
        let message = {
            let mut queue = self.queue.write().await;
            queue.pop().await
        };

        if let Some(message) = message {
            match self.process_message(&message).await {
                Ok(response) => {
                    info!("Successfully processed message: {}", message.id);
                    self.save_response(&message, &response).await?;
                }
                Err(e) => {
                    error!("Failed to process message {}: {:?}", message.id, e);
                    if message.retry_count < MAX_RETRIES {
                        let mut retried_msg = message;
                        retried_msg.retry_count += 1;
                        let mut queue = self.queue.write().await;
                        queue.push(retried_msg).await?;
                    } else {
                        self.handle_failed_message(&message).await?;
                    }
                }
            }
        }

        Ok(())
    }

    async fn check_rate_limit(&self, user_id: &str) -> Result<(), ServiceError> {
        let mut rate_limiter = self.rate_limiter.write().await;
        let now = Utc::now().timestamp();

        if let Some((last_time, count)) = rate_limiter.get(user_id) {
            if now - last_time < RATE_LIMIT_WINDOW && *count >= RATE_LIMIT_MAX {
                return Err(ServiceError::RateLimitExceeded(
                    format!("Rate limit exceeded for user {}", user_id)
                ));
            }
        }

        rate_limiter
            .entry(user_id.to_string())
            .and_modify(|(time, count)| {
                if now - *time >= RATE_LIMIT_WINDOW {
                    *time = now;
                    *count = 1;
                } else {
                    *count += 1;
                }
            })
            .or_insert((now, 1));

        Ok(())
    }

    fn validate_message(&self, message: &Message) -> Result<(), ServiceError> {
        if message.content.is_empty() {
            return Err(ServiceError::InvalidMessage("Empty message content".to_string()));
        }

        if message.user_id.is_empty() {
            return Err(ServiceError::InvalidMessage("Empty user ID".to_string()));
        }

        if message.content.chars().count() > 4000 {
            return Err(ServiceError::InvalidMessage("Message too long".to_string()));
        }

        Ok(())
    }

    async fn handle_failed_message(&self, message: &Message) -> Result<(), ServiceError> {
        let db_client = self.db_pool.get().await
            .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

        queries::mark_message_failed(&db_client, message.id).await?;

        if let Ok(webhook_url) = std::env::var("ERROR_WEBHOOK_URL") {
            self.send_error_notification(&webhook_url, message).await?;
        }

        Ok(())
    }

    async fn send_error_notification(&self, webhook_url: &str, message: &Message) -> Result<(), ServiceError> {
        let client = reqwest::Client::new();
        let notification = json!({
            "message_id": message.id,
            "user_id": message.user_id,
            "error": "Message processing failed after max retries",
            "timestamp": Utc::now().timestamp()
        });

        client.post(webhook_url)
            .json(&notification)
            .send()
            .await
            .map_err(|e| ServiceError::ProcessingError(e.to_string()))?;

        Ok(())
    }

    fn build_prompt(&self, message: &Message, context: &Vec<db::models::StoredMessage>) -> Result<String, ServiceError> {
        let mut prompt = String::new();

        if !context.is_empty() {
            prompt.push_str("Previous conversation:\n");
            for msg in context {
                prompt.push_str(&format!("{}: {}\n",
                    if msg.user_id == "claude" { "Assistant" } else { "Human" },
                    msg.content
                ));
            }
            prompt.push_str("\n");
        }

        prompt.push_str(&format!("Human: {}\n\nAssistant:", message.content));

        Ok(prompt)
    }

    async fn save_response(&self, original_message: &Message, response: &str) -> Result<(), ServiceError> {
        let db_client = self.db_pool.get().await
            .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

        queries::save_response_metrics(
            &db_client,
            original_message.id,
            response.len() as i32,
            Utc::now().timestamp() - original_message.timestamp,
        ).await?;

        Ok(())
    }

    async fn cleanup_expired_conversations(&self) -> Result<(), ServiceError> {
        let db_client = self.db_pool.get().await
            .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

        let count = queries::close_expired_conversations(&db_client).await?;
        if count > 0 {
            info!("Closed {} expired conversations", count);
        }

        Ok(())
    }
     /// Retrieves a specific conversation by ID.
    /// 
    /// # Arguments
    /// * `conversation_id` - The UUID of the conversation to retrieve
    /// 
    /// # Returns
    /// The conversation if found, None otherwise
    pub async fn get_conversation(
      &self,
      conversation_id: Uuid,
  ) -> Result<Option<Conversation>, ServiceError> {
      let db_client = self.db_pool.get().await
          .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;
      info!("Getting conversation by id: {}", conversation_id);
      queries::get_conversation_by_id(&db_client, conversation_id).await
  }

  /// Lists conversations for a user with pagination support.
  /// 
  /// # Arguments
  /// * `user_id` - The ID of the user whose conversations to list
  /// * `include_inactive` - Whether to include inactive conversations
  /// * `page_size` - Number of conversations per page
  /// * `page` - Page number (0-based)
  /// 
  /// # Returns
  /// A tuple of (conversations, total_count)
  pub async fn list_conversations(
      &self,
      user_id: &str,
      include_inactive: bool,
      page_size: i64,
      page: i64,
  ) -> Result<(Vec<Conversation>, i64), ServiceError> {
      let db_client = self.db_pool.get().await
          .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

      let offset = page_size * page;
      let conversations = queries::list_user_conversations(
          &db_client,
          user_id,
          include_inactive,
          page_size,
          offset
      ).await?;

      let total_count = queries::get_conversation_count(
          &db_client,
          user_id,
          include_inactive
      ).await?;

      Ok((conversations, total_count))
  }
  /// Retrieves messages for a specific conversation with pagination support.
    /// 
    /// # Arguments
    /// * `conversation_id` - The UUID of the conversation
    /// * `before` - Optional cursor for pagination (timestamp)
    /// * `limit` - Maximum number of messages to return
    /// 
    /// # Returns
    /// Messages, pagination info, and total count
    #[instrument(skip(self))]
    pub async fn get_conversation_messages(
        &self,
        conversation_id: Uuid,
        offset: Option<i64>,
        limit: i64,
    ) -> Result<(Vec<StoredMessage>, bool), ServiceError> {
        let db_client = self.db_pool.get().await
            .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

        let limit = limit.min(100);
        let offset = offset.unwrap_or(0).max(0);
        
        let messages = queries::get_conversation_messages(
            &db_client,
            conversation_id,
            Some(offset),
            limit
        ).await?;

        let has_more = messages.len() == limit as usize;

        Ok((messages, has_more))
    }

    /// Lists conversations for a user with pagination and filtering.
    /// 
    /// # Arguments
    /// * `user_id` - The ID of the user whose conversations to list
    /// * `include_inactive` - Whether to include inactive conversations
    /// * `page_size` - Number of items per page
    /// * `page` - Page number (0-based)
    /// 
    /// # Returns
    /// Tuple of (conversations, total count, has more)
    #[instrument(skip(self))]
    pub async fn list_conversations_paginated(
        &self,
        user_id: &str,
        include_inactive: bool,
        page_size: i64,
        page: i64,
    ) -> Result<(Vec<Conversation>, i64, bool), ServiceError> {
        let page_size = page_size.min(100);
        let page = page.max(0);

        let (conversations, total_count) = self.list_conversations(
            user_id,
            include_inactive,
            page_size,
            page
        ).await?;

        let has_more = (page + 1) * page_size < total_count;

        Ok((conversations, total_count, has_more))
    }

    /// Validates a conversation access attempt
    async fn validate_conversation_access(
        &self,
        conversation_id: Uuid,
        user_id: Option<&str>
    ) -> Result<(), ServiceError> {
        if let Some(user_id) = user_id {
            let db_client = self.db_pool.get().await
                .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

            let conversation = queries::get_conversation_by_id(&db_client, conversation_id).await?;
            
            match conversation {
                Some(conv) if conv.user_id == user_id => Ok(()),
                Some(_) => Err(ServiceError::Unauthorized("Not authorized to access this conversation".to_string())),
                None => Err(ServiceError::NotFound("Conversation not found".to_string())),
            }
        } else {
            Ok(()) // No user ID check required
        }
    }
}