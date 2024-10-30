// mod.rs
mod message;
mod conversation;

pub use message::Message;
pub use conversation::{ConversationState, AgentAction};

// If you need to add any module-level constants or utilities
pub const MAX_RETRY_ATTEMPTS: u32 = 3;
pub const DEFAULT_TIMEOUT: i64 = 300; // 5 minutes in seconds

impl Default for ConversationState {
    fn default() -> Self {
        Self {
            platform: "discord".to_string(), // Or whatever your default platform should be
            last_action: AgentAction::Ignore,
            message_count: 0,
            active: true,
            thread_id: None,
            last_activity: 0,
            retry_attempts: 0,
        }
    }
}

impl ConversationState {
    pub fn new(platform: String) -> Self {
        Self {
            platform,
            ..Default::default()
        }
    }

    pub fn increment_message_count(&mut self) {
        self.message_count += 1;
    }

    pub fn set_thread_id(&mut self, thread_id: String) {
        self.thread_id = Some(thread_id);
    }

    pub fn update_last_activity(&mut self, timestamp: i64) {
        self.last_activity = timestamp;
    }

    pub fn increment_retry(&mut self) -> u32 {
        self.retry_attempts += 1;
        self.retry_attempts
    }

    pub fn is_expired(&self, current_time: i64) -> bool {
        current_time - self.last_activity > DEFAULT_TIMEOUT
    }
}

impl AgentAction {
    pub fn should_continue(&self) -> bool {
        matches!(self, AgentAction::Continue)
    }

    pub fn should_swap_token(&self) -> bool {
        matches!(self, AgentAction::SwapToken)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_conversation_state_default() {
        let state = ConversationState::default();
        assert!(state.active);
        assert_eq!(state.message_count, 0);
        assert_eq!(state.retry_attempts, 0);
    }

    #[test]
    fn test_conversation_state_new() {
        let state = ConversationState::new("discord".to_string());
        assert_eq!(state.platform, "discord".to_string());
        assert!(state.active);
    }

    #[test]
    fn test_agent_action_methods() {
        assert!(AgentAction::Continue.should_continue());
        assert!(!AgentAction::Ignore.should_continue());
        assert!(AgentAction::SwapToken.should_swap_token());
        assert!(!AgentAction::Continue.should_swap_token());
    }
}