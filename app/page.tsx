"use client";

import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

type Message = { role: "user" | "assistant"; content: string };
type Conversation = { id: string; title: string; provider: string; model: string; updated_at: string };
const models = [
  { provider: "openai", model: "gpt-4o-mini", label: "GPT-4o mini", vendor: "OpenAI" },
  { provider: "anthropic", model: "claude-sonnet-4-20250514", label: "Claude Sonnet 4", vendor: "Anthropic" },
  { provider: "google", model: "gemini-2.5-flash", label: "Gemini 2.5 Flash", vendor: "Google" }
] as const;

export default function Home() {
  const [selected, setSelected] = useState("openai:gpt-4o-mini");
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [history, setHistory] = useState<Conversation[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);

  const current = models.find(m => `${m.provider}:${m.model}` === selected) || models[0];

  async function refreshHistory() {
    const response = await fetch("/api/conversations", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      setHistory(data.conversations || []);
    }
  }

  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY) return;
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      setUserEmail(data.user?.email ?? null);
      if (data.user) void refreshHistory();
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user.email ?? null);
      if (session?.user) void refreshHistory();
      else setHistory([]);
    });
    return () => subscription.unsubscribe();
  }, []);

  async function openConversation(item: Conversation) {
    setError("");
    const response = await fetch(`/api/conversations/${item.id}`, { cache: "no-store" });
    const data = await response.json();
    if (!response.ok) { setError(data.error || "Unable to open conversation."); return; }
    setConversationId(item.id);
    setMessages(data.messages || []);
    setSelected(`${item.provider}:${item.model}`);
    setHistoryOpen(false);
  }

  function newChat() {
    setConversationId(null);
    setMessages([]);
    setPrompt("");
    setError("");
    setHistoryOpen(false);
  }

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    setUserEmail(null);
    newChat();
  }

  async function sendMessage(event?: FormEvent) {
    event?.preventDefault();
    const text = prompt.trim();
    if (!text || loading) return;
    const next: Message[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setPrompt("");
    setError("");
    setLoading(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({ provider: current.provider, model: current.model, messages: next, conversationId, stream: true })
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || "Unable to get a response.");
      }
      if (!response.headers.get("content-type")?.includes("text/event-stream")) {
        const data = await response.json();
        setMessages([...next, { role: "assistant", content: data.reply }]);
        setConversationId(data.conversationId || conversationId);
      } else {
        let accumulated = "";
        setMessages([...next, { role: "assistant", content: "" }]);
        await readChatEventStream(
          response,
          (id) => setConversationId(id),
          (delta) => {
            accumulated += delta;
            setMessages([...next, { role: "assistant", content: accumulated }]);
          },
        );
        if (!accumulated) setMessages([...next, { role: "assistant", content: "The model returned an empty response." }]);
      }
      void refreshHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="NP.ai home"><span className="brand-mark">N</span><span>NP<span className="brand-dot">.</span>ai</span></Link>
        <div className="top-actions">
          <span className="status-dot" /> Multi-model workspace
          {userEmail ? <><button className="header-link" onClick={() => setHistoryOpen(!historyOpen)}>History ({history.length})</button><span className="user-email">{userEmail}</span><button className="header-link" onClick={signOut}>Sign out</button></> : <Link href="/auth">Sign in</Link>}
          <a href="https://github.com/gamer631/np-ai" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </header>

      {historyOpen && <aside className="history-panel"><div className="history-heading"><strong>Your conversations</strong><button onClick={() => setHistoryOpen(false)}>Close</button></div>{history.length === 0 ? <p>No saved conversations yet.</p> : history.map(item => <button className="history-item" key={item.id} onClick={() => void openConversation(item)}><span>{item.title}</span><small>{new Date(item.updated_at).toLocaleDateString()}</small></button>)}</aside>}

      <section className={`workspace ${messages.length ? "has-messages" : ""}`}>
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="eyebrow"><span /> YOUR AI, YOUR WAY</div>
            <h1>Think beyond<br /><span>the ordinary.</span></h1>
            <p>One thoughtful workspace. Multiple powerful AI models.<br className="desktop-break" /> Choose your model and make something remarkable.</p>
            <div className="suggestions">
              {["Help me build a website", "Explain a complex idea simply", "Write a professional introduction"].map(item =>
                <button key={item} className="suggestion" onClick={() => setPrompt(item)}>{item}<span>↗</span></button>
              )}
            </div>
          </div>
        ) : (
          <div className="conversation">
            {messages.map((message, index) => (
              <article className={`message ${message.role}`} key={index}>
                <div className="message-avatar">{message.role === "user" ? "Y" : "N"}</div>
                <div className="message-body"><div className="message-label">{message.role === "user" ? "YOU" : "NP.AI"}</div><p>{message.content}</p></div>
              </article>
            ))}
            {loading && <div className="message assistant"><div className="message-avatar">N</div><div className="message-body"><div className="message-label">NP.AI · THINKING</div><div className="typing"><i /><i /><i /></div></div></div>}
            <div id="conversation-end" />
          </div>
        )}
        {error && <div className="error-message" role="alert">{error}{error.includes("Sign in") && <> <Link href="/auth">Sign in here</Link>.</>}</div>}
        <form className="composer" onSubmit={sendMessage}>
          <textarea value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={onKeyDown} placeholder={userEmail ? "Message NP.ai..." : "Sign in to start chatting..."} rows={2} aria-label="Message NP.ai" />
          <div className="composer-bottom">
            <label className="model-select"><span className="select-spark">✳</span><select value={selected} onChange={e => setSelected(e.target.value)} aria-label="Choose AI model">{models.map(m => <option key={m.model} value={`${m.provider}:${m.model}`}>{m.label} · {m.vendor}</option>)}</select><span className="chevron">⌄</span></label>
            <div className="send-area"><span className="hint">Enter to send · Shift + Enter for new line</span><button className="send-button" type="submit" disabled={loading || !prompt.trim() || !userEmail} aria-label="Send message">↑</button></div>
          </div>
        </form>
        <div className="disclaimer">AI can make mistakes. Check important information. Your API keys stay on your server.</div>
      </section>
      <footer><span>© {new Date().getFullYear()} NP.ai</span><span>Built for curiosity. Powered by choice.</span></footer>
    </main>
  );
}


