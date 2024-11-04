use thiserror::Error;

#[derive(Error, Debug)]
pub enum ServiceError {
    #[error("Failed to process message: {0}")]
    ProcessingError(String),
    
    #[error("User not found: {0}")]
    UserNotFound(String),
    
    #[error("Channel error: {0}")]
    ChannelError(String),
    
    #[error("Queue full: {0}")]
    QueueFull(String),
    
    #[error("Database error: {0}")]
    DatabaseError(String),
    
    #[error("Rate limit exceeded: {0}")]
    RateLimitExceeded(String),
    
    #[error("Invalid message format: {0}")]
    InvalidMessage(String),
    
    #[error("Thread pool error: {0}")]
    ThreadPoolError(String),

    #[error("Database pool error: {0}")]
    DatabasePoolError(String),

    #[error("Config error: {0}")]
    ConfigError(String),

    #[error("Server error: {0}")]
    ServerError(String),

    #[error("Configuration error: {0}")]
    Configuration(String),

    #[error("Internal error: {0}")]
    Internal(String),

    #[error("Unauthorized: {0}")]
    Unauthorized(String),

    #[error("Not found: {0}")]
    NotFound(String),
}

impl warp::reject::Reject for ServiceError {}

impl From<config::ConfigError> for ServiceError {
    fn from(error: config::ConfigError) -> Self {
        ServiceError::Configuration(error.to_string())
    }
}