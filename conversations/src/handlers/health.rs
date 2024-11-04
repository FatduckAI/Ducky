use serde::Serialize;
use warp::{Rejection, Reply};
use tracing::instrument;
use super::ApiResponse;

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
}

#[instrument]
pub async fn handle_health() -> Result<impl Reply, Rejection> {
    Ok(warp::reply::json(&ApiResponse::new(HealthResponse {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })))
}