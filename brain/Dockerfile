# Dockerfile
FROM rust:1.75 as builder

WORKDIR /usr/src/app
COPY . .

# Install dependencies
RUN cargo build --release

# Runtime stage
FROM debian:bullseye-slim
COPY --from=builder /usr/src/app/target/release/message_handler /usr/local/bin/

# Install necessary runtime libraries
RUN apt-get update && apt-get install -y \
    libssl1.1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 3030
EXPOSE 9000

CMD ["message_handler"]
