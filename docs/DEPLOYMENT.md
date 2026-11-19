# DEPLOYMENT

Development runs on localhost with Uvicorn and SQLite.

## Windows local run

```powershell
cd "C:\Users\Murtaza Haider\Life-OS"
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Raspberry Pi / always-on host

Use a dedicated OS account, a systemd service, regular encrypted backups and a reverse proxy only if LAN access is required. Do not expose Life OS directly to the public internet.

If AdGuard Home is on the same LAN, configure its base URL and credentials through environment variables in the service unit/secret store. Do not commit those values to Git.

## CI

GitHub Actions runs the test suite and compile check on Python 3.11 and 3.14 for pull requests and on main.
