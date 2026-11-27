# NILcenter experiment and permission MVP

## Implemented

The Python SDK now includes a local experiment metadata store and an
application-level capability-grant primitive.

### Experiment store

- Creates UUID-addressed experiment records.
- Tracks laboratory, hypothesis, tags, metadata, lifecycle status and UTC timestamps.
- Writes JSON through a same-directory temporary file, flushes it and atomically
  replaces the target.
- Rejects non-JSON metadata and malformed existing stores rather than silently
  overwriting them.
- Uses a process-local re-entrant lock.

The JSON store is intended for a single-user local prototype. It is not a
multi-process database, distributed store, encrypted vault or audit-grade
record system. Research datasets should be stored separately and referenced by
stable identifiers and checksums.

### Capability broker

- Denies by default.
- Requires an explicit approval flag before issuing a grant.
- Binds each grant to an exact subject, capability and resource.
- Enforces a bounded TTL and supports revocation.

**Security boundary:** this broker is an in-process policy primitive. It does
not enforce Linux permissions, isolate processes, restrict network access or
sandbox Python. It must not be used as the sole security control for executing
untrusted code. Production execution requires an independently reviewed OS
broker and sandbox backend.

## Next implementation gates

1. Add multi-process-safe persistence or move to SQLite with transactions.
2. Add experiment event history and content hashes for artifacts.
3. Implement an OS-facing permission service with authenticated IPC.
4. Integrate a disposable sandbox backend with filesystem, network, CPU,
   memory and process limits.
5. Perform threat modelling and adversarial tests before enabling tool execution.
