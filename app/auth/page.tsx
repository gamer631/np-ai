"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function AuthPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const supabase = createClient();
      if (mode === "signup") {
        const { data, error: authError } = await supabase.auth.signUp({
          email, password, options: { data: { display_name: name }, emailRedirectTo: `${window.location.origin}/auth/callback` },
        });
        if (authError) throw authError;
        if (!data.session) setNotice("Account created. Check your email to confirm your address, then sign in.");
        else window.location.assign("/");
      } else {
        const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
        if (authError) throw authError;
        window.location.assign("/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed. Please try again.");
    } finally { setBusy(false); }
  }

  return (
    <main className="shell">
      <header className="topbar"><Link className="brand" href="/"><span className="brand-mark">N</span><span>NP<span className="brand-dot">.</span>ai</span></Link><div className="top-actions">Nepal-first AI workspace</div></header>
      <section className="auth-card">
        <div className="eyebrow"><span /> YOUR AI, YOUR WAY</div>
        <h1>{mode === "signin" ? "Welcome back." : "Create your account."}</h1>
        <p className="auth-subtitle">Sign in to save your conversations and use your personal AI workspace.</p>
        <div className="auth-tabs"><button type="button" className={mode === "signin" ? "active" : ""} onClick={() => {setMode("signin");setError("");setNotice("");}}>Sign in</button><button type="button" className={mode === "signup" ? "active" : ""} onClick={() => {setMode("signup");setError("");setNotice("");}}>Create account</button></div>
        <form className="auth-form" onSubmit={submit}>
          {mode === "signup" && <label>Your name<input autoComplete="name" value={name} onChange={e=>setName(e.target.value)} required maxLength={80} placeholder="Your name"/></label>}
          <label>Email address<input type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} required placeholder="you@example.com"/></label>
          <label>Password<input type="password" autoComplete={mode === "signin" ? "current-password" : "new-password"} value={password} onChange={e=>setPassword(e.target.value)} required minLength={8} placeholder="At least 8 characters"/></label>
          {error && <div className="error-message" role="alert">{error}</div>}
          {notice && <div className="success-message" role="status">{notice}</div>}
          <button className="auth-submit" type="submit" disabled={busy}>{busy ? "Please wait…" : mode === "signin" ? "Sign in to NP.ai" : "Create NP.ai account"} <span>→</span></button>
        </form>
        <p className="auth-footnote">By continuing, you agree to use NP.ai responsibly. <Link href="/">Back to chat</Link></p>
      </section>
      <footer><span>© {new Date().getFullYear()} NP.ai</span><span>Your conversations, private to your account.</span></footer>
    </main>
  );
}
