import { createHmac } from "node:crypto";

const SHORT_WINDOW_SECONDS = 10 * 60;
const SHORT_WINDOW_LIMIT = 10;
const DAILY_WINDOW_SECONDS = 24 * 60 * 60;
const DAILY_WINDOW_LIMIT = 100;
const REDIS_TIMEOUT_MS = 2_000;

const RATE_LIMIT_SCRIPT = [
  "local shortCount = redis.call('INCR', KEYS[1])",
  "if shortCount == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end",
  "local dailyCount = redis.call('INCR', KEYS[2])",
  "if dailyCount == 1 then redis.call('EXPIRE', KEYS[2], ARGV[4]) end",
  "local shortTtl = redis.call('TTL', KEYS[1])",
  "local dailyTtl = redis.call('TTL', KEYS[2])",
  "if shortCount > tonumber(ARGV[1]) or dailyCount > tonumber(ARGV[3]) then",
  "  local retryAfter = 0",
  "  if shortCount > tonumber(ARGV[1]) then retryAfter = math.max(retryAfter, shortTtl) end",
  "  if dailyCount > tonumber(ARGV[3]) then retryAfter = math.max(retryAfter, dailyTtl) end",
  "  return {0, retryAfter, shortCount, dailyCount}",
  "end",
  "return {1, 0, shortCount, dailyCount}",
].join("\n");

export type ChatRateLimitResult =
  | { allowed: true; configured: boolean; limit: number; remaining: number }
  | { allowed: false; status: 429 | 503; retryAfter: number; limit: number; remaining: number };

function getClientAddress(request: Request): string | null {
  // These headers must be set/overwritten by the trusted ingress proxy.
  const address =
    request.headers.get("cf-connecting-ip") ||
    request.headers.get("x-real-ip") ||
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();

  return address && address.length <= 128 ? address : null;
}

function hashAddress(address: string, salt: string): string {
  return createHmac("sha256", salt).update(address).digest("hex");
}

export async function checkChatRateLimit(request: Request): Promise<ChatRateLimitResult> {
  const limit = SHORT_WINDOW_LIMIT;
  const redisUrl = process.env.UPSTASH_REDIS_REST_URL?.trim();
  const redisToken = process.env.UPSTASH_REDIS_REST_TOKEN?.trim();
  const salt = process.env.RATE_LIMIT_SALT?.trim();

  if (!redisUrl || !redisToken || !salt) {
    if (process.env.NODE_ENV === "production") {
      return { allowed: false, status: 503, retryAfter: 60, limit, remaining: 0 };
    }
    return { allowed: true, configured: false, limit, remaining: limit };
  }

  if (salt.length < 32) {
    throw new Error("Rate-limit salt must contain at least 32 characters.");
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(redisUrl);
  } catch {
    throw new Error("Rate-limit service configuration is invalid.");
  }
  if (parsedUrl.protocol !== "https:") {
    throw new Error("Rate-limit service must use HTTPS.");
  }

  const address = getClientAddress(request);
  if (!address) {
    // Do not silently place all unidentified clients in one shared production bucket.
    return { allowed: false, status: 503, retryAfter: 60, limit, remaining: 0 };
  }

  const identity = hashAddress(address, salt);
  const shortKey = `npai:chat:10m:${identity}`;
  const dailyKey = `npai:chat:24h:${identity}`;

  const response = await fetch(`${parsedUrl.origin}${parsedUrl.pathname.replace(/\/$/, "")}/pipeline`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${redisToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify([[
      "EVAL",
      RATE_LIMIT_SCRIPT,
      "2",
      shortKey,
      dailyKey,
      String(SHORT_WINDOW_LIMIT),
      String(SHORT_WINDOW_SECONDS),
      String(DAILY_WINDOW_LIMIT),
      String(DAILY_WINDOW_SECONDS),
    ]]),
    cache: "no-store",
    signal: AbortSignal.timeout(REDIS_TIMEOUT_MS),
  });

  if (!response.ok) throw new Error("Rate-limit service request failed.");

  const payload: unknown = await response.json();
  if (!Array.isArray(payload) || !payload[0] || typeof payload[0] !== "object") {
    throw new Error("Rate-limit service returned an invalid response.");
  }

  const result = (payload[0] as { result?: unknown; error?: unknown }).result;
  if (!Array.isArray(result) || result.length < 4) {
    throw new Error("Rate-limit service returned an invalid result.");
  }

  const allowed = Number(result[0]) === 1;
  const retryAfter = Math.max(1, Number(result[1]) || SHORT_WINDOW_SECONDS);
  const shortCount = Math.max(0, Number(result[2]) || 0);
  const dailyCount = Math.max(0, Number(result[3]) || 0);
  const remaining = Math.max(0, Math.min(SHORT_WINDOW_LIMIT - shortCount, DAILY_WINDOW_LIMIT - dailyCount));

  if (!allowed) {
    return { allowed: false, status: 429, retryAfter, limit, remaining };
  }

  return { allowed: true, configured: true, limit, remaining };
}
