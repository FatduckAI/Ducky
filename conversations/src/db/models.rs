use std::error::Error;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio_postgres::{types::{to_sql_checked, FromSql, IsNull, ToSql, Type}, Row};
use uuid::Uuid;
use bytes::BytesMut;


impl ToSql for PgTimestamp {
  fn to_sql(&self, ty: &Type, out: &mut BytesMut) -> Result<IsNull, Box<dyn Error + Sync + Send>> {
      // Convert to microseconds since PostgreSQL epoch (2000-01-01)
      let postgres_epoch = DateTime::from_timestamp(946684800, 0).unwrap().naive_utc();
      let duration = self.0.naive_utc() - postgres_epoch;
      
      let microseconds = duration.num_microseconds()
            .ok_or_else(|| {
                // Use a simple error message since we can't construct internal error types
                Box::new(std::io::Error::new(
                    std::io::ErrorKind::InvalidData,
                    "timestamp overflow - value outside supported range"
                ))
            })?;
        
  microseconds.to_sql(ty, out)
  }

  fn accepts(ty: &Type) -> bool {
      matches!(ty.name(), "timestamp" | "timestamptz")
  }

  to_sql_checked!();
}

// Custom timestamp wrapper to handle PostgreSQL timestamp conversion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PgTimestamp(pub DateTime<Utc>);
impl<'a> FromSql<'a> for PgTimestamp {
  fn from_sql(
      _ty: &Type,
      raw: &'a [u8],
  ) -> Result<PgTimestamp, Box<dyn Error + Sync + Send>> {
      let naive_datetime = match _ty.name() {
          "timestamp" | "timestamptz" => {
              let val = i64::from_sql(_ty, raw)?;
              // Convert PostgreSQL microseconds since 2000-01-01 to NaiveDateTime
              let postgres_epoch = DateTime::from_timestamp(946684800, 0).unwrap().naive_utc();
              let microseconds = val / 1_000_000;
              let nanos = ((val % 1_000_000) * 1000) as u32;
              postgres_epoch + chrono::Duration::seconds(microseconds)
                  + chrono::Duration::nanoseconds(nanos as i64)
          },
          _ => return Err("unexpected type for timestamp".into()),
      };
      
      Ok(PgTimestamp(DateTime::from_naive_utc_and_offset(naive_datetime, Utc)))
  }

  fn accepts(ty: &Type) -> bool {
      matches!(ty.name(), "timestamp" | "timestamptz")
  }
}

impl From<DateTime<Utc>> for PgTimestamp {
    fn from(dt: DateTime<Utc>) -> Self {
        PgTimestamp(dt)
    }
}

impl PgTimestamp {
    pub fn now() -> Self {
        Self(Utc::now())
    }
}

impl Default for PgTimestamp {
    fn default() -> Self {
        Self::now()
    }
}


#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    pub id: Uuid,
    pub user_id: String,
    pub platform: String,
    pub started_at: DateTime<Utc>,
    pub ended_at: Option<DateTime<Utc>>,
    pub is_active: bool,
    pub metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

impl From<Row> for Conversation {
    fn from(row: Row) -> Self {
        Self {
            id: row.get("id"),
            user_id: row.get("user_id"),
            platform: row.get("platform"),
            started_at: row.get::<_, PgTimestamp>("started_at").0,
            ended_at: row.get::<_, Option<PgTimestamp>>("ended_at").map(|t| t.0),
            is_active: row.get("is_active"),
            metadata: row.get("metadata"),
            created_at: row.get::<_, PgTimestamp>("created_at").0,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StoredMessage {
    pub id: Uuid,
    pub conversation_id: Uuid,
    pub user_id: String,
    pub content: String,
    pub thread_id: Option<String>,
    pub metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
}

impl From<Row> for StoredMessage {
    fn from(row: Row) -> Self {
        Self {
            id: row.get("id"),
            conversation_id: row.get("conversation_id"),
            user_id: row.get("user_id"),
            content: row.get("content"),
            thread_id: row.get("thread_id"),
            metadata: row.get("metadata"),
            created_at: row.get::<_, PgTimestamp>("created_at").0,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct ConversationStats {
    pub active_conversations: i64,
    pub total_messages: i64,
    pub messages_last_hour: i64,
    pub avg_response_time_ms: Option<f64>,
}
