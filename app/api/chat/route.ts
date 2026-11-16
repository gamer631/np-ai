import { NextResponse } from "next/server";
import { generateReply, hasProviderKey, type Provider } from "@/lib/ai/providers";

export const runtime = "nodejs";

const MAX_BODY_BYTES = 64 * 1024;
const MAX_MESSAGES = 40;
const MAX_MESSAGE_CHARS = 12_000;
const MAX_TOTAL_CHARS = 40_000;

const allowedModels: Record<Provider, readonly string[]> = {
  openai: ["gpt-4o-mini"],
  anthropic: ["claude-sonnet-4-20250514"],
  google: ["gemini-2.5-flash"],
};

type ChatMessage = { role: "user" | "assistant"; content: string };

function badRequest(error: string, status = 400) {
  return NextResponse.json({ error }, { status });
}

export async function POST(request: Request) {
  const declaredLength = Number(request.headers.get("content-length") || 0);
  if (declaredLength > MAX_BODY_BYTES) {
    return badRequest("Request body is too large.", 413);
  }

  let rawBody: string;
  try {
    rawBody = await request.text();
  } catch {
    return badRequest("Unable to read request body.", 400);
  }

  if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) {
    return badRequest("Request body is too large.", 413);
  }

  let body: unknown;
  try {
    body = JSON.parse(rawBody);
  } catch {
    return badRequest("Request body must be valid JSON.");
  }

  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return badRequest("Request body must be a JSON object.");
  }

  const input = body as Record<string, unknown>;
  const provider = input.provider;
  const model = input.model;
  const messages = input.messages;

  if (
    typeof provider !== "string" ||
    !Object.prototype.hasOwnProperty.call(allowedModels, provider)
  ) {
    return badRequest("Choose a supported provider and model.");
  }

  const selectedProvider = provider as Provider;
  if (
    typeof model !== "string" ||
    !allowedModels[selectedProvider].includes(model)
  ) {
    return badRequest("The selected model is not allowed for this provider.");
  }

  if (!Array.isArray(messages) || messages.length === 0 || messages.length > MAX_MESSAGES) {
    return badRequest(`Send between 1 and ${MAX_MESSAGES} messages.`);
  }

  let totalChars = 0;
  const validatedMessages: ChatMessage[] = [];
  for (const item of messages) {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return badRequest("One or more messages are invalid.");
    }
    const message = item as Record<string, unknown>;
    if (
      (message.role !== "user" && message.role !== "assistant") ||
      typeof message.content !== "string" ||
      message.content.trim().length === 0 ||
      message.content.length > MAX_MESSAGE_CHARS
    ) {
      return badRequest("One or more messages are invalid.");
    }
    totalChars += message.content.length;
    if (totalChars > MAX_TOTAL_CHARS) {
      return badRequest("Conversation is too large.", 413);
    }
    validatedMessages.push({ role: message.role, content: message.content });
  }

  if (!hasProviderKey(selectedProvider)) {
    return badRequest("The selected AI provider is not configured on this server.", 503);
  }

  try {
    const reply = await generateReply(selectedProvider, model, validatedMessages);
    return NextResponse.json({ reply });
  } catch (error) {
    if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
      return NextResponse.json({ error: "The AI provider took too long to respond. Please try again." }, { status: 504 });
    }
    return NextResponse.json(
      { error: "The AI provider could not complete your request. Please try again." },
      { status: 502 }
    );
  }
}
