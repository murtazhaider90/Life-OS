# SECURITY

- Default bind address is `127.0.0.1`.
- Loopback requests are accepted for the local dashboard.
- Non-loopback API access requires `LIFE_OS_API_TOKEN`.
- Course material is parsed locally before retrieval.
- File types and upload size are constrained.
- Duplicate documents are detected by SHA-256.
- Credentials are not stored in SQLite.

## Academic RAG security

Uploaded documents are untrusted content.

Academic Brain:
- never treats retrieved document text as system/developer instructions;
- flags common prompt-injection-like phrases;
- excludes flagged instruction-like sentences from extractive answers;
- tells an optional provider to ignore commands inside SOURCE blocks;
- validates provider source IDs against the retrieved source set;
- falls back to extractive mode when provider citation verification fails;
- exposes conflicting explicit source facts instead of silently resolving them.

General model knowledge is disabled by default for academic Q&A.

## AdGuard Home

Any network-rule mutation requires explicit confirmation. Existing user rules are preserved and Life OS tracks ownership of the exact rules it adds so release/expiry removes only owned rules.
