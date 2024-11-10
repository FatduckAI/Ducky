import type { AIProvider } from "../agent/types";

interface OllamaResponse {
  response: string;
  done: boolean;
}

export class OllamaRunpodProvider implements AIProvider {
  type: "ollama" = "ollama";
  private static instance: OllamaRunpodProvider;
  private baseUrl: string;

  config = {
    model: "llama2",
    temperature: 0.7,
    maxTokens: 1024,
  };

  private constructor() {
    const runpodEndpoint = process.env.RUNPOD_OLLAMA_ENDPOINT;
    if (!runpodEndpoint) {
      throw new Error(
        "RUNPOD_OLLAMA_ENDPOINT not found in environment variables"
      );
    }

    this.baseUrl = runpodEndpoint.endsWith("/")
      ? runpodEndpoint.slice(0, -1)
      : runpodEndpoint;
  }

  public static getInstance(): OllamaRunpodProvider {
    if (!OllamaRunpodProvider.instance) {
      OllamaRunpodProvider.instance = new OllamaRunpodProvider();
    }
    return OllamaRunpodProvider.instance;
  }

  private async makeRequest(endpoint: string, body: any) {
    const url = `${this.baseUrl}${endpoint}`;
    console.log(`Making request to: ${url}`);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Ollama API error (${url}): ${response.status} - ${errorText}`
        );
      }

      return response;
    } catch (error) {
      if (
        error instanceof TypeError &&
        error.message.includes("fetch failed")
      ) {
        throw new Error(
          `Failed to connect to Ollama at ${url}. Please check if the service is running and the endpoint is correct.`
        );
      }
      throw error;
    }
  }

  async generateResponse(
    systemPrompt: string,
    userPrompt: string
  ): Promise<string> {
    try {
      // Check if model exists first
      await this.makeRequest("/api/tags", {});

      const response = await this.makeRequest("/api/generate", {
        model: this.config.model,
        prompt: `${systemPrompt}\n\n${userPrompt}`,
        options: {
          temperature: this.config.temperature,
          num_predict: this.config.maxTokens,
        },
        stream: false,
      });

      const result = (await response.json()) as OllamaResponse;

      if (!result.response) {
        throw new Error("No content in Ollama response");
      }

      return result.response;
    } catch (error) {
      console.error("Error generating response from Ollama:", error);
      throw error;
    }
  }
}

export const ollamaProvider = OllamaRunpodProvider.getInstance();
