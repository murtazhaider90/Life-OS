# PRIVACY

Life OS is local-first. Course material, plans, study sessions, activity observations and context records stay in the local SQLite database unless you explicitly configure an external integration.

Activity collectors deliberately exclude window titles, keystrokes, clipboard data, screenshots, page contents, URL paths and query strings. Browser telemetry stores hostname only. Raw activity retention defaults to 45 days.

Sleep, training and meal data is opt-in. Manual values are labelled `USER_ESTIMATE`; non-manual integrations are labelled `EXTERNAL_SOURCE`. Sleep/state gaps are not interpreted as normality. Context records have explicit delete endpoints.

## Voice assistant

The side assistant does not persist raw conversation transcripts. Accepted commands are converted into the same structured task/calendar/state/context records used by the rest of Life OS.

Browser microphone recognition is not automatically equivalent to local processing. The UI prefers on-device recognition when the browser exposes it. Otherwise it warns that the browser may use an external speech-recognition service and requires a one-time browser-local consent before starting voice recognition. Typed input is always available.

The optional spoken-reply feature uses the browser/operating-system speech-synthesis interface and is off by default.

AdGuard integration sends only the rule-management requests needed to your configured AdGuard Home instance. Credentials remain environment-only.

No current component performs continuous microphone recording, continuous webcam capture, private-message ingestion, password collection or silent network blocking.
