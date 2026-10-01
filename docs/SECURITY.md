# SECURITY

- Default bind address is `127.0.0.1`.
- Loopback requests are accepted for the local dashboard.
- Non-loopback API access requires `LIFE_OS_API_TOKEN`; configure a long random token before LAN exposure.
- Uploaded material is parsed locally; Phase 1 does not transmit it to an AI provider.
- File type and upload size are constrained.
- Raw credentials and passwords are not stored in the database.
- Future integrations must keep credentials in environment/secret storage, not evidence records.
