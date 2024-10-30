use crate::{db::Conversation, handler::MessageHandler};
use super::ApiResponse;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use warp::{ Rejection, Reply};
use uuid::Uuid;
use tracing::{debug, instrument};
use serde_json::json;


#[derive(Debug, Deserialize)]
pub struct ConversationQuery {
    pub user_id: String,
    pub include_inactive: Option<bool>,
    pub page: Option<i64>,
    pub page_size: Option<i64>,
}


#[derive(Debug, Deserialize)]
pub struct MessagesQuery {
    pub offset: Option<i64>,
    pub limit: Option<i64>,
}

#[derive(Debug, Serialize)]
struct ConversationsResponse {
    success: bool,
    data: ConversationsData,
}

#[derive(Debug, Serialize)]
struct ConversationsData {
    conversations: Vec<Conversation>,
    total_count: i64,
    has_more: bool,
}


#[instrument(skip(handler))]
pub async fn handle_list_conversations(
    handler: Arc<MessageHandler>,
    query: ConversationQuery,
) -> Result<impl Reply, Rejection> {
    debug!("Handling list conversations request with query: {:?}", query);

    let (conversations, total_count) = handler
        .list_conversations_paginated(
            &query.user_id,
            query.include_inactive.unwrap_or(false),
            query.page_size.unwrap_or(20),
            query.page.unwrap_or(0),
        )
        .await
        .map_err(|e| {
            debug!("Error fetching conversations: {:?}", e);
            warp::reject::custom(e)
        })?;

    let page_size = query.page_size.unwrap_or(20);
    let current_page = query.page.unwrap_or(0);
    let has_more = total_count > (current_page + 1) * page_size;

    let response = ConversationsResponse {
        success: true,
        data: ConversationsData {
            conversations,
            total_count,
            has_more,
        },
    };

    debug!("Sending response: {:?}", response);

    Ok(warp::reply::with_status(
        warp::reply::json(&response),
        warp::http::StatusCode::OK,
    ))
}

#[instrument(skip(handler))]
pub async fn handle_get_conversation(
    conversation_id: Uuid,
    handler: Arc<MessageHandler>,
) -> Result<impl Reply, Rejection> {
    match handler.get_conversation(conversation_id).await {
        Ok(Some(conversation)) => Ok(warp::reply::json(&ApiResponse::new(conversation))),
        Ok(None) => Err(warp::reject::not_found()),
        Err(e) => Err(warp::reject::custom(e))
    }
}

#[instrument(skip(handler))]
pub async fn handle_conversation_messages(
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

    Ok(warp::reply::json(&ApiResponse::new(json!({
        "messages": messages,
        "has_more": has_more
    }))))
}