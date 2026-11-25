import { NextResponse } from "next/server";
import { generateReply, hasProviderKey, streamReply, type Provider } from "@/lib/ai/providers";
import { createClient } from "@/lib/supabase/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

function badRequest(error: string, status = 400, headers?: HeadersInit) {
  return NextResponse.json({ error }, { status, headers: { "Cache-Control": "private, no-store", ...headers } });
}

async function readLimitedBody(request: Request): Promise<string | null> {
  if (!request.body) return "";
  const reader = request.body.getReader();
  const chunks: Uint8Array[] = [];
  let totalBytes = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      totalBytes += value.byteLength;
      if (totalBytes > MAX_BODY_BYTES) {
        await reader.cancel();
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(body);
}

export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return badRequest("Sign in to use NP.ai.", 401);

  const declaredLength = Number(request.headers.get("content-length") || 0);
  if (declaredLength > MAX_BODY_BYTES) return badRequest("Request body is too large.", 413);

  let rawBody: string | null;
  try {
    rawBody = await readLimitedBody(request);
  } catch {
    return badRequest("Unable to read request body.");
  }
  if (rawBody === null) return badRequest("Request body is too large.", 413);

  let body: unknown;
  try { body = JSON.parse(rawBody); }
  catch { return badRequest("Request body must be valid JSON."); }

  if (!body || typeof body !== "object" || Array.isArray(body)) return badRequest("Request body must be a JSON object.");
  const input = body as Record<string, unknown>;
  const provider = input.provider;
  const model = input.model;
  const messages = input.messages;
  const conversationId = input.conversationId;

  if (typeof provider !== "string" || !Object.prototype.hasOwnProperty.call(allowedModels, provider)) {
    return badRequest("Choose a supported provider and model.");
  }
  const selectedProvider = provider as Provider;
  if (typeof model !== "string" || !allowedModels[selectedProvider].includes(model)) {
    return badRequest("The selected model is not allowed for this provider.");
  }
  if (conversationId !== undefined && (typeof conversationId !== "string" || !/^[0-9a-f-]{36}$/i.test(conversationId))) {
    return badRequest("Conversation ID is invalid.");
  }
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > MAX_MESSAGES) {
    return badRequest(`Send between 1 and ${MAX_MESSAGES} messages.`);
  }

  let totalChars = 0;
  const validatedMessages: ChatMessage[] = [];
  for (const item of messages) {
    if (!item || typeof item !== "object" || Array.isArray(item)) return badRequest("One or more messages are invalid.");
    const message = item as Record<string, unknown>;
    if ((message.role !== "user" && message.role !== "assistant") ||
        typeof message.content !== "string" || !message.content.trim() ||
        message.content.length > MAX_MESSAGE_CHARS) {
      return badRequest("One or more messages are invalid.");
    }
    totalChars += message.content.length;
    if (totalChars > MAX_TOTAL_CHARS) return badRequest("Conversation is too large.", 413);
    validatedMessages.push({ role: message.role, content: message.content });
  }
  const latestUserMessage = [...validatedMessages].reverse().find(message => message.role === "user");
  if (!latestUserMessage || validatedMessages[validatedMessages.length - 1].role !== "user") {
    return badRequest("A new user message is required.");
  }

  // Validate conversation ownership before consuming quota or calling a paid provider.
  if (conversationId) {
    const { data: ownedConversation, error: ownershipError } = await supabase.from("conversations")
      .select("id").eq("id", conversationId as string).eq("user_id", user.id).maybeSingle();
    if (ownershipError || !ownedConversation) return badRequest("Conversation not found.", 404);
  }
  if (!hasProviderKey(selectedProvider)) return badRequest("The selected AI provider is not configured on this server.", 503);

  const { data: quotaRows, error: quotaError } = await supabase.rpc("consume_chat_quota");
  if (quotaError) return badRequest("Account usage protection is unavailable. Apply the NP.ai Supabase migration and try again.", 503);
  const quota = Array.isArray(quotaRows) ? quotaRows[0] : quotaRows;
  if (!quota || quota.allowed !== true) {
    return badRequest("You've reached your account chat limit. Please wait before trying again.", 429, {
      "Retry-After": String(Math.max(1, Number(quota?.retry_after_seconds) || 60)),
      "X-Account-RateLimit-Remaining": String(Math.max(0, Number(quota?.short_remaining) || 0)),
    });
  }

  if (input.stream === true) {
    let savedConversationId = conversationId as string | undefined;

    if (savedConversationId) {
      const { error: updateError } = await supabase.from("conversations")
        .update({ provider: selectedProvider, model, updated_at: new Date().toISOString() })
        .eq("id", savedConversationId).eq("user_id", user.id);
      if (updateError) return badRequest("Unable to prepare this conversation.", 500);
    } else {
      const { data: created, error } = await supabase.from("conversations").insert({
        user_id: user.id,
        title: latestUserMessage.content.slice(0, 80),
        provider: selectedProvider,
        model,
      }).select("id").single();
      if (error || !created) return badRequest("Unable to create this conversation.", 500);
      savedConversationId = created.id;
    }

    const { error: userSaveError } = await supabase.from("messages").insert({
      conversation_id: savedConversationId,
      user_id: user.id,
      role: "user",
      content: latestUserMessage.content,
    });
    if (userSaveError) return badRequest("Unable to save your message.", 500);

    const abortController = new AbortController();
    request.signal.addEventListener("abort", () => abortController.abort(), { once: true });
    const encoder = new TextEncoder();
    const responseBody = new ReadableStream<Uint8Array>({
      async start(controller) {
        const send = (event: string, payload: Record<string, unknown>) => {
          controller.enqueue(encoder.encode(`event: ${event}\\ndata: ${JSON.stringify(payload)}\\n\\n`));
        };
        let reply = "";
        try {
          send("meta", {
            conversationId: savedConversationId,
            usage: { shortRemaining: quota.short_remaining, dailyRemaining: quota.daily_remaining },
          });
          for await (const delta of streamReply(selectedProvider, model, validatedMessages, abortController.signal)) {
            if (!delta) continue;
            reply += delta;
            send("token", { text: delta });
          }

          const finalReply = reply || "The model returned an empty response.";
          const { error: assistantSaveError } = await supabase.from("messages").insert({
            conversation_id: savedConversationId,
            user_id: user.id,
            role: "assistant",
            content: finalReply,
          });
          if (assistantSaveError) {
            send("error", { error: "Your response was generated but could not be saved." });
          } else {
            send("done", { conversationId: savedConversationId });
          }
        } catch (error) {
          if (abortController.signal.aborted) {
            send("error", { error: "The request was cancelled before completion." });
          } else if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
            send("error", { error: "The AI provider took too long to respond. Please try again." });
          } else {
            send("error", { error: "The AI provider could not complete your request. Please try again." });
          }
        } finally {
          controller.close();
        }
      },
      cancel() {
        abortController.abort();
      },
    });

    return new Response(responseBody, {
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "private, no-store, no-transform",
        Connection: "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  }

  let reply: string;
  try {
    reply = await generateReply(selectedProvider, model, validatedMessages);
  } catch (error) {
    if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
      return badRequest("The AI provider took too long to respond. Please try again.", 504);
    }
    return badRequest("The AI provider could not complete your request. Please try again.", 502);
  }

  let savedConversationId = conversationId as string | undefined;
  if (savedConversationId) {
    const { error: updateError } = await supabase.from("conversations")
      .update({ provider: selectedProvider, model, updated_at: new Date().toISOString() })
      .eq("id", savedConversationId).eq("user_id", user.id);
    if (updateError) return badRequest("Your reply was generated but the conversation could not be saved.", 500);
  } else {
    const { data: created, error } = await supabase.from("conversations").insert({
      user_id: user.id,
      title: latestUserMessage.content.slice(0, 80),
      provider: selectedProvider,
      model,
    }).select("id").single();
    if (error || !created) return badRequest("Your reply was generated but the conversation could not be saved.", 500);
    savedConversationId = created.id;
  }

  const { error: saveError } = await supabase.from("messages").insert([
    { conversation_id: savedConversationId, user_id: user.id, role: "user", content: latestUserMessage.content },
    { conversation_id: savedConversationId, user_id: user.id, role: "assistant", content: reply },
  ]);
  if (saveError) return badRequest("Your reply was generated but the conversation could not be saved.", 500);

  return NextResponse.json(
    { reply, conversationId: savedConversationId, usage: { shortRemaining: quota.short_remaining, dailyRemaining: quota.daily_remaining } },
    { headers: { "Cache-Control": "private, no-store" } },
  );
}
