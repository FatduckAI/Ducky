use std::sync::Arc;

use serde::Serialize;
use tracing::info;
use uuid::Uuid;

use tracing::{error, instrument};
use crate::{models::Message, ServiceError};
use crate::handler::MessageHandler;
use super::ApiResponse;
use warp::{Rejection, Reply};

#[derive(Debug, Serialize)]
pub struct MessageResponse {
    pub message_id: Uuid,
    pub response: String,
}

#[instrument(skip(handler, message), fields(message_id = %message.id))]
pub async fn handle_message(
    message: Message,
    handler: Arc<MessageHandler>,
) -> Result<impl Reply, Rejection> {
    info!("Received message: {:?}", message);
    
    let message_id = message.id;
    
    let response = tokio::task::spawn_blocking(move || {
        tokio::runtime::Handle::current().block_on(async {
            handler.process_message(&message).await
        })
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

    Ok(warp::reply::json(&ApiResponse::new(MessageResponse {
        message_id,
        response,
    })))
}