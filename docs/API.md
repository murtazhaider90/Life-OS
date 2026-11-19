# API

FastAPI exposes interactive OpenAPI docs at `/docs`.

## Academic Brain

Course material:
- `GET /api/course/documents`
- `POST /api/course/documents`
- `POST /api/course/documents/bulk`
- `DELETE /api/course/documents/{id}`
- `GET /api/course/search?q=...&module=...&topic=...`

Academic intelligence:
- `GET /api/academic/status`
- `GET /api/academic/modules`
- `POST /api/academic/ask`
- `POST /api/academic/documents/{id}/analyse`
- `GET /api/academic/objectives`
- `GET/POST /api/academic/assessments`
- `POST /api/academic/assessments/{id}/breakdown`
- `POST /api/academic/revision-plan`
- `POST /api/academic/quiz`
- `GET/POST /api/academic/mistakes`
- `POST /api/academic/mistakes/{id}/resolve`

Learning evidence:
- `GET/POST /api/learning/attempts`
- `GET /api/learning/topics`

## Planning and life context

- `GET/POST /api/tasks`
- `POST /api/tasks/{id}/complete`
- `GET/POST /api/calendar`
- `GET/POST /api/study-sessions`
- `POST /api/study-sessions/{id}/finish`
- `POST /api/plans/daily`
- `POST /api/plans/weekly`
- `GET /api/plans/weekly/active?week_start=YYYY-MM-DD`
- `POST /api/plans/weekly/replan`
- `GET /api/briefing/morning?brief_date=YYYY-MM-DD`
- `GET /api/reviews/weekly?week_start=YYYY-MM-DD`
- `GET/POST /api/state-inputs`
- `GET/POST /api/context/sleep`
- `GET/POST /api/context/training`
- `GET/POST /api/context/meals`
- `GET /api/context/summary`
- `GET /api/context/weekly?week_start=YYYY-MM-DD`

## Assistant

- `GET /api/assistant/status`
- `POST /api/assistant/message`

Raw assistant transcripts are not persisted.

## Activity and focus

- `POST /api/activity/events/bulk`
- `GET /api/activity/events`
- `GET/POST /api/activity/rules`
- `POST /api/activity/rules/{id}/disable`
- `GET /api/activity/study-sessions/{id}/metrics`
- `POST /api/activity/retention/prune`
- `GET/POST /api/focus/domains`
- `POST /api/focus/domains/{id}/disable`
- `GET /api/focus/status`
- `GET /api/focus/recommendation`
- `GET /api/focus/preview`
- `POST /api/focus/apply`
- `POST /api/focus/release`
