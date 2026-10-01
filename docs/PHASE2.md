# Phase 2 — Behavioral tracking

Phase 2 adds local, privacy-minimal behavioral telemetry without turning observations into judgments.

## Implemented

- `activity_events`: sampled foreground application or browser hostname, duration, optional idle seconds and device ID.
- `activity_rules`: explicit user-created rules that label an application/domain as `study`, `distraction`, or `neutral`.
- `activity_labels`: derived labels kept separate from raw observations, including the rule/basis that produced them.
- `user_state_inputs`: low-friction energy/focus/difficulty/confusion check-ins with `USER_ESTIMATE` provenance.
- Deterministic study-session metrics: start latency, explicitly-labelled distraction seconds, study-labelled seconds and neutral seconds.
- Configurable raw activity retention with deletion that leaves higher-value state/session data intact.
- Desktop collector for foreground application names and optional idle time. No window titles, keystrokes, screenshots, clipboard or file contents are captured.
- Optional Chromium extension that samples hostname only. URL paths, queries, titles and page contents are discarded.

## Important interpretation rule

Unlabelled activity is **not** treated as distraction. Labels come only from enabled user rules. This avoids silently classifying unfamiliar apps or websites as bad behavior.

## Collector support

- Windows: foreground executable and idle time via local Win32 APIs.
- macOS: frontmost application name via `System Events`.
- Linux/X11: foreground process via `xdotool` when installed; idle time via `xprintidle` when installed.

Collectors fail open: if a signal is unavailable, they send no invented value.
