# Nepal Innovation Labs — NIL.ai

**Born in Nepal. Built for the world.**

Nepal Innovation Labs is an independent research and engineering initiative focused on useful, reliable artificial intelligence. NIL.ai is the company identity and public research-laboratory brand. NP.ai is its open-source multi-provider AI workspace.

## Ecosystem

- **NIL.ai website:** company identity, research directions, principles and project information — see [website/](./website/).
- **NP.ai:** multi-provider AI workspace using OpenAI, Anthropic and Google APIs — see the root application and [GitHub project](https://github.com/gamer631/np-ai).

## Repository layout

- `website/` — standalone Next.js company website for NIL.ai.
- `app/`, `lib/`, `supabase/` — NP.ai product application, provider adapters and database migration.
- `.github/workflows/` — independent CI pipelines for product, website and local database tests.

## Engineering principles

- Evidence before claims: CI, integration and production checks are recorded separately.
- Privacy by design: provider secrets stay server-side; Supabase row-level security protects user data.
- Secure defaults: bounded inputs, per-account usage controls, normalized provider errors and security headers.
- Reproducible builds: committed npm lockfiles and `npm ci` in CI.
- No invented proof: mock-provider tests are not live-provider verification; local database tests are not hosted-project verification.

## Development

For the NIL.ai website:

```bash
cd website
npm ci
npm run dev
```

For NP.ai:

```bash
npm ci
cp .env.example .env.local
# Configure Supabase URL/publishable key and at least one server-side provider key.
npm run dev
```

For local Supabase database tests, install Docker and the Supabase CLI, then run:

```bash
supabase start
supabase db reset
supabase test db
```

See [website README](./website/README.md) for website setup and the product README on the backend branch for detailed NP.ai configuration.

## Status

This repository contains active development work. Do not infer production readiness from a successful build. Hosted Supabase, email delivery, provider credentials, staging deployment, accessibility review, monitoring, privacy/legal review and production domain configuration must be verified in the owner's accounts before public launch.

## License

MIT. See [LICENSE](./LICENSE).
