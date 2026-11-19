from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from .client import LifeOSClient, LifeOSConnectionError


WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_SPACE = 0x20
VK_LWIN = 0x5B
VK_H = 0x48
KEYEVENTF_KEYUP = 0x0002
HOTKEY_ID = 0xB051
POLL_MS = 50
PROMPT_POLL_MS = 5 * 60 * 1000


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("lPrivate", wintypes.DWORD),
    ]


class SidecarPreferences:
    def __init__(self) -> None:
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LifeOS"
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "sidecar.json"
        self.data = {
            "proactive_prompts": True,
            "speak_replies": False,
            "voice_typing_acknowledged": False,
        }
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value
        try:
            self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except OSError:
            pass


class LifeOSSidecar:
    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("The Windows sidecar can only run on Windows.")

        self.client = LifeOSClient()
        self.preferences = SidecarPreferences()
        self.root = tk.Tk()
        self.root.title("Life OS Assistant")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.root.minsize(360, 520)

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.last_prompt_id: str | None = None
        self.server_online = False

        self._configure_geometry()
        self._build_ui()
        self._register_hotkey()

        self.root.after(300, self._poll_hotkey)
        self.root.after(600, self._initial_refresh)
        self.root.after(PROMPT_POLL_MS, self._poll_prompts)

    def _configure_geometry(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(430, max(360, screen_w // 4))
        height = max(620, screen_h - 80)
        height = min(height, screen_h - 20)
        x = screen_w - width - 12
        y = 10
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="Life OS Assistant", font=("Segoe UI", 15, "bold")).pack(side="left")
        self.status_label = ttk.Label(header, text="Connecting…")
        self.status_label.pack(side="right")

        ttk.Label(
            outer,
            text="Ctrl + Alt + Space shows/hides this panel from anywhere.",
            foreground="#666666",
        ).pack(fill="x", pady=(2, 10))

        self.prompt_frame = ttk.LabelFrame(outer, text="What I need from you", padding=8)
        self.prompt_label = ttk.Label(self.prompt_frame, text="", wraplength=370, justify="left")
        self.prompt_label.pack(fill="x")

        self.chat = tk.Text(
            outer,
            wrap="word",
            height=18,
            state="disabled",
            font=("Segoe UI", 10),
            relief="flat",
            padx=8,
            pady=8,
        )
        self.chat.pack(fill="both", expand=True, pady=(8, 8))
        self.chat.tag_configure("assistant", spacing1=4, spacing3=8)
        self.chat.tag_configure("user", justify="right", spacing1=4, spacing3=8)

        controls = ttk.Frame(outer)
        controls.pack(fill="x")

        self.input_var = tk.StringVar()
        self.entry = ttk.Entry(controls, textvariable=self.input_var)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda _event: self.send_current())

        self.mic_button = ttk.Button(controls, text="🎙 Talk", command=self.start_voice_typing)
        self.mic_button.pack(side="left", padx=(6, 0))

        ttk.Button(controls, text="Send", command=self.send_current).pack(side="left", padx=(6, 0))

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(8, 0))

        self.proactive_var = tk.BooleanVar(value=bool(self.preferences.get("proactive_prompts", True)))
        ttk.Checkbutton(
            options,
            text="Proactive prompts",
            variable=self.proactive_var,
            command=self._save_options,
        ).pack(side="left")

        self.speak_var = tk.BooleanVar(value=bool(self.preferences.get("speak_replies", False)))
        ttk.Checkbutton(
            options,
            text="Speak replies",
            variable=self.speak_var,
            command=self._save_options,
        ).pack(side="left", padx=(10, 0))

        footer = ttk.Frame(outer)
        footer.pack(fill="x", pady=(8, 0))
        ttk.Button(footer, text="Open dashboard", command=lambda: webbrowser.open(self.client.base_url)).pack(side="left")
        ttk.Button(footer, text="Hide", command=self.hide).pack(side="left", padx=(6, 0))
        ttk.Button(footer, text="Quit sidecar", command=self.quit).pack(side="right")

        ttk.Label(
            outer,
            text="Voice button uses Windows Voice Typing (Win+H). Life OS does not store raw chat transcripts.",
            foreground="#666666",
            wraplength=390,
            justify="left",
        ).pack(fill="x", pady=(8, 0))

    def _save_options(self) -> None:
        self.preferences.set("proactive_prompts", bool(self.proactive_var.get()))
        self.preferences.set("speak_replies", bool(self.speak_var.get()))

    def _register_hotkey(self) -> None:
        ok = self.user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_SPACE)
        if not ok:
            self._append(
                "assistant",
                "Global hotkey could not be registered. The sidecar still works from its window.",
            )

    def _poll_hotkey(self) -> None:
        msg = MSG()
        while self.user32.PeekMessageW(ctypes.byref(msg), None, WM_HOTKEY, WM_HOTKEY, PM_REMOVE):
            if msg.wParam == HOTKEY_ID:
                self.toggle()
        self.root.after(POLL_MS, self._poll_hotkey)

    def _initial_refresh(self) -> None:
        self._run_background(self._refresh_status, True)

    def _poll_prompts(self) -> None:
        self._run_background(self._refresh_status, False)
        self.root.after(PROMPT_POLL_MS, self._poll_prompts)

    def _refresh_status(self, initial: bool) -> None:
        try:
            health = self.client.health()
            status = self.client.assistant_status()
        except LifeOSConnectionError:
            self.root.after(0, self._set_offline)
            return

        questions = status.get("questions") or []
        prompt = questions[0] if questions else None
        self.root.after(0, lambda: self._set_online(health, prompt, initial))

    def _set_offline(self) -> None:
        self.server_online = False
        self.status_label.configure(text="Server offline")
        self.prompt_frame.pack_forget()

    def _set_online(self, health: dict, prompt: dict | None, initial: bool) -> None:
        self.server_online = True
        self.status_label.configure(text=f"v{health.get('version', '?')} · local")

        if not prompt:
            self.prompt_frame.pack_forget()
            return

        self.prompt_label.configure(
            text=f"{prompt.get('prompt', '')}\n\nWhy: {prompt.get('reason', '')}"
        )
        if not self.prompt_frame.winfo_ismapped():
            self.prompt_frame.pack(fill="x", pady=(0, 2), before=self.chat)

        prompt_id = str(prompt.get("id") or "")
        should_pop = (
            bool(self.proactive_var.get())
            and prompt_id
            and prompt_id != self.last_prompt_id
        )
        self.last_prompt_id = prompt_id
        if should_pop:
            self.show()
            self._append("assistant", prompt.get("prompt", "I need some information."))
            if self.speak_var.get():
                self._speak_async(prompt.get("prompt", ""))
        elif initial and self.root.state() != "withdrawn":
            self.entry.focus_set()

    def _append(self, role: str, text: str) -> None:
        self.chat.configure(state="normal")
        prefix = "Life OS: " if role == "assistant" else "You: "
        self.chat.insert("end", prefix + text.strip() + "\n", role)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def send_current(self) -> None:
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self._append("user", text)
        self.entry.configure(state="disabled")
        self.mic_button.configure(state="disabled")
        self._run_background(self._send_message, text)

    def _send_message(self, text: str) -> None:
        try:
            result = self.client.send_message(text)
            reply = str(result.get("reply") or "Done.")
        except (LifeOSConnectionError, ValueError) as exc:
            reply = f"I couldn't reach Life OS safely: {exc}"
        self.root.after(0, lambda: self._finish_reply(reply))

    def _finish_reply(self, reply: str) -> None:
        self._append("assistant", reply)
        self.entry.configure(state="normal")
        self.mic_button.configure(state="normal")
        self.entry.focus_set()
        if self.speak_var.get():
            self._speak_async(reply)
        self._run_background(self._refresh_status, False)

    def start_voice_typing(self) -> None:
        if not self.preferences.get("voice_typing_acknowledged", False):
            accepted = messagebox.askokcancel(
                "Windows Voice Typing",
                "This button opens Windows Voice Typing (Win+H). Depending on your Windows speech settings, Microsoft may process speech online.\n\nLife OS receives only the resulting text and does not store the raw assistant transcript. Continue?",
                parent=self.root,
            )
            if not accepted:
                return
            self.preferences.set("voice_typing_acknowledged", True)

        self.show()
        self.entry.focus_force()
        self.root.update_idletasks()
        self.root.after(150, self._send_win_h)

    def _send_win_h(self) -> None:
        self.user32.keybd_event(VK_LWIN, 0, 0, 0)
        self.user32.keybd_event(VK_H, 0, 0, 0)
        self.user32.keybd_event(VK_H, 0, KEYEVENTF_KEYUP, 0)
        self.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

    def _speak_async(self, text: str) -> None:
        if not text.strip():
            return

        def worker() -> None:
            escaped = text.replace("'", "''")
            command = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Rate = 0; "
                f"$s.Speak('{escaped}')"
            )
            encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
            try:
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=60,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except (OSError, subprocess.SubprocessError):
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _run_background(self, fn, *args) -> None:
        threading.Thread(target=fn, args=args, daemon=True).start()

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.entry.focus_force()

    def hide(self) -> None:
        self.root.withdraw()

    def toggle(self) -> None:
        if self.root.state() == "withdrawn":
            self.show()
        else:
            self.hide()

    def quit(self) -> None:
        try:
            self.user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if sys.platform != "win32":
        print("Life OS Windows sidecar requires Windows.", file=sys.stderr)
        return 1
    app = LifeOSSidecar()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
