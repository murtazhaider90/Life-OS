# Personal AI Life OS — Windows sidecar milestone

A local-first, single-user system for evidence-based planning, academic retrieval, privacy-minimal behavioral tracking, context-aware scheduling, voice/text capture, and explicit focus interventions.

## What works now

- Provenance-aware tasks, calendar, study sessions, learning attempts, course-document retrieval, daily planning and versioned weekly planning.
- Dynamic replanning, weak-topic evidence, morning briefing, context-aware suggested work blocks, and weekly review.
- Browser dashboard with task/calendar/state/sleep/training/meal inputs.
- Browser side assistant with voice/text commands.
- **Windows always-on-top assistant sidecar** with a global **Ctrl + Alt + Space** show/hide hotkey.
- Windows-native voice typing launched from the sidecar with a one-time privacy warning.
- Optional spoken replies through Windows speech synthesis.
- Proactive missing-information prompts that use the existing deterministic assistant queue.
- One-click Windows launcher and desktop-shortcut installer.
- Optional AdGuard Home focus mode with explicit confirmation and owned-rule cleanup.
- GitHub CI on Python 3.11 and 3.14.

## Windows sidecar setup

After pulling this feature branch and installing the package, create the desktop shortcut once:

    powershell -ExecutionPolicy Bypass -File .\windows\install_shortcut.ps1

Then double-click **Life OS** on the desktop. The local server starts in the background and the sidecar opens.

Use:

    Ctrl + Alt + Space

from anywhere in Windows to show or hide the assistant.

The **Talk** button invokes Windows Voice Typing. Life OS receives the resulting text and does not persist the raw assistant transcript.

## Manual run

    cd "C:\Users\Murtaza Haider\Life-OS"
    .venv\Scripts\Activate.ps1
    python -m pip install -e ".[dev]"
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Then in a second terminal:

    cd "C:\Users\Murtaza Haider\Life-OS"
    .venv\Scripts\Activate.ps1
    python -m desktop.windows_sidecar

Open the full dashboard at http://127.0.0.1:8000.

## Evidence and privacy boundaries

The sidecar is only another client of the existing Life OS assistant API. Ambiguous commands fail closed instead of mutating data. Missing context remains missing. Windows voice typing is a separate speech-processing boundary and may use Microsoft's online speech recognition depending on Windows settings, so the sidecar warns before first use.
