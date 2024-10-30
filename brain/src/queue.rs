use std::collections::VecDeque;
use tracing::{debug, warn};

use crate::models::Message;
use crate::error::ServiceError;

#[derive(Debug)]
pub struct MessageQueue {
    queue: VecDeque<Message>,
    max_size: usize,
}

impl MessageQueue {
    pub fn new(max_size: usize) -> Self {
        Self {
            queue: VecDeque::with_capacity(max_size),
            max_size,
        }
    }

    pub async fn push(&mut self, message: Message) -> Result<(), ServiceError> {
        if self.queue.len() >= self.max_size {
            warn!("Queue is full: {}/{}", self.queue.len(), self.max_size);
            return Err(ServiceError::QueueFull(
                format!("Message queue is at capacity: {}/{}", self.queue.len(), self.max_size)
            ));
        }

        debug!("Pushing message: {}", message.id);
        self.queue.push_back(message);
        Ok(())
    }

    pub async fn pop(&mut self) -> Option<Message> {
        let message = self.queue.pop_front();
        if let Some(ref msg) = message {
            debug!("Popped message: {}", msg.id);
        }
        message
    }

    pub fn len(&self) -> usize {
        self.queue.len()
    }

    pub fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }

    pub fn max_size(&self) -> usize {
        self.max_size
    }

    pub fn set_max_size(&mut self, size: usize) {
        self.max_size = size;
    }

    pub fn clear(&mut self) {
        self.queue.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;
    use std::collections::HashMap;

    fn create_test_message() -> Message {
        Message {
            id: Uuid::new_v4(),
            user_id: "test_user".to_string(),
            platform: "discord".to_string(),
            content: "test message".to_string(),
            timestamp: chrono::Utc::now().timestamp(),
            priority: "normal".to_string(),
            metadata: HashMap::new(),
            retry_count: 0,
            thread_id: None,
        }
    }

    #[tokio::test]
    async fn test_queue_fifo_ordering() {
        let mut queue = MessageQueue::new(10);

        // Push multiple messages
        let msg1 = create_test_message();
        let msg2 = create_test_message();
        let msg3 = create_test_message();

        let id1 = msg1.id;
        let id2 = msg2.id;
        let id3 = msg3.id;

        queue.push(msg1).await.unwrap();
        queue.push(msg2).await.unwrap();
        queue.push(msg3).await.unwrap();

        // Verify FIFO ordering
        assert_eq!(queue.pop().await.unwrap().id, id1);
        assert_eq!(queue.pop().await.unwrap().id, id2);
        assert_eq!(queue.pop().await.unwrap().id, id3);
    }

    #[tokio::test]
    async fn test_queue_capacity() {
        let mut queue = MessageQueue::new(2);

        // Try to push more messages than capacity
        assert!(queue.push(create_test_message()).await.is_ok());
        assert!(queue.push(create_test_message()).await.is_ok());
        assert!(queue.push(create_test_message()).await.is_err());
    }

    #[tokio::test]
    async fn test_empty_queue() {
        let mut queue = MessageQueue::new(5);
        assert!(queue.pop().await.is_none());
        assert!(queue.is_empty());
        
        let msg = create_test_message();
        queue.push(msg).await.unwrap();
        assert!(!queue.is_empty());
        
        assert!(queue.pop().await.is_some());
        assert!(queue.is_empty());
    }

    #[tokio::test]
    async fn test_clear_queue() {
        let mut queue = MessageQueue::new(5);
        
        queue.push(create_test_message()).await.unwrap();
        queue.push(create_test_message()).await.unwrap();
        assert_eq!(queue.len(), 2);

        queue.clear();
        assert_eq!(queue.len(), 0);
        assert!(queue.is_empty());
    }
}