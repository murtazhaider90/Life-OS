# Personal AI Life OS — Phase 3

A local-first, single-user system for evidence-based planning, academic retrieval, privacy-minimal behavioral tracking, and adaptive weekly planning.

## Current capabilities

- Provenance-aware evidence records (`FACT`, `OBSERVATION`, `USER_ESTIMATE`, `AI_INFERENCE`, `AI_RECOMMENDATION`, `EXTERNAL_SOURCE`).
- Concrete tasks with module/topic/objective/output/source metadata.
- Calendar events with duplicate detection and explicit source fields.
- Deterministic daily and weekly planning with calendar conflict checks and explainable evidence.
- Versioned dynamic replanning after missed work instead of blindly shifting every block forward.
- Minimum viable week marking based on due work, high-priority module work, and sufficiently evidenced weak topics.
- Study sessions plus recorded problem/practice attempts with accuracy, confidence, difficulty, and learning-objective metadata.
- Transparent weak-topic/retrieval heuristics with evidence counts and no scientific/medical framing.
- Morning briefing endpoint and dashboard next-action display.
- Weekly academic/behavioral/planning review with explicit missing-data reporting for Phase 5 context signals.
- Course PDF/TXT/Markdown ingestion, chunking, metadata, SHA-256 deduplication, and local SQLite FTS5 retrieval.
- Phase 2 minimal computer activity ingestion, explicit study/distraction rules, session start-latency/distraction metrics, and low-friction energy/focus inputs.
- Optional desktop foreground-app sampler and hostname-only browser extension under `collectors/`.
- Provider-neutral `AIProvider` interface; deterministic features require no AI vendor.
- Localhost-first access; bearer token required when not operating unauthenticated on loopback.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Interactive API documentation is at `/docs`.

## Evidence boundaries

Phase 3 still does not infer sleep, training recovery, meal effects, location context, or medical/psychological states. Unlabelled activity is never assumed to be distraction. Learning status is an internal planning heuristic based only on recorded attempts. Behavioral comparisons (for example, music on/off) require minimum sample counts, remain observational, and are stored as provisional/developing inferences rather than facts.
