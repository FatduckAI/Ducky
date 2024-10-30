//! # Message Processing Service
//! 
//! A scalable service for processing messages with Claude AI integration.
//! 
//! ## Features
//! 
//! - Conversation state management with 24-hour sessions
//! - Automatic Claude AI integration for responses
//! - Rate limiting and backpressure handling
//! - Message queuing
//! - Database persistence with PostgreSQL
//! 
//! ## Quick Start
//! 
//! ```rust,no_run
//! use message_handler::{Config, Service};
//! 
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Load configuration
//!     let config = Config::load()?;
//!     
//!     // Create and start service
//!     let service = Service::new(config).await?;
//!     service.run().await?;
//!     
//!     Ok(())
//! }
//! ```

use std::sync::Arc;
use tokio;
use deadpool_postgres;
use tracing::{info, error};

// Public modules
pub mod config;
pub mod error;
pub mod handler;
pub mod server;
pub mod models;
pub mod db;
pub mod services;

// Internal modules
mod queue;

// Re-export commonly used types
pub use crate::config::Config;
pub use crate::handler::MessageHandler;
pub use crate::server::Server;
pub use crate::error::ServiceError;

// Type aliases for common types
pub type Result<T> = std::result::Result<T, ServiceError>;
pub type DbPool = deadpool_postgres::Pool;
pub type DbClient = deadpool_postgres::Client;

/// Module configuration constants
pub mod constants {
    /// Default server port
    pub const DEFAULT_PORT: u16 = 3030;
    
    /// Default message queue size
    pub const DEFAULT_QUEUE_SIZE: usize = 10000;
    
    /// Default rate limit window in seconds
    pub const DEFAULT_RATE_LIMIT_WINDOW: i64 = 60;
    
    /// Default maximum messages per rate limit window
    pub const DEFAULT_RATE_LIMIT_MAX: u32 = 100;
    
    /// Conversation timeout in seconds (24 hours)
    pub const CONVERSATION_TIMEOUT: i64 = 24 * 60 * 60;
}

/// Represents a complete service instance
pub struct Service {
    pub server: Server,
    pub config: Config,
    handler: Arc<MessageHandler>,
}

impl Service {
    /// Create a new service instance with custom configuration
    pub async fn new(config: Config) -> Result<Self> {
        // Initialize metrics

        info!("Initializing database connection...");
        let db_pool = db::create_pool(&config).await?;
        
        // Test the connection
        db::pool::test_connection(&db_pool).await.map_err(|e| {
            error!("Database connection test failed: {}", e);
            e
        })?;
        info!("Database connection established successfully");
        // Create handler
        let handler = MessageHandler::new(
            config.queue.size,
            db_pool,
        )?;

        let handler = Arc::new(handler);
        
        // Spawn processing task
        let handler_clone = Arc::clone(&handler);
        tokio::spawn(async move {
            handler_clone.start_processing().await;
        });

        // Create server
        let server = Server::new(handler.clone(), &config);

        Ok(Self { server, config, handler })
    }

    /// Run the service
    pub async fn run(self) -> Result<()> {
        self.server.run().await.map_err(|e| {
            ServiceError::ServerError(format!("Server error: {}", e))
        })?;
        Ok(())
    }

    /// Get service statistics
    pub fn get_stats(&self) -> handler::HandlerStats {
        self.handler.get_stats()
    }
}

// Version information
pub mod version {
    /// Get the current version of the service
    pub fn current() -> &'static str {
        env!("CARGO_PKG_VERSION")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::Message;
    use uuid::Uuid;
    use std::collections::HashMap;
    use chrono::Utc;

    async fn create_test_message() -> Message {
        Message {
            id: Uuid::new_v4(),
            user_id: "test_user".to_string(),
            platform: "discord".to_string(),
            priority: "normal".to_string(),
            content: "Test message".to_string(),
            timestamp: Utc::now().timestamp(),
            metadata: HashMap::new(),
            retry_count: 0,
            thread_id: None,
        }
    }

    #[tokio::test]
    async fn test_service_initialization() {
        let config = Config::load().expect("Failed to load config");
        let service = Service::new(config).await.expect("Failed to create service");
        assert_eq!(service.config.server.port, constants::DEFAULT_PORT);
    }

    #[tokio::test]
    async fn test_message_processing() {
        let config = Config::load().expect("Failed to load config");
        let service = Service::new(config).await.expect("Failed to create service");
        
        let message = create_test_message().await;
        let result = service.handler.process_message(&message).await;
        assert!(result.is_ok(), "Message processing failed: {:?}", result);
    }
}