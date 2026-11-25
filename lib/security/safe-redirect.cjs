"use strict";

const BASE_ORIGIN = "https://np-ai.invalid";

function safeInternalPath(value) {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return "/";
  }

  try {
    const parsed = new URL(value, BASE_ORIGIN);
    if (parsed.origin !== BASE_ORIGIN) return "/";
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return "/";
  }
}

module.exports = { safeInternalPath };
