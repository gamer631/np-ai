export type Provider = "openai" | "anthropic" | "google";

type ChatMessage = { role: "user" | "assistant"; content: string };

const REQUEST_TIMEOUT_MS = 30_000;

const envKeys: Record<Provider, string> = {
  openai: "OPENAI_API_KEY",
  anthropic: "ANTHROPIC_API_KEY",
  google: "GOOGLE_API_KEY",
};

export function hasProviderKey(provider: Provider): boolean {
  return Boolean(process.env[envKeys[provider]]?.trim());
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  try {
    const value: unknown = await response.json();
    return value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  } catch {
    return {};
  }
}

function providerError(data: Record<string, unknown>, fallback: string): Error {
  // Provider error bodies are deliberately not returned to clients or logged:
  // they can contain request details and should not become an information leak.
  return new Error(fallback);
}

function nonEmptyText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

async function providerFetch(url: string, init: RequestInit): Promise<Response> {
  return fetch(url, {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
}

export async function generateReply(
  provider: Provider,
  model: string,
  messages: ChatMessage[],
): Promise<string> {
  const conversation = messages.map(({ role, content }) => ({ role, content }));

  if (provider === "openai") {
    const key = process.env.OPENAI_API_KEY;
    if (!key) throw new Error("Provider is not configured.");
    const response = await providerFetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages: conversation, temperature: 0.7 }),
    });
    const data = await readJson(response);
    if (!response.ok) throw providerError(data, "OpenAI request failed.");
    const choices = Array.isArray(data.choices) ? data.choices : [];
    const first = choices[0] && typeof choices[0] === "object"
      ? (choices[0] as Record<string, unknown>)
      : {};
    const message = first.message && typeof first.message === "object"
      ? (first.message as Record<string, unknown>)
      : {};
    return nonEmptyText(message.content) || "The model returned an empty response.";
  }

  if (provider === "anthropic") {
    const key = process.env.ANTHROPIC_API_KEY;
    if (!key) throw new Error("Provider is not configured.");
    const response = await providerFetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model,
        max_tokens: 2048,
        messages: conversation,
      }),
    });
    const data = await readJson(response);
    if (!response.ok) throw providerError(data, "Anthropic request failed.");
    const content = Array.isArray(data.content) ? data.content : [];
    const text = content
      .filter((part): part is Record<string, unknown> =>
        Boolean(part) && typeof part === "object" && (part as Record<string, unknown>).type === "text",
      )
      .map((part) => nonEmptyText(part.text) || "")
      .filter(Boolean)
      .join("\n");
    return text || "The model returned an empty response.";
  }

  const key = process.env.GOOGLE_API_KEY;
  if (!key) throw new Error("Provider is not configured.");
  const contents = conversation.map((message) => ({
    role: message.role === "assistant" ? "model" : "user",
    parts: [{ text: message.content }],
  }));
  const response = await providerFetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(key)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents,
        generationConfig: { temperature: 0.7, maxOutputTokens: 2048 },
      }),
    },
  );
  const data = await readJson(response);
  if (!response.ok) throw providerError(data, "Google AI request failed.");
  const candidates = Array.isArray(data.candidates) ? data.candidates : [];
  const candidate = candidates[0] && typeof candidates[0] === "object"
    ? (candidates[0] as Record<string, unknown>)
    : {};
  const content = candidate.content && typeof candidate.content === "object"
    ? (candidate.content as Record<string, unknown>)
    : {};
  const parts = Array.isArray(content.parts) ? content.parts : [];
  const text = parts
    .filter((part): part is Record<string, unknown> => Boolean(part) && typeof part === "object")
    .map((part) => nonEmptyText(part.text) || "")
    .filter(Boolean)
    .join("");
  return text || "The model returned an empty response.";
}
