# NP.ai

**Think beyond.** NP.ai is an open-source, multi-provider AI chat workspace.

> This project is an AI application, not a foundation model. It connects to model providers using API keys supplied by the person running the app.

## Features

- Clean, responsive chat interface
- Choose between OpenAI, Anthropic Claude, and Google Gemini
- Provider calls run on the server; API keys are never sent to the browser
- Simple provider adapter that can be extended with more models

## Requirements

- Node.js 20.9 or newer
- An API key from at least one supported provider

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

Model availability and pricing can change. Update the model IDs in `app/page.tsx` when you want to use different models.

## Project structure

```
app/
  api/chat/route.ts    Server-side chat endpoint
  globals.css          Application styles
  layout.tsx           Root layout and metadata
  page.tsx             Chat interface
lib/ai/providers.ts    Provider integrations
```

## Roadmap

- [ ] Streaming responses
- [ ] Conversation history and user accounts
- [ ] File and document uploads
- [ ] Usage limits and cost controls
- [ ] Additional model providers
- [ ] Automated tests and deployment workflow

## Contributing

Issues and pull requests are welcome. Please never include credentials, private user data, or API keys in issues or commits.

## License

MIT. See [LICENSE](./LICENSE).
