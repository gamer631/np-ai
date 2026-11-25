import test from "node:test";
import assert from "node:assert/strict";
import { generateReply, streamReply } from "../lib/ai/providers.ts";

const originalKeys = {
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
  GOOGLE_API_KEY: process.env.GOOGLE_API_KEY,
};

test("OpenAI adapter sends server key and extracts assistant text", async (t) => {
  process.env.OPENAI_API_KEY = "test-openai-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.equal(url, "https://api.openai.com/v1/chat/completions");
    assert.equal(init.headers.Authorization, "Bearer test-openai-key");
    const body = JSON.parse(init.body);
    assert.equal(body.model, "gpt-4o-mini");
    assert.equal(body.messages[0].content, "Hello");
    assert.ok(init.signal);
    return new Response(JSON.stringify({ choices: [{ message: { content: "Namaste" } }] }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });

  assert.equal(await generateReply("openai", "gpt-4o-mini", [{ role: "user", content: "Hello" }]), "Namaste");
});

test("Anthropic adapter extracts text blocks and sends its key in a header", async (t) => {
  process.env.ANTHROPIC_API_KEY = "test-anthropic-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (_url, init) => {
    assert.equal(init.headers["x-api-key"], "test-anthropic-key");
    assert.equal(init.headers["anthropic-version"], "2023-06-01");
    return new Response(JSON.stringify({
      content: [{ type: "text", text: "Hello" }, { type: "tool_use", id: "ignored" }, { type: "text", text: " Nepal" }],
    }), { status: 200 });
  });

  assert.equal(await generateReply("anthropic", "claude-sonnet-4-20250514", [{ role: "user", content: "Hi" }]), "Hello\n Nepal");
});

test("Google adapter sends API key in header and maps assistant role", async (t) => {
  process.env.GOOGLE_API_KEY = "test-google-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.match(String(url), /gemini-2\.5-flash:generateContent$/);
    assert.equal(init.headers["x-goog-api-key"], "test-google-key");
    const body = JSON.parse(init.body);
    assert.equal(body.contents[0].role, "model");
    assert.equal(body.contents[1].role, "user");
    return new Response(JSON.stringify({
      candidates: [{ content: { parts: [{ text: "Hello" }, { text: " from Gemini" }] } }],
    }), { status: 200 });
  });

  assert.equal(await generateReply("google", "gemini-2.5-flash", [
    { role: "assistant", content: "Earlier answer" },
    { role: "user", content: "Continue" },
  ]), "Hello from Gemini");
});

test("provider errors do not leak upstream response bodies", async (t) => {
  process.env.OPENAI_API_KEY = "test-openai-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async () => new Response(
    JSON.stringify({ error: { message: "private upstream diagnostic and key material" } }),
    { status: 401 },
  ));

  await assert.rejects(
    generateReply("openai", "gpt-4o-mini", [{ role: "user", content: "Hello" }]),
    (error) => {
      assert.equal(error.message, "AI provider request failed.");
      assert.equal(error.message.includes("private upstream"), false);
      return true;
    },
  );
});

test("malformed successful provider payload returns a safe empty-response fallback", async (t) => {
  process.env.OPENAI_API_KEY = "test-openai-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async () => new Response(JSON.stringify({ choices: [] }), { status: 200 }));

  assert.equal(
    await generateReply("openai", "gpt-4o-mini", [{ role: "user", content: "Hello" }]),
    "The model returned an empty response.",
  );
});

function restoreKeys() {
  for (const [key, value] of Object.entries(originalKeys)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
}


test("OpenAI streaming adapter emits text deltas and ignores the terminal marker", async (t) => {
  process.env.OPENAI_API_KEY = "test-openai-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.equal(url, "https://api.openai.com/v1/chat/completions");
    assert.equal(JSON.parse(init.body).stream, true);
    return new Response(
      'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\ndata: {"choices":[{"delta":{"content":" Nepal"}}]}\n\ndata: [DONE]\n\n',
      { status: 200, headers: { "content-type": "text/event-stream" } },
    );
  });
  assert.equal(await collect(streamReply("openai", "gpt-4o-mini", [{ role: "user", content: "Hi" }])), "Hello Nepal");
});

test("Anthropic streaming adapter emits only text delta events", async (t) => {
  process.env.ANTHROPIC_API_KEY = "test-anthropic-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (_url, init) => {
    assert.equal(JSON.parse(init.body).stream, true);
    return new Response(
      'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Namaste"}}\n\nevent: message_stop\ndata: {"type":"message_stop"}\n\n',
      { status: 200, headers: { "content-type": "text/event-stream" } },
    );
  });
  assert.equal(await collect(streamReply("anthropic", "claude-sonnet-4-20250514", [{ role: "user", content: "Hi" }])), "Namaste");
});

test("Google streaming adapter maps candidate text parts", async (t) => {
  process.env.GOOGLE_API_KEY = "test-google-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async (url, init) => {
    assert.match(String(url), /:streamGenerateContent\?alt=sse$/);
    assert.equal(init.headers["x-goog-api-key"], "test-google-key");
    return new Response(
      'data: {"candidates":[{"content":{"parts":[{"text":"Jai "},{"text":"Nepal"}]}}]}\n\n',
      { status: 200, headers: { "content-type": "text/event-stream" } },
    );
  });
  assert.equal(await collect(streamReply("google", "gemini-2.5-flash", [{ role: "user", content: "Hi" }])), "Jai Nepal");
});

test("streaming provider errors are redacted", async (t) => {
  process.env.OPENAI_API_KEY = "test-openai-key";
  t.after(() => restoreKeys());
  t.mock.method(globalThis, "fetch", async () => new Response(
    JSON.stringify({ error: { message: "private upstream stream error" } }),
    { status: 429 },
  ));
  await assert.rejects(
    collect(streamReply("openai", "gpt-4o-mini", [{ role: "user", content: "Hi" }])),
    (error) => error.message === "AI provider request failed.",
  );
});

async function collect(stream) {
  let output = "";
  for await (const chunk of stream) output += chunk;
  return output;
}
