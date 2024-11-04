use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]  // Add these derives
pub struct ConversationState {
    pub platform: String,
    pub last_action: AgentAction,
    pub message_count: u32,
    pub active: bool,
    pub thread_id: Option<String>,
    pub last_activity: i64,
    pub retry_attempts: u32,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]  // This helps with database compatibility

pub enum AgentAction {
    Ignore,
    Continue,
    SwapToken,
}