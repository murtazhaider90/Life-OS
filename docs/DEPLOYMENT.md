# DEPLOYMENT

Development runs on localhost with Uvicorn and SQLite. Raspberry Pi deployment should use a dedicated OS account, a systemd service, regular encrypted backups and a reverse proxy only if LAN access is required. Do not expose the service to the public internet in Phase 1.
