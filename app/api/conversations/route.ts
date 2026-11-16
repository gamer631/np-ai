import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return NextResponse.json({ error: "Sign in required." }, { status: 401 });
  const { data, error } = await supabase.from("conversations").select("id,title,provider,model,created_at,updated_at").eq("user_id", user.id).order("updated_at", { ascending: false }).limit(50);
  if (error) return NextResponse.json({ error: "Unable to load conversations." }, { status: 500 });
  return NextResponse.json({ conversations: data }, { headers: { "Cache-Control": "private, no-store" } });
}
