//! HTTP server implementation for the message processing service.
//! 
//! This module provides the HTTP interface for the service, including:
//! - Message submission endpoint
//! - Health check endpoint
//! - Metrics endpoint
//! - CORS configuration
//! - Graceful shutdown handling

use std::sync::Arc;
use std::convert::Infallible;
use serde::Deserialize;
use uuid::Uuid;
use warp::{Filter, Rejection, Reply};
use serde_json::json;
use metrics::{counter, gauge};
use tracing::{debug, error, info, instrument};

use crate::config::Config;
use crate::handler::MessageHandler;
use crate::error::ServiceError;
use crate::models::Message;

/// HTTP server for the message processing service
#[derive(Debug)]
pub struct Server {
    /// Message handler instance
    handler: Arc<MessageHandler>,
    /// Server configuration
    config: Config,
}

impl Server {
  pub fn new(handler: Arc<MessageHandler>, config: &Config) -> Self {
      Self {
          handler,
          config: config.clone(),
      }
  }

  pub async fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
      let routes = self.routes();
      
      info!(
          "Starting server on {}:{}",
          self.config.server.host, self.config.server.port
      );

      let addr = format!(
          "{}:{}", 
          self.config.server.host, 
          self.config.server.port
      ).parse::<std::net::SocketAddr>()
        .map_err(|e| ServiceError::ServerError(e.to_string()))?;

      warp::serve(routes)
          .run(addr)
          .await;
          
      Ok(())
  }

  fn routes(&self) -> impl Filter<Extract = impl Reply, Error = Rejection> + Clone {
    let health_route = warp::path("health")
        .and(warp::get())
        .and_then(health_handler);

    let message_route = warp::path("message")
        .and(warp::post())
        .and(warp::body::json())
        .and(with_handler(self.handler.clone()))
        .and_then(handle_message);

    // Debug logging filter
    let log = warp::log::custom(|info| {
        debug!(
            "Received request: {} {}",
            info.method(),
            info.path()
        );
    });

    // List conversations route
    let list_conversations = warp::path("conversations")
        .and(warp::get())
        .and(with_handler(self.handler.clone()))
        .and(warp::query::<ConversationsQuery>())
        .and_then(handle_list_conversations);

      
    // Conversation messages route with exact path matching
    let get_conversation_messages = warp::path!("conversation" / Uuid / "messages")
        .and(warp::get())
        .and(with_handler(self.handler.clone()))
        .and(warp::query::<MessagesQuery>())
        .and_then(|id, handler, query| {
            debug!("Processing conversation messages request: id={}, query={:?}", id, query);
            handle_conversation_messages(id, handler, query)
        });


    // Get single conversation route
    let get_conversation = warp::path!("conversation" / Uuid)
        .and(warp::get())
        .and(with_handler(self.handler.clone()))
        .and_then(handle_get_conversation);

    info!("Setting up routes");

    let cors = warp::cors()
        .allow_any_origin()
        .allow_methods(vec!["POST", "GET", "OPTIONS"])
        .allow_headers(vec!["Content-Type", "Authorization"]);

    // Print all available routes
    debug!("Available routes:");
    debug!(" - GET /health");
    debug!(" - POST /message");
    debug!(" - GET /conversations");
    debug!(" - GET /conversation/:id");
    debug!(" - GET /conversation/:id/messages");

    // Combine all routes with logging
    health_route
        .or(message_route)
        .or(list_conversations)
        .or(get_conversation)
        .or(get_conversation_messages)
        .with(cors)
        .with(log)
        .recover(handle_rejection)
        .boxed()
  }

  async fn shutdown_signal(&self) {
      tokio::signal::ctrl_c()
          .await
          .expect("Failed to install CTRL+C signal handler");
      info!("Shutdown signal received, starting graceful shutdown");
  }
}

// Add query parameter structs
#[derive(Debug, Deserialize)]
struct ConversationsQuery {
    user_id: String,
    include_inactive: Option<bool>,
    page: Option<i64>,
    page_size: Option<i64>,
}

#[derive(Debug, Deserialize)]
struct MessagesQuery {
    offset: Option<i64>,
    limit: Option<i64>,
}

