# NIL Run Manifest v0.1

A run manifest records explicit, portable experiment metadata for comparison and
reproducibility. The caller must provide metadata; NIL does not automatically
collect host environment details or secrets.

## Recorded fields

- schema version and UTC creation time
- experiment and job UUID
- optional code revision and runtime name/version
- optional random seed
- dependency name/version pairs
- input/output artifact paths, SHA-256 digests, and sizes
- JSON-compatible configuration

## Fingerprint

`RunManifest.fingerprint()` hashes canonical JSON (sorted keys, compact encoding,
finite numeric values only). Dependency and artifact ordering is normalized, so
equivalent manifests produce identical fingerprints. Fingerprints change when the
recorded configuration or metadata changes.

This is a metadata fingerprint, not proof that a run is deterministic. External
services, hardware, nondeterministic algorithms, unrecorded dependencies, and
runtime differences can affect results.
