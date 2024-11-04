use reqwest::Client;
use serde_json::json;
use crate::error::ServiceError;

#[derive(Debug)]
pub struct ClaudeClient {
    client: Client,
    api_key: String,
}

impl ClaudeClient {
    pub fn new(api_key: String) -> Self {
        Self {
            client: Client::new(),
            api_key,
        }
    }

    pub async fn get_response(&self, message: &str) -> Result<String, ServiceError> {
        let response = self
            .client
            .post("https://api.anthropic.com/v1/messages")
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .json(&json!({
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1024,
                "messages": [{
                    "role": "user",
                    "content": message
                }]
            }))
            .send()
            .await
            .map_err(|e| ServiceError::ProcessingError(e.to_string()))?;

        let body = response
            .json::<serde_json::Value>()
            .await
            .map_err(|e| ServiceError::ProcessingError(e.to_string()))?;

        Ok(body["content"][0]["text"]
            .as_str()
            .unwrap_or("Sorry, I couldn't process that request.")
            .to_string())
    }
}