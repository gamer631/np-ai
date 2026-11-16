"use client";

import { FormEvent, KeyboardEvent, useState } from "react";

type Message = { role: "user" | "assistant"; content: string };
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

  const current = models.find(m => `${m.provider}:${m.model}` === selected) || models[0];

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
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: current.provider, model: current.model, messages: next })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to get a response.");
      setMessages([...next, { role: "assistant", content: data.reply }]);
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
        <a className="brand" href="/" aria-label="NP.ai home"><span className="brand-mark">N</span><span>NP<span className="brand-dot">.</span>ai</span></a>
        <div className="top-actions"><span className="status-dot" /> Multi-model workspace <a href="https://github.com/gamer631/np-ai" target="_blank" rel="noreferrer">GitHub ↗</a></div>
      </header>

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
        {error && <div className="error-message" role="alert">{error}</div>}
        <form className="composer" onSubmit={sendMessage}>
          <textarea value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={onKeyDown} placeholder="Message NP.ai..." rows={2} aria-label="Message NP.ai" />
          <div className="composer-bottom">
            <label className="model-select"><span className="select-spark">✳</span><select value={selected} onChange={e => setSelected(e.target.value)} aria-label="Choose AI model">{models.map(m => <option key={m.model} value={`${m.provider}:${m.model}`}>{m.label} · {m.vendor}</option>)}</select><span className="chevron">⌄</span></label>
            <div className="send-area"><span className="hint">Enter to send · Shift + Enter for new line</span><button className="send-button" type="submit" disabled={loading || !prompt.trim()} aria-label="Send message">↑</button></div>
          </div>
        </form>
        <div className="disclaimer">AI can make mistakes. Check important information. Your API keys stay on your server.</div>
      </section>
      <footer><span>© {new Date().getFullYear()} NP.ai</span><span>Built for curiosity. Powered by choice.</span></footer>
    </main>
  );
}
