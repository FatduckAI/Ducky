use std::process;
use tracing::{error, info};
use message_handler::{Config, Result, Service, ServiceError};
use dotenv::dotenv;

#[tokio::main]
async fn main() {
    if let Err(e) = run().await {
        error!("Application error: {}", e);
        process::exit(1);
    }
}

async fn run() -> Result<()> {

    // Load .env file first
    dotenv().ok();

    // Try this instead:
    let filter = std::env::var("RUST_LOG")
        .unwrap_or_else(|_| "info,warp=info".to_string());

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .init();  

    info!(target: "app", "Starting message processing service"); // This will show up in the logs

    // Load configuration
    let config = Config::load().map_err(|e| {
        error!("Failed to load configuration: {}", e);
        ServiceError::Configuration(e.to_string())
    })?;

    // Create and start service (this will initialize DB connection)
    let service = Service::new(config).await?;

    // Log startup information
    info!(
        "Service started on {}:{}",
        service.config.server.host,
        service.config.server.port
    );

    // Run service with signal handling
    tokio::select! {
        result = service.run() => {
            if let Err(e) = result {
                error!("Service error: {}", e);
                return Err(e);
            }
        }
        _ = tokio::signal::ctrl_c() => {
            info!("Shutdown signal received, starting graceful shutdown");
        }
    }

    info!("Service shutdown complete");
    Ok(())
}

