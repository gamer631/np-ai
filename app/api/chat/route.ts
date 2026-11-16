import { NextResponse } from "next/server";
import { generateReply, hasProviderKey, type Provider } from "@/lib/ai/providers";

export const runtime = "nodejs";

const allowedProviders: Provider[] = ["openai", "anthropic", "google"];

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const provider = body.provider as Provider;
    const model = typeof body.model === "string" ? body.model.trim() : "";
    const messages = body.messages;

    if (!allowedProviders.includes(provider) || !model) {
      return NextResponse.json({ error: "Choose a supported provider and model." }, { status: 400 });
    }
    if (!Array.isArray(messages) || messages.length === 0 || messages.length > 40) {
      return NextResponse.json({ error: "Send between 1 and 40 messages." }, { status: 400 });
    }
    if (!messages.every((m: any) =>
      (m.role === "user" || m.role === "assistant") &&
      typeof m.content === "string" && m.content.length > 0 && m.content.length <= 12000
    )) {
      return NextResponse.json({ error: "One or more messages are invalid." }, { status: 400 });
    }
    if (!hasProviderKey(provider)) {
      return NextResponse.json({ error: `Add the ${provider} API key to your .env.local file, then restart the server.` }, { status: 400 });
    }

    const reply = await generateReply(provider, model, messages);
    return NextResponse.json({ reply });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Something went wrong.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
