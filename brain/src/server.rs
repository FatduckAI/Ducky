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
use uuid::Uuid;
use crate::config::Config;
use warp::{Filter, Rejection, Reply};
use serde_json::json;
use tracing::{debug, info};

use crate::error::ServiceError;
use crate::handlers::{
  handle_list_conversations,
  handle_get_conversation,
  handle_conversation_messages,
};
use crate::MessageHandler;
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
        .and_then(MessageHandler::handle_message);

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
        .and(warp::query())
        .and_then(handle_list_conversations);

      
    // Conversation messages route with exact path matching
    let get_conversation_messages = warp::path!("conversations" / Uuid / "messages")
        .and(warp::get())
        .and(with_handler(self.handler.clone()))
        .and(warp::query())
        .and_then(|id, handler, query| {
            debug!("Processing conversation messages request: id={}, query={:?}", id, query);
            handle_conversation_messages(id, handler, query)
        });


    // Get single conversation route
    let get_conversation = warp::path!("conversations" / Uuid)
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
        .recover(MessageHandler::handle_rejection)
        .boxed()
  }

  async fn shutdown_signal(&self) {
      tokio::signal::ctrl_c()
          .await
          .expect("Failed to install CTRL+C signal handler");
      info!("Shutdown signal received, starting graceful shutdown");
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

