# API

FastAPI exposes interactive OpenAPI docs at `/docs`.

Primary endpoints:
- `GET/POST /api/tasks`
- `POST /api/tasks/{id}/complete`
- `GET/POST /api/calendar`
- `GET/POST /api/study-sessions`
- `POST /api/study-sessions/{id}/finish`
- `POST /api/plans/daily`
- `POST /api/plans/weekly`
- `GET /api/plans/weekly/active?week_start=YYYY-MM-DD`
- `POST /api/plans/weekly/replan`
- `GET/POST /api/learning/attempts`
- `GET /api/learning/topics`
- `GET /api/briefing/morning?brief_date=YYYY-MM-DD`
- `GET /api/reviews/weekly?week_start=YYYY-MM-DD`
- `POST /api/course/documents`
- `GET /api/course/search?q=...`
- `GET /api/evidence`
- `POST /api/activity/events/bulk`
- `GET /api/activity/events`
- `GET/POST /api/activity/rules`
- `POST /api/activity/rules/{id}/disable`
- `GET /api/activity/study-sessions/{id}/metrics`
- `POST /api/activity/retention/prune`
- `GET/POST /api/state-inputs`
