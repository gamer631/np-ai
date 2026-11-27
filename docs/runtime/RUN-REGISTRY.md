# NIL Run Registry v0.1

The RunRegistry persists validated RunManifest snapshots in SQLite. Job UUID is the
primary key. Identical saves are idempotent; a conflicting manifest for an
existing job ID is rejected to protect provenance. Listing supports experiment
filters and bounded result counts.

The registry stores metadata only. It does not execute workloads or store artifact
bytes; artifact bytes belong in ArtifactStore and may be referenced by manifest
hashes. This is a local SQLite component, not a multi-node service.
