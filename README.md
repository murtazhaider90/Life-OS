# Personal AI Life OS — Phase 1

A local-first, single-user foundation for evidence-based planning and academic retrieval.

## Current capabilities

- Provenance-aware evidence records (`FACT`, `OBSERVATION`, `USER_ESTIMATE`, `AI_INFERENCE`, `AI_RECOMMENDATION`, `EXTERNAL_SOURCE`).
- Tasks with module/topic/objective/output/source metadata.
- Calendar events with duplicate detection and explicit source fields.
- Deterministic daily planning that checks calendar conflicts and exposes its evidence.
- Basic study-session tracking, including focus/energy/difficulty/confusion/music fields.
- Course document ingestion for PDF/TXT/Markdown, chunking, metadata, SHA-256 deduplication and local SQLite FTS5 retrieval.
- Provider-neutral `AIProvider` interface; no vendor is required for deterministic features.
- Localhost-first access; bearer token required when not operating unauthenticated on loopback.
- Lightweight dashboard and API documentation at `/docs`.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

## Important limitation

This is Phase 1 infrastructure. It does **not** infer sleep, distraction, mood, readiness, or behavioral traits yet. It does not silently convert AI output into facts. AI model integration is intentionally behind an unconfigured provider interface until credentials/provider choices are supplied.
