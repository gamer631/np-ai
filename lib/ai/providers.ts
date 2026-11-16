export type Provider = "openai" | "anthropic" | "google";

type ChatMessage = { role: "user" | "assistant"; content: string };

const envKeys: Record<Provider, string> = {
  openai: "OPENAI_API_KEY",
  anthropic: "ANTHROPIC_API_KEY",
  google: "GOOGLE_API_KEY"
};

export function hasProviderKey(provider: Provider) {
  return Boolean(process.env[envKeys[provider]]);
}

export async function generateReply(
  provider: Provider,
  model: string,
  messages: ChatMessage[]
): Promise<string> {
  const conversation = messages.map(({ role, content }) => ({ role, content }));

  if (provider === "openai") {
    const key = process.env.OPENAI_API_KEY;
    if (!key) throw new Error("OpenAI API key is not configured.");
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages: conversation, temperature: 0.7 })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error?.message || "OpenAI request failed.");
    return data.choices?.[0]?.message?.content || "The model returned an empty response.";
  }

  if (provider === "anthropic") {
    const key = process.env.ANTHROPIC_API_KEY;
    if (!key) throw new Error("Anthropic API key is not configured.");
    const system = conversation.filter(m => m.role === "assistant" ? false : false);
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
      },
      body: JSON.stringify({
        model,
        max_tokens: 2048,
        messages: conversation.map(m => ({ role: m.role, content: m.content }))
      })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error?.message || "Anthropic request failed.");
    return (data.content || []).filter((part: { type: string }) => part.type === "text").map((part: { text: string }) => part.text).join("\n") || "The model returned an empty response.";
  }

  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error("Google AI API key is not configured.");
  const contents = conversation.map(m => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: m.content }]
  }));
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ contents, generationConfig: { temperature: 0.7, maxOutputTokens: 2048 } })
    }
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || "Google AI request failed.");
  return data.candidates?.[0]?.content?.parts?.map((part: { text?: string }) => part.text || "").join("") || "The model returned an empty response.";
}
