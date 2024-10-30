use deadpool_postgres::Client;
use uuid::Uuid;
use tracing::instrument;
use crate::error::ServiceError;
use super::{models::{Conversation, PgTimestamp, StoredMessage}, ConversationStats};



#[instrument(skip(client))]
pub async fn find_active_conversation(
    client: &Client,
    user_id: &str,
) -> Result<Option<Conversation>, ServiceError> {
    let query = "
        SELECT * FROM conversations 
        WHERE user_id = $1 
        AND is_active = true 
        AND started_at > NOW() - INTERVAL '24 hours'
        ORDER BY created_at DESC 
        LIMIT 1
    ";

    let row = client
        .query_opt(query, &[&user_id])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(row.map(Conversation::from))
}

#[instrument(skip(client))]
pub async fn create_conversation(
    client: &Client,
    user_id: &str,
    platform: String,
    metadata: serde_json::Value,
) -> Result<Conversation, ServiceError> {
  tracing::info!("Creating conversation - user_id: {}, platform: {:?}", user_id, platform);

    let query = "
        INSERT INTO conversations (
            id, user_id, platform, started_at, is_active, metadata, created_at
        )
        VALUES ($1, $2, $3, $4, true, $5, $4)
        RETURNING *
    ";

    let id = Uuid::new_v4();
    let now = PgTimestamp::now();
    
    let row = client
        .query_one(
            query, 
            &[&id, &user_id, &platform, &now, &metadata]
        )
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(Conversation::from(row))
}

