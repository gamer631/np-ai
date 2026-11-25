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

function providerError(): Error {
  // Do not expose provider error bodies: they may include request details.
  return new Error("AI provider request failed.");
}

function nonEmptyText(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

async function providerFetch(url: string, init: RequestInit, signal?: AbortSignal): Promise<Response> {
  const timeoutSignal = AbortSignal.timeout(REQUEST_TIMEOUT_MS);
  const requestSignal = signal ? AbortSignal.any([signal, timeoutSignal]) : timeoutSignal;
  return fetch(url, {
    ...init,
    cache: "no-store",
    signal: requestSignal,
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
    if (!response.ok) throw providerError();
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
      body: JSON.stringify({ model, max_tokens: 2048, messages: conversation }),
    });
    const data = await readJson(response);
    if (!response.ok) throw providerError();
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
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-goog-api-key": key,
      },
      body: JSON.stringify({
        contents,
        generationConfig: { temperature: 0.7, maxOutputTokens: 2048 },
      }),
    },
  );
  const data = await readJson(response);
  if (!response.ok) throw providerError();
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


function extractStreamText(provider: Provider, payload: Record<string, unknown>): string {
  if (payload.error) throw providerError();

  if (provider === "openai") {
    const choices = Array.isArray(payload.choices) ? payload.choices : [];
    const first = choices[0] && typeof choices[0] === "object"
      ? (choices[0] as Record<string, unknown>)
      : {};
    const delta = first.delta && typeof first.delta === "object"
      ? (first.delta as Record<string, unknown>)
      : {};
    return typeof delta.content === "string" ? delta.content : "";
  }

  if (provider === "anthropic") {
    if (payload.type === "error") throw providerError();
    const delta = payload.delta && typeof payload.delta === "object"
      ? (payload.delta as Record<string, unknown>)
      : {};
    return payload.type === "content_block_delta" && delta.type === "text_delta" && typeof delta.text === "string"
      ? delta.text
      : "";
  }

  const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
  const candidate = candidates[0] && typeof candidates[0] === "object"
    ? (candidates[0] as Record<string, unknown>)
    : {};
  const content = candidate.content && typeof candidate.content === "object"
    ? (candidate.content as Record<string, unknown>)
    : {};
  const parts = Array.isArray(content.parts) ? content.parts : [];
  return parts
    .filter((part): part is Record<string, unknown> => Boolean(part) && typeof part === "object")
    .map((part) => nonEmptyText(part.text) || "")
    .filter(Boolean)
    .join("");
}

async function* readProviderEventStream(
  response: Response,
  provider: Provider,
): AsyncGenerator<string> {
  if (!response.body) throw providerError();
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let dataLines: string[] = [];

  const parseEvent = (lines: string[]): string => {
    if (!lines.length) return "";
    const data = lines.join("\n");
    if (data === "[DONE]") return "";
    try {
      const payload: unknown = JSON.parse(data);
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) return "";
      return extractStreamText(provider, payload as Record<string, unknown>);
    } catch (error) {
      if (error instanceof Error && error.message === "AI provider request failed.") throw error;
      // Ignore non-JSON keepalives and malformed event fragments.
      return "";
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let newline = buffer.indexOf("\n");
      while (newline !== -1) {
        const line = buffer.slice(0, newline).replace(/\r$/, "");
        buffer = buffer.slice(newline + 1);
        if (line === "") {
          const text = parseEvent(dataLines);
          dataLines = [];
          if (text) yield text;
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).replace(/^ /, ""));
        }
        newline = buffer.indexOf("\n");
      }
      if (done) break;
    }

    if (buffer.startsWith("data:")) dataLines.push(buffer.slice(5).replace(/^ /, ""));
    const finalText = parseEvent(dataLines);
    if (finalText) yield finalText;
  } finally {
    try { await reader.cancel(); } catch { /* The stream may already be closed. */ }
    reader.releaseLock();
  }
}

/**
 * Stream text deltas from a provider without exposing provider credentials or
 * upstream error payloads to the caller.
 */
export async function* streamReply(
  provider: Provider,
  model: string,
  messages: ChatMessage[],
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const conversation = messages.map(({ role, content }) => ({ role, content }));
  let url: string;
  let headers: Record<string, string>;
  let body: Record<string, unknown>;

  if (provider === "openai") {
    const key = process.env.OPENAI_API_KEY;
    if (!key) throw new Error("Provider is not configured.");
    url = "https://api.openai.com/v1/chat/completions";
    headers = { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
    body = { model, messages: conversation, temperature: 0.7, stream: true };
  } else if (provider === "anthropic") {
    const key = process.env.ANTHROPIC_API_KEY;
    if (!key) throw new Error("Provider is not configured.");
    url = "https://api.anthropic.com/v1/messages";
    headers = {
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "content-type": "application/json",
    };
    body = { model, max_tokens: 2048, messages: conversation, stream: true };
  } else {
    const key = process.env.GOOGLE_API_KEY;
    if (!key) throw new Error("Provider is not configured.");
    url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:streamGenerateContent?alt=sse`;
    headers = { "Content-Type": "application/json", "x-goog-api-key": key };
    body = {
      contents: conversation.map((message) => ({
        role: message.role === "assistant" ? "model" : "user",
        parts: [{ text: message.content }],
      })),
      generationConfig: { temperature: 0.7, maxOutputTokens: 2048 },
    };
  }

  const response = await providerFetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  }, signal);
  if (!response.ok) throw providerError();
  yield* readProviderEventStream(response, provider);
}
