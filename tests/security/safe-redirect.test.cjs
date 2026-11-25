"use strict";

/* eslint-disable @typescript-eslint/no-require-imports -- Node.js test runner uses CommonJS. */

const test = require("node:test");
const assert = require("node:assert/strict");
const { safeInternalPath } = require("../../lib/security/safe-redirect.cjs");

test("allows root-relative application paths", () => {
  assert.equal(safeInternalPath("/"), "/");
  assert.equal(safeInternalPath("/dashboard?tab=usage#latest"), "/dashboard?tab=usage#latest");
});

test("rejects absolute and protocol-relative external destinations", () => {
  assert.equal(safeInternalPath("https://attacker.example/"), "/");
  assert.equal(safeInternalPath("//attacker.example/"), "/");
  assert.equal(safeInternalPath("///attacker.example/"), "/");
});

test("rejects backslash-based redirect forms", () => {
  assert.equal(safeInternalPath("\\\\attacker.example"), "/");
  assert.equal(safeInternalPath("/\\\\attacker.example"), "/");
});

test("rejects non-path and malformed values", () => {
  assert.equal(safeInternalPath("javascript:alert(1)"), "/");
  assert.equal(safeInternalPath(""), "/");
  assert.equal(safeInternalPath(null), "/");
  assert.equal(safeInternalPath({}), "/");
});
