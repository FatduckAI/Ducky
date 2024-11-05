import Together from "together-ai";

export interface TogetherConfig {
  apiKey: string;
  model: string;
  maxTokens: number;
}

export const defaultConfig: TogetherConfig = {
  apiKey: process.env.TOGETHER_API_KEY || "",
  model: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
  maxTokens: 1024,
};

let togetherInstance: Together | null = null;

export const getTogetherClient = (): Together => {
  if (!togetherInstance) {
    togetherInstance = new Together({
      apiKey: defaultConfig.apiKey,
    });
  }
  return togetherInstance;
};

export const generateTogetherResponse = async (
  systemPrompt: string,
  userPrompt: string
): Promise<string> => {
  const client = getTogetherClient();

  const response = await client.chat.completions.create({
    model: defaultConfig.model,
    max_tokens: defaultConfig.maxTokens,
    messages: [
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: userPrompt,
      },
    ],
  });

  return response.choices[0]?.message?.content || "";
};
