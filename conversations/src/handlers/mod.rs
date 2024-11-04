mod conversation;
mod health;
mod messages;

pub use conversation::{ConversationQuery, MessagesQuery};
pub use health::HealthResponse;
pub use messages::MessageResponse;

// Re-export the handlers for convenient access
pub use conversation::{
    handle_conversation_messages,
    handle_get_conversation,
    handle_list_conversations,
};
pub use health::handle_health;
pub use messages::handle_message;
use serde::Serialize;

// Common types used across handlers
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub data: T,
    pub timestamp: i64,
}

impl<T> ApiResponse<T> {
    pub fn new(data: T) -> Self {
        Self {
            success: true,
            data,
            timestamp: chrono::Utc::now().timestamp(),
        }
    }
}