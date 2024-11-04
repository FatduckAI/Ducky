use deadpool_postgres::{Config as PoolConfig, Pool, Runtime};
use tokio_postgres::NoTls;
use crate::{Config, Result, error::ServiceError};
use std::str::FromStr;

impl From<deadpool_postgres::CreatePoolError> for ServiceError {
    fn from(err: deadpool_postgres::CreatePoolError) -> Self {
        ServiceError::DatabasePoolError(err.to_string())
    }
}

pub async fn create_pool(config: &Config) -> Result<Pool> {
    // Validate URL by attempting to parse it
    tokio_postgres::Config::from_str(&config.database.url)
        .map_err(|e| ServiceError::DatabasePoolError(
            format!("Invalid database URL: {}", e)
        ))?;

    let mut pool_config = PoolConfig::new();
    
    // Set the database URL
    pool_config.url = Some(config.database.url.clone());
    
    // Set max connections from config

    // Create the pool
    let pool = pool_config.create_pool(Some(Runtime::Tokio1), NoTls)?;
    // Optional: Test the connection
    let _ = pool.get().await.map_err(|e| {
        ServiceError::DatabasePoolError(format!("Failed to connect to database: {}", e))
    })?;

    Ok(pool)
}

// Optional: Add a helper function to test pool connectivity
pub async fn test_connection(pool: &Pool) -> Result<()> {
let client = pool.get().await.map_err(|e| {
  ServiceError::DatabasePoolError(format!("Failed to get client from pool: {}", e))
})?;

client.execute("SELECT 1", &[]).await.map_err(|e| {
  ServiceError::DatabasePoolError(format!("Failed to execute test query: {}", e))
})?;

Ok(())
}