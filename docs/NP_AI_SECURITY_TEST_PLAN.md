# NP.ai Security Test Plan

**Status:** Test plan. Tests are not yet evidence of passing security controls.

## Scope

The first release handles authenticated chat, conversation history, provider API calls and per-account usage quotas. Document upload and retrieval are future scope and require a separate threat model before implementation.

## Test accounts

Use two independently registered test users (A and B) in a non-production Supabase project. Never use real customer data or production credentials.

## Authorization and tenant isolation

- [ ] Unauthenticated requests to chat and conversation APIs return 401.
- [ ] Email confirmation callback rejects absolute, protocol-relative and backslash-based external redirect destinations.
- [ ] Callback codes are exchanged only through the configured Supabase Auth client.
- [ ] User A can read only A's conversations and messages.
- [ ] User B cannot read, update or delete A's conversations or messages by changing IDs.
- [ ] A foreign conversation ID is rejected before quota consumption and before any provider request.
- [ ] A user cannot insert a message whose user_id differs from the authenticated identity.
- [ ] RLS remains enabled on every user-owned table.
- [ ] Anonymous and authenticated users cannot read the usage ledger directly.
- [ ] The quota function derives identity from auth.uid() and rejects calls without a user identity.

## Input and resource limits

- [ ] Malformed JSON is rejected.
- [ ] Oversized streamed bodies are rejected without buffering the entire body.
- [ ] Unknown providers and provider/model mismatches are rejected.
- [ ] Unsupported roles, empty messages, excessive message counts and character limits are rejected.
- [ ] Provider timeouts return a bounded error and do not expose credentials or upstream response bodies.

## Quota behavior

- [ ] Concurrent requests cannot exceed the 10-per-10-minute limit.
- [ ] The 100-per-24-hour limit is enforced independently.
- [ ] Retry-After is positive and consistent with the next eligible request.
- [ ] Provider failures are accounted for consistently with documented product policy.
- [ ] A request rejected for foreign conversation ownership does not consume quota.

## Secrets and privacy

- [ ] Provider keys are only read in server-side code.
- [ ] No secrets appear in client bundles, logs, error messages, Git history or URLs.
- [ ] Responses containing account data use private, no-store caching.
- [ ] Logs do not contain full prompts, private messages or provider credentials.
- [ ] Environment examples contain placeholders only.

## Adversarial review

- [ ] Attempt IDOR against conversation and message endpoints using test accounts.
- [ ] Attempt quota race conditions with controlled concurrent requests.
- [ ] Attempt prompt injection in user messages and document content; verify content cannot change authorization or server policy.
- [ ] Verify no user-controlled value can select arbitrary provider endpoints or model identifiers.

## Evidence format

For each test, record the commit SHA, environment, test account roles, exact request, expected result, observed status/body, database state, provider-call count and timestamp. Redact tokens and personal data.

## Release gate

Do not call NP.ai production-ready until CI passes, the migration is applied and verified in a staging project, authorization tests pass with two users, quota tests pass under concurrency, and a human security review is complete.