async function readChatEventStream(
  response: Response,
  onConversation: (id: string) => void,
  onToken: (text: string) => void,
): Promise<void> {
  if (!response.body) throw new Error("The streaming response was empty.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "";
  let dataLines: string[] = [];

  const dispatch = () => {
    if (!dataLines.length) {
      eventName = "";
      return;
    }
    const raw = dataLines.join("\\n");
    dataLines = [];
    const currentEvent = eventName;
    eventName = "";
    let payload: Record<string, unknown>;
    try {
      const parsed: unknown = JSON.parse(raw);
      payload = parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? parsed as Record<string, unknown>
        : {};
    } catch {
      throw new Error("The server sent an invalid streaming event.");
    }
    if (currentEvent === "meta" && typeof payload.conversationId === "string") {
      onConversation(payload.conversationId);
    } else if (currentEvent === "token" && typeof payload.text === "string") {
      onToken(payload.text);
    } else if (currentEvent === "error") {
      throw new Error(typeof payload.error === "string" ? payload.error : "The response stream failed.");
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let newline = buffer.indexOf("\\n");
      while (newline !== -1) {
        const line = buffer.slice(0, newline).replace(/\\r$/, "");
        buffer = buffer.slice(newline + 1);
        if (!line) dispatch();
        else if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).replace(/^ /, ""));
        newline = buffer.indexOf("\\n");
      }
      if (done) break;
    }
    if (buffer.startsWith("data:")) dataLines.push(buffer.slice(5).replace(/^ /, ""));
    dispatch();
  } catch (error) {
    try { await reader.cancel(); } catch { /* The stream may already be closed. */ }
    throw error;
  } finally {
    reader.releaseLock();
  }
}
