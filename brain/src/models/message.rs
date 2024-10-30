// src/models/message.rs
//! Message types and related functionality.
//! 
//! This module contains the core message types used throughout the service.
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::collections::HashMap;

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Message {
    /// Unique identifier for the message
    pub id: Uuid,
    /// ID of the user who sent the message
    pub user_id: String,
    /// Platform the message was sent from
    pub platform: String,
    /// Content of the message
    pub content: String,
    /// Unix timestamp when the message was sent
    pub timestamp: i64,
    /// Priority level for processing
    pub priority: String,
    /// Additional metadata about the message
    pub metadata: HashMap<String, String>,
    /// Number of processing attempts
    pub retry_count: u32,
    /// Optional thread ID for threaded conversations
    #[serde(default)]
    pub thread_id: Option<String>,
}
