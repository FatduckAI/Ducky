# Message Processing Service

A scalable message processing service built with Rust that handles conversations across multiple platforms and integrates with Claude AI for responses.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Development](#development)

## Features

- Multi-platform message handling (Twitter, Discord, Telegram)
- Conversation state management with 24-hour sessions
- Automatic Claude AI integration for responses
- Rate limiting and backpressure handling
- Message queuing and prioritization
- Comprehensive error handling and recovery
- Metrics and monitoring
- Database persistence with PostgreSQL

## Architecture

The service is built using a modular architecture:

```
src/
├── main.rs              # Application entry point
├── config.rs            # Configuration management
├── error.rs             # Error types and handling
├── handler.rs           # Message processing logic
├── server.rs            # HTTP server implementation
├── models/              # Domain models
│   ├── message.rs       # Message types
│   ├── conversation.rs  # Conversation state
│   └── platform.rs      # Platform enums
├── db/                  # Database operations
│   ├── models.rs        # Database models
│   └── queries.rs       # SQL queries
├── services/            # External services
│   └── claude.rs        # Claude AI integration
└── queue.rs             # Message queue implementation
```

## Setup

1. Prerequisites:

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install PostgreSQL
sudo apt-get install postgresql
```

2. Environment Configuration:

```bash
# Create .env file
cat << EOF > .env
DATABASE_URL=postgresql://user:password@localhost/dbname
ANTHROPIC_API_KEY=your_api_key
PORT=3030
RUST_LOG=info
EOF
```

3. Database Setup:

```bash
# Run migrations
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

4. Build and Run:

```bash
cargo build --release
./target/release/message_handler
```

## API Reference

### HTTP Endpoints

#### POST /message

Process a new message:

```json
{
  "user_id": "string",
  "platform": "Discord",
  "content": "string",
  "priority": "Normal",
  "thread_id": "string?",
  "metadata": {
    "key": "value"
  }
}
```

#### GET /health

Check service health:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": 1635724800
}
```

#### GET /metrics

Get service metrics:

```json
{
  "messages_processed": 100,
  "queue_size": 5,
  "error_rate": 0.01,
  "active_conversations": 10
}
```

## Configuration

Configuration is managed through environment variables and a config file:

```toml
# config/default.toml
[server]
host = "0.0.0.0"
port = 3030
thread_pool_size = 32

[database]
max_connections = 20

[queue]
size = 10000
retry_attempts = 3

[metrics]
port = 9000
```

## Deployment

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Add PostgreSQL addon
3. Configure environment variables:
   - `DATABASE_URL` (automatically set by Railway)
   - `ANTHROPIC_API_KEY`
   - `RUST_LOG`

### Docker Deployment

```dockerfile
FROM rust:1.75 as builder
WORKDIR /usr/src/app
COPY . .
RUN cargo build --release

FROM debian:bullseye-slim
COPY --from=builder /usr/src/app/target/release/message_handler /usr/local/bin/
CMD ["message_handler"]
```

## Development

### Running Tests

```bash
# Run all tests
cargo test

# Run specific test suite
cargo test conversation_handling

# Run with logging
RUST_LOG=debug cargo test
```

### Code Documentation

```bash
# Generate and open documentation
cargo doc --no-deps --open
```

### Database Migrations

```bash
# Create new migration
./scripts/create_migration.sh "add_user_preferences"

# Run migrations
./scripts/migrate.sh
```

## Module Documentation
