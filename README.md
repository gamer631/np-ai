# NP.ai

**Think beyond.** NP.ai is a Nepal-first multi-provider AI workspace.

NP.ai is an application, not a foundation model. It securely calls AI providers using server-side API keys supplied by the operator. Supabase provides authentication, PostgreSQL storage, row-level security, and per-account usage quotas.

## Current capabilities

- Responsive multi-model chat interface (OpenAI, Anthropic, Google)
- Supabase email/password sign-up, sign-in, email confirmation callback, and sign-out
- Cookie-based SSR sessions using `@supabase/ssr`
- Authenticated chat API; unauthenticated requests are rejected
- Per-account quotas enforced atomically in PostgreSQL: 10 chats per 10 minutes and 100 per 24 hours
- Conversation and message persistence with user ownership enforced by Row Level Security
- Conversation history endpoints and a basic history panel
- Streaming responses from OpenAI, Anthropic, and Google with server-side persistence
- Provider keys stay server-side

## Stack

- Next.js 15 App Router, React 19, TypeScript
- Supabase Auth + PostgreSQL + RLS
- `@supabase/ssr` and `@supabase/supabase-js`

## Create and connect Supabase

1. Create a Supabase project in your own account at https://supabase.com/dashboard.
2. Select a region close to Nepal (Singapore if available).
3. In the project SQL Editor, run the complete migration at `supabase/migrations/202611160001_initial_schema.sql`.
4. In Project Settings -> API, copy the Project URL and publishable key.
5. In local `.env.local`, set:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
6. In Supabase Authentication -> URL Configuration, set the Site URL to your deployed app URL (or `http://localhost:3000` for local development) and add the redirect URL `http://localhost:3000/auth/callback` plus your production `https://YOUR_DOMAIN/auth/callback`.
7. Enable email/password authentication. Configure SMTP before inviting real users; the built-in email sender is intended for limited testing.

**Never put a Supabase secret/service-role key in browser variables, GitHub commits, or chat.** This app uses the publishable key with user sessions and RLS. The database password is not needed by the application.

## Run locally

Requirements: Node.js 20.9 or newer.

```bash
git clone https://github.com/gamer631/np-ai.git
cd np-ai
npm ci
cp .env.example .env.local
# Fill in Supabase URL, publishable key, and at least one AI provider key.
npm run dev
```

Open http://localhost:3000 and create an account at /auth.

## Local database security tests

Requirements: Docker and the Supabase CLI.

```bash
supabase start
supabase db reset
supabase test db
```

The pgTAP suite in `supabase/tests/rls_quota.test.sql` checks two-user row isolation, cross-account writes, quota-ledger privacy, and the short-window quota boundary. CI pins Supabase CLI 3.4.0 and runs the suite against a disposable local stack. These tests run against a disposable local Supabase database; they do not apply migrations to your hosted project.

## AI provider keys

Add at least one key to the server environment:

- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys
- Google AI Studio: https://aistudio.google.com/app/apikey

Provider usage may incur charges. Never commit `.env.local` or expose provider keys to the browser.

## Database and security

The SQL migration creates:

- `profiles` — one profile per Supabase Auth user
- `conversations` — user-owned conversation metadata
- `messages` — user-owned conversation messages
- `chat_usage_events` — private quota event ledger

RLS is enabled on every application table. The quota function uses a per-user PostgreSQL advisory transaction lock so concurrent requests cannot race past the quota. It is callable only by authenticated users and derives the user ID from `auth.uid()`.

The chat endpoint also validates request sizes, model/provider pairing, message roles, and server provider configuration. Provider calls have a timeout and normalized errors. Streaming errors are redacted and client cancellation aborts upstream work.

## Important limitations

- Supabase project creation, database migration execution, Auth URL configuration, provider keys, and deployment secrets must be completed in the owner's accounts.
- The current quotas count chat requests, including requests where a provider later fails; this avoids free retries bypassing usage accounting.
- Account creation abuse protection, billing, payment collection, streaming, attachments, admin tools, and comprehensive automated tests are not yet implemented.
- This repository has not yet been verified with a live Supabase project or production provider credentials. Do not treat it as production-ready until the CI checks, migration, auth flow, quota behavior, and staging deployment are tested.

## Roadmap

- [x] Supabase Auth integration
- [x] User profiles and RLS-protected conversations
- [x] Per-account atomic chat quotas
- [ ] Live Supabase migration and authentication verification
- [x] Provider adapter unit tests (including streaming and error redaction)
- [x] Local Supabase pgTAP suite added; passing CI run still required
- [ ] Chat API integration and end-to-end tests
- [x] Streaming responses across the three supported providers
- [ ] File and document uploads
- [ ] Billing, plan management, and operational monitoring
- [ ] Production deployment and security review

## License

MIT. See [LICENSE](./LICENSE).
