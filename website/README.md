# NIL.ai Company Website

Standalone public company website for Nepal Innovation Labs. This app is deliberately isolated from the NP.ai product application.

## Requirements

- Node.js 20.9+
- npm

## Configuration

Copy `.env.example` to `.env.local`. Set `NEXT_PUBLIC_SITE_URL` only after verifying the production domain and DNS. Without it, canonical metadata URLs and sitemap entries are intentionally omitted.

## Run locally

```bash
cd website
npm install
npm run dev
```

Open http://localhost:3000.

## Checks

```bash
npm run typecheck
npm run lint
npm run build
```

A lockfile should be generated and committed after a clean install in the intended Node/npm environment.

## Notes

- The site uses the NIL.ai research-laboratory visual direction.
- Product links currently point to the existing NP.ai GitHub repository.
- The domain configured in metadata is a placeholder until ownership and DNS are verified.
- Do not add fabricated customer logos, partnerships, research results or performance claims.
- Review content, accessibility and security before production deployment.