#[instrument(skip(client))]
pub async fn save_message(
    client: &Client,
    conversation_id: Uuid,
    user_id: &str,
    content: &str,
    thread_id: Option<&str>,
    platform: String,
    metadata: serde_json::Value,
) -> Result<StoredMessage, ServiceError> {
    let query = "
        INSERT INTO messages (
            id, conversation_id, user_id, content, 
            platform, priority, thread_id, metadata, created_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    ";

    let id = Uuid::new_v4();
    let now = PgTimestamp::now();
    let platform = "discord"; // Or get this from parameters
    let priority = "normal"; // Or get this from parameters

    let row = client
        .query_one(
            query,
            &[
                &id, &conversation_id, &user_id, &content,
                &platform, &priority, &thread_id, &metadata, &now
            ],
        )
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(StoredMessage::from(row))
}

#[instrument(skip(client))]
pub async fn close_conversation(
    client: &Client,
    conversation_id: Uuid,
) -> Result<Conversation, ServiceError> {
    let query = "
        UPDATE conversations
        SET is_active = false,
            ended_at = $2
        WHERE id = $1
        RETURNING *
    ";

    let now = PgTimestamp::now();
    
    let row = client
        .query_one(query, &[&conversation_id, &now])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(Conversation::from(row))
}

#[instrument(skip(client))]
pub async fn get_conversation_history(
    client: &Client,
    user_id: &str,
    limit: i64,
) -> Result<Vec<StoredMessage>, ServiceError> {
    let query = "
        SELECT m.* FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = $1
        ORDER BY m.created_at DESC
        LIMIT $2
    ";

    let rows = client
        .query(query, &[&user_id, &limit])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(rows.into_iter().map(StoredMessage::from).collect())
}

// Additional helper function to get conversation statistics
#[instrument(skip(client))]
pub async fn get_conversation_stats(
    client: &Client,
    user_id: &str,
) -> Result<ConversationStats, ServiceError> {
    let query = "
        WITH stats AS (
            SELECT 
                COUNT(DISTINCT c.id) FILTER (WHERE c.is_active) as active_conversations,
                COUNT(m.id) as total_messages,
                COUNT(m.id) FILTER (WHERE m.created_at > NOW() - INTERVAL '1 hour') as messages_last_hour,
                AVG(EXTRACT(EPOCH FROM (
                    LEAD(m.created_at) OVER (PARTITION BY m.conversation_id ORDER BY m.created_at) - m.created_at
                )) * 1000) as avg_response_time_ms
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = $1
        )
        SELECT * FROM stats
    ";

    let row = client
        .query_one(query, &[&user_id])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(ConversationStats {
        active_conversations: row.get("active_conversations"),
        total_messages: row.get("total_messages"),
        messages_last_hour: row.get("messages_last_hour"),
        avg_response_time_ms: row.get("avg_response_time_ms"),
    })
}

pub async fn get_recent_messages(
    client: &deadpool_postgres::Client,
    user_id: &str,
    limit: i64
) -> Result<Vec<StoredMessage>, ServiceError> {
    let rows = client
        .query(
            "SELECT * FROM messages 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2",
            &[&user_id, &limit]
        )
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(rows.into_iter().map(StoredMessage::from).collect())
}

pub async fn mark_message_failed(client: &Client, message_id: Uuid) -> Result<(), ServiceError> {
    client.execute(
        "UPDATE messages SET status = 'failed', updated_at = NOW() WHERE id = $1",
        &[&message_id]
    ).await
    .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(())
}

pub async fn save_response_metrics(
    client: &deadpool_postgres::Client,
    message_id: Uuid,
    response_length: i32,
    processing_time: i64,
) -> Result<(), crate::error::ServiceError> {
    client.execute(
        "UPDATE messages SET response_length = $1, processing_time = $2 WHERE id = $3",
        &[&response_length, &processing_time, &message_id],
    ).await.map_err(|e| crate::error::ServiceError::DatabaseError(e.to_string()))?;

    Ok(())
}

pub async fn close_expired_conversations(client: &deadpool_postgres::Client) -> Result<i64, ServiceError> {
    let query = "
        UPDATE conversations 
        SET is_active = false, 
            ended_at = NOW() 
        WHERE is_active = true 
        AND created_at < NOW() - INTERVAL '24 hours'
        RETURNING id";
    
    let rows = client.execute(query, &[]).await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;
    Ok(rows as i64)
}

#[instrument(skip(client))]
pub async fn get_conversation_by_id(
    client: &Client,
    conversation_id: Uuid,
) -> Result<Option<Conversation>, ServiceError> {
    let query = "
        SELECT * FROM conversations 
        WHERE id = $1
    ";

    let row = client
        .query_opt(query, &[&conversation_id])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(row.map(Conversation::from))
}

#[instrument(skip(client))]
pub async fn list_user_conversations(
    client: &Client,
    user_id: &str,
    include_inactive: bool,
    limit: i64,
    offset: i64,
) -> Result<Vec<Conversation>, ServiceError> {
    let query = if include_inactive {
        "
            SELECT * FROM conversations 
            WHERE user_id = $1
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
        "
    } else {
        "
            SELECT * FROM conversations 
            WHERE user_id = $1 
            AND is_active = true
            ORDER BY created_at DESC 
            LIMIT $2 OFFSET $3
        "
    };

    let rows = client
        .query(query, &[&user_id, &limit, &offset])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(rows.into_iter().map(Conversation::from).collect())
}

#[instrument(skip(client))]
pub async fn get_conversation_count(
    client: &Client,
    user_id: &str,
    include_inactive: bool,
) -> Result<i64, ServiceError> {
    let query = if include_inactive {
        "SELECT COUNT(*) FROM conversations WHERE user_id = $1"
    } else {
        "SELECT COUNT(*) FROM conversations WHERE user_id = $1 AND is_active = true"
    };

    let count: i64 = client
        .query_one(query, &[&user_id])
        .await
        .map_err(|e| ServiceError::DatabaseError(e.to_string()))?
        .get(0);

    Ok(count)
}

/// Retrieves messages for a specific conversation with pagination support
/// 
/// # Arguments
/// * `client` - Database client
/// * `conversation_id` - The UUID of the conversation to get messages for
/// * `offset` - Optional offset for pagination
/// * `limit` - Maximum number of messages to return
#[instrument(skip(client))]
pub async fn get_conversation_messages(
    client: &Client,
    conversation_id: Uuid,
    offset: Option<i64>,
    limit: i64,
) -> Result<Vec<StoredMessage>, ServiceError> {
    let query = if offset.is_some() {
        "
            SELECT m.* FROM messages m
            WHERE m.conversation_id = $1 
            ORDER BY m.created_at DESC 
            OFFSET $2
            LIMIT $3
        "
    } else {
        "
            SELECT m.* FROM messages m
            WHERE m.conversation_id = $1 
            ORDER BY m.created_at DESC 
            LIMIT $2
        "
    };

    let rows = if let Some(offset_val) = offset {
        client
            .query(query, &[&conversation_id, &offset_val, &limit])
            .await
    } else {
        client
            .query(query, &[&conversation_id, &limit])
            .await
    }
    .map_err(|e| ServiceError::DatabaseError(e.to_string()))?;

    Ok(rows.into_iter().map(StoredMessage::from).collect())
}