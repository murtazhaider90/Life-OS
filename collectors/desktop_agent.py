"""Privacy-minimal foreground-app sampler for the local Life OS.

Collects application/process name and optional idle seconds. It deliberately does not
capture window titles, keystrokes, screenshots, clipboard data, or document contents.
"""
from __future__ import annotations

import ctypes
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

API_URL = os.environ.get("LIFE_OS_ACTIVITY_URL", "http://127.0.0.1:8000/api/activity/events/bulk")
TIMEZONE = os.environ.get("LIFE_OS_TIMEZONE", "Europe/London")
SAMPLE_SECONDS = max(5, int(os.environ.get("LIFE_OS_ACTIVITY_SAMPLE_SECONDS", "15")))
DEVICE_FILE = Path.home() / ".life_os_device_id"


def device_id() -> str:
    if DEVICE_FILE.exists():
        return DEVICE_FILE.read_text().strip()
    value = str(uuid.uuid4())
    DEVICE_FILE.write_text(value)
    return value


def foreground_application() -> str | None:
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output([
                "osascript", "-e",
                'tell application "System Events" to get name of first application process whose frontmost is true',
            ], text=True, timeout=2)
            return out.strip() or None
        if system == "Linux":
            pid = subprocess.check_output(["xdotool", "getactivewindow", "getwindowpid"], text=True, timeout=2).strip()
            return Path(f"/proc/{pid}/comm").read_text().strip() or None
        if system == "Windows":
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            hwnd = user32.GetForegroundWindow()
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            handle = kernel32.OpenProcess(0x1000, False, pid.value)
            if not handle:
                return None
            try:
                size = ctypes.c_ulong(32768)
                buf = ctypes.create_unicode_buffer(size.value)
                if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                    return os.path.basename(buf.value)
            finally:
                kernel32.CloseHandle(handle)
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def idle_seconds() -> int | None:
    system = platform.system()
    try:
        if system == "Linux":
            out = subprocess.check_output(["xprintidle"], text=True, timeout=2)
            return int(out.strip()) // 1000
        if system == "Windows":
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(info)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                elapsed_ms = ctypes.windll.kernel32.GetTickCount() - info.dwTime
                return max(0, int(elapsed_ms // 1000))
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def send_sample(app: str | None, idle: int | None) -> None:
    observed = datetime.now(ZoneInfo(TIMEZONE))
    payload = {
        "events": [{
            "device_id": device_id(),
            "kind": "app_sample",
            "occurred_at": observed.isoformat(),
            "duration_seconds": SAMPLE_SECONDS,
            "application": app,
            "idle_seconds": idle,
            "source": "desktop_agent",
            "source_event_id": f"{device_id()}:{int(observed.timestamp())}",
        }]
    }
    req = Request(API_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=5) as response:
        response.read()


def main() -> int:
    print(f"Life OS desktop activity agent: sampling every {SAMPLE_SECONDS}s; no window titles/screenshots/keystrokes are collected.")
    while True:
        try:
            send_sample(foreground_application(), idle_seconds())
        except Exception as exc:  # keep local collector resilient; server remains source of truth
            print(f"activity sample failed: {exc}", file=sys.stderr)
        time.sleep(SAMPLE_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