/// Handler for the message submission endpoint
#[instrument(skip(handler))]
async fn handle_message(
  message: Message,
  handler: Arc<MessageHandler>,
) -> Result<impl Reply, Rejection> {
  println!("Received message");
  info!("Received message: {:?}", message);
  counter!("messages_received_total").increment(1);
  gauge!("message_queue_size").increment(1.0);

  info!(
      "Received message from user {} on platform {}",
      message.user_id, message.platform
  );

  match handler.process_message(&message).await {
      Ok(response) => {
          counter!("messages_processed_success").increment(1);
          gauge!("message_queue_size").decrement(1.0);
          
          Ok(warp::reply::json(&json!({
              "success": true,
              "response": response,
              "message_id": message.id,
              "timestamp": chrono::Utc::now().timestamp()
          })))
      }
      Err(e) => {
          error!("Error processing message: {:?}", e);
          counter!("messages_processed_error").increment(1);
          gauge!("message_queue_size").decrement(1.0);
          
          Err(warp::reject::custom(e))
      }
  }
}

async fn health_handler() -> Result<impl Reply, Rejection> {
  Ok(warp::reply::json(&json!({
      "status": "healthy",
      "timestamp": chrono::Utc::now().timestamp(),
      "version": env!("CARGO_PKG_VERSION")
  })))
}


/// Helper function to include handler in route filters
fn with_handler(
    handler: Arc<MessageHandler>,
) -> impl Filter<Extract = (Arc<MessageHandler>,), Error = Infallible> + Clone {
    warp::any().map(move || handler.clone())
}

/// Error handler for rejected requests
async fn handle_rejection(err: Rejection) -> Result<impl Reply, Infallible> {

  error!("Rejection occurred: {:?}", err);

  let (code, message) = if err.is_not_found() {
      (warp::http::StatusCode::NOT_FOUND, "")
  } else if let Some(_) = err.find::<warp::reject::MethodNotAllowed>() {
      (warp::http::StatusCode::METHOD_NOT_ALLOWED, "Method Not Allowed")
  } else if let Some(e) = err.find::<ServiceError>() {
      match e {
          ServiceError::RateLimitExceeded(_) => (
              warp::http::StatusCode::TOO_MANY_REQUESTS,
              "Rate limit exceeded"
          ),
          ServiceError::InvalidMessage(_) => (
              warp::http::StatusCode::BAD_REQUEST,
              "Invalid message format"
          ),
          _ => (
              warp::http::StatusCode::INTERNAL_SERVER_ERROR,
              "Internal server error"
          ),
      }
  } else {
      (
          warp::http::StatusCode::INTERNAL_SERVER_ERROR,
          "Internal Server Error",
      )
  };

  let json = warp::reply::json(&json!({
      "success": false,
      "error": message,
      "timestamp": chrono::Utc::now().timestamp()
  }));

  Ok(warp::reply::with_status(json, code))
}
#[instrument(skip(handler))]
async fn handle_list_conversations(
    handler: Arc<MessageHandler>,
    query: ConversationsQuery,
) -> Result<impl Reply, Rejection> {
    let (conversations, total_count, has_more) = handler
        .list_conversations_paginated(
            &query.user_id,
            query.include_inactive.unwrap_or(false),
            query.page_size.unwrap_or(20),
            query.page.unwrap_or(0),
        )
        .await
        .map_err(|e| warp::reject::custom(e))?;

    Ok(warp::reply::json(&json!({
        "conversations": conversations,
        "total_count": total_count,
        "has_more": has_more
    })))
}

#[instrument(skip(handler))]
async fn handle_get_conversation(
    conversation_id: Uuid,
    handler: Arc<MessageHandler>,
) -> Result<impl Reply, Rejection> {
    match handler.get_conversation(conversation_id).await {
        Ok(Some(conversation)) => Ok(warp::reply::json(&conversation)),
        Ok(None) => Err(warp::reject::not_found()),
        Err(e) => Err(warp::reject::custom(e))
    }
}

#[instrument(skip(handler))]
async fn handle_conversation_messages(
    conversation_id: Uuid,
    handler: Arc<MessageHandler>,
    query: MessagesQuery,
) -> Result<impl Reply, Rejection> {
    let (messages, has_more) = handler
        .get_conversation_messages(
            conversation_id,
            query.offset,
            query.limit.unwrap_or(50),
        )
        .await
        .map_err(|e| warp::reject::custom(e))?;

    Ok(warp::reply::json(&json!({
        "messages": messages,
        "has_more": has_more
    })))
}