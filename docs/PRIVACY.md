# PRIVACY

Phase 1 is local-first. Course material, planning data and study sessions remain in the local SQLite database. There is no configured cloud AI provider and no screenshot/webcam capture.

Before adding telemetry, implement configurable retention and aggregation so raw activity can be deleted while useful summaries remain. Never collect passwords, private-message contents, continuous webcam footage or unnecessary screenshots.


Phase 2 collectors deliberately exclude window titles, keystrokes, clipboard data, screenshots, page contents, URL paths and query strings. Browser telemetry stores hostname only. Raw activity retention defaults to 45 days and is configurable.
