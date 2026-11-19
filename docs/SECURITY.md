# SECURITY

- Default bind address is `127.0.0.1`.
- Loopback requests are accepted for the local dashboard.
- Non-loopback API access requires `LIFE_OS_API_TOKEN`.
- Uploaded course material is parsed locally.
- File type and upload size are constrained.
- Raw passwords/credentials are not stored in SQLite.

## AdGuard Home

AdGuard credentials are read from `.env` / environment variables only. Life OS does not expose the password through its status endpoint.

Any network-rule mutation requires an explicit confirmed API/UI action. Applying focus mode first reads existing AdGuard user rules, preserves them, and records which rules Life OS actually owns. Release/expiry removes only owned rules.

The background expiry loop runs only when AdGuard settings are configured. AdGuard request failures are isolated and cannot crash the Life OS server.
