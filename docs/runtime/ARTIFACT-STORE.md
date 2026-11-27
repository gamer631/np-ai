# NIL Artifact Store v0.1

The SDK includes a local content-addressed artifact store.

- Blobs are addressed by SHA-256 and deduplicated.
- Writes use a temporary file and atomic replacement.
- Metadata is stored in SQLite.
- Reads verify both recorded size and content hash.
- Caller-provided maximum size bounds individual artifacts.
- Delete removes blob and metadata.

This is a local, single-host storage primitive only. It is not object storage,
multi-tenant isolation, backup, replication, or a cloud storage API.
