# NP.ai

**Think beyond.** NP.ai is an open-source, Nepal-first multi-provider AI chat workspace.

> This project is an AI application, not a foundation model. It connects to model providers using API keys supplied by the person running the app.

## Features

- Clean, responsive chat interface
- Choose between OpenAI, Anthropic Claude, and Google Gemini
- Provider calls run on the server; API keys are never sent to the browser
- Server-side request validation, body-size limits, and provider timeouts
- Optional local-development rate-limit bypass; production requires durable Upstash-backed limits
- Provider credentials are sent in authorization headers, not query strings

## Requirements

- Node.js 20.9 or newer
- An API key from at least one supported provider
- An Upstash Redis database for production chat usage limits

## Run locally

1. Clone the repository:
   ```bash
   git clone https://github.com/gamer631/np-ai.git
   cd np-ai
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create your local environment file:
   ```bash
   cp .env.example .env.local
   ```
4. Add at least one provider key to `.env.local`.
5. Start the development server:
   ```bash
   npm run dev
   ```
6. Open http://localhost:3000.

In development, requests are allowed when Upstash is not configured. Configure the Upstash variables locally to exercise real quotas. In production, the chat endpoint fails closed unless the limiter is configured and reachable.

## Production usage limits

Create an Upstash Redis database and set these server-only environment variables:

- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`
- `RATE_LIMIT_SALT` — a unique random secret of at least 32 bytes; generate with `openssl rand -hex 32`

The chat endpoint applies these per-client-IP limits:

- 10 requests per 10 minutes
- 100 requests per 24 hours

Counters are incremented atomically in Redis. Client IPs are HMAC-hashed before being used in Redis keys; raw IP addresses are not stored in the keys. The limiter trusts the ingress headers `cf-connecting-ip`, `x-real-ip`, or the first value in `x-forwarded-for`. Deploy behind a trusted proxy that overwrites these headers; do not expose the app directly to untrusted traffic with spoofable forwarding headers.

These are anonymous IP-based abuse controls, not per-account billing quotas. Shared networks may share a limit, and users can potentially change IPs. Per-user quotas require authenticated accounts and a persistent user identity.

If the Redis service is unavailable or misconfigured, chat requests return 503 rather than bypassing production limits. A rate-limited request returns 429 and a `Retry-After` header.

## Provider keys

- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys
- Google AI Studio: https://aistudio.google.com/app/apikey

Only configure the providers you intend to use. API usage may incur charges according to each provider's pricing. Never commit `.env.local` or publish API keys.

## Supported model defaults

| Provider | Model |
| --- | --- |
| OpenAI | `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4-20250514` |
| Google | `gemini-2.5-flash` |

Model availability and pricing can change. Update the model IDs in `app/page.tsx` and the server allowlist in `app/api/chat/route.ts` together.

## Project structure

```
app/
  api/chat/route.ts    Server-side chat endpoint
  globals.css          Application styles
  layout.tsx           Root layout and metadata
  page.tsx             Chat interface
lib/
  ai/providers.ts      Provider integrations
  rate-limit.ts        Durable Redis-backed request limits
```

## Roadmap

- [ ] Hosted user authentication and account sessions
- [ ] Per-user daily/monthly quotas and billing controls
- [ ] Streaming responses
- [ ] Conversation history and user accounts
- [ ] File and document uploads
- [ ] Automated tests and deployment workflow
- [ ] Additional model providers

## Contributing

Issues and pull requests are welcome. Please never include credentials, private user data, or API keys in issues or commits.

## License

MIT. See [LICENSE](./LICENSE).
