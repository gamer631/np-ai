import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { data: conversation, error } = await supabase.from("conversations").select("id,title,provider,model").eq("id", id).eq("user_id", user.id).maybeSingle();
  if (error || !conversation) return NextResponse.json({ error: "Conversation not found." }, { status: 404 });
  const { data: messages, error: messageError } = await supabase.from("messages").select("role,content,created_at").eq("conversation_id", id).eq("user_id", user.id).order("created_at", { ascending: true });
  if (messageError) return NextResponse.json({ error: "Unable to load messages." }, { status: 500 });
  return NextResponse.json({ conversation, messages }, { headers: { "Cache-Control": "private, no-store" } });
}
