use std::env;

use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub queue: QueueConfig,
    pub metrics: MetricsConfig,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub thread_pool_size: usize,
}

#[derive(Debug, Deserialize, Clone)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct QueueConfig {
    pub size: usize,
    pub retry_attempts: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct MetricsConfig {
    pub port: u16,
}

impl Config {
  pub fn load() -> Result<Self, config::ConfigError> {
      Ok(Self {
          server: ServerConfig {
              host: env::var("SERVER_HOST").unwrap_or_else(|_| "127.0.0.1".to_string()),
              port: env::var("SERVER_PORT").unwrap_or_else(|_| "3030".to_string())
                  .parse()
                  .unwrap_or(3030),
              thread_pool_size: env::var("SERVER_THREAD_POOL_SIZE")
                  .unwrap_or_else(|_| "4".to_string())
                  .parse()
                  .unwrap_or(4),
          },
          database: DatabaseConfig {
              url: env::var("DATABASE_URL").expect("DATABASE_URL must be set"),
              max_connections: env::var("DATABASE_MAX_CONNECTIONS")
                  .unwrap_or_else(|_| "5".to_string())
                  .parse()
                  .unwrap_or(5),
          },
          queue: QueueConfig {
              size: env::var("QUEUE_SIZE")
                  .unwrap_or_else(|_| "10000".to_string())
                  .parse()
                  .unwrap_or(10000),
              retry_attempts: env::var("QUEUE_RETRY_ATTEMPTS")
                  .unwrap_or_else(|_| "3".to_string())
                  .parse()
                  .unwrap_or(3),
          },
          metrics: MetricsConfig {
              port: env::var("METRICS_PORT")
                  .unwrap_or_else(|_| "9090".to_string())
                  .parse()
                  .unwrap_or(9090),
          },
      })
  }
}