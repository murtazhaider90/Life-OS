# Windows sidecar

The Windows sidecar turns the Life OS assistant into an always-on-top desktop companion instead of a browser-only panel.

## Behaviour

- Anchors to the right side of the screen and stays above normal windows.
- Global hotkey: **Ctrl + Alt + Space** toggles the sidecar from anywhere.
- Sends typed commands to the existing assistant API.
- Polls the missing-information queue and can pop up when a new high-priority question appears.
- Uses native Windows Voice Typing for speech-to-text.
- Optional spoken replies use Windows speech synthesis.
- Opens the full browser dashboard on demand.
- Closing the window hides it; use **Quit sidecar** to fully exit.

The assistant still uses the same deterministic mutation boundary as the browser version. Ambiguous requests do not create or change records.

## Voice typing

The Talk button focuses the assistant input then triggers the native **Win+H** voice-typing interface. Life OS itself receives only the resulting text.

Windows speech processing is a separate privacy boundary. The sidecar displays a one-time warning because Windows may use online speech recognition depending on the user's Windows speech settings.

Life OS does not continuously record the microphone and does not persist raw assistant chat transcripts.

## One-click startup

Once the branch is installed, run:

    powershell -ExecutionPolicy Bypass -File .\windows\install_shortcut.ps1

This creates a **Life OS** shortcut on the Windows desktop. Opening it checks the local server, starts it hidden when necessary, then launches the sidecar.

To stop a background server started by that launcher:

    powershell -ExecutionPolicy Bypass -File .\windows\stop_life_os.ps1

The stop script verifies that the stored PID belongs to the Life OS Uvicorn process before terminating it.

## Manual launch

Start the server:

    .venv\Scripts\Activate.ps1
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Then in another PowerShell window:

    .venv\Scripts\Activate.ps1
    python -m desktop.windows_sidecar
