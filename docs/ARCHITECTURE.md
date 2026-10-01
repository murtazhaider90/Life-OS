# ARCHITECTURE

## Phase 1 shape

```text
Browser
  |
FastAPI application
  |-- deterministic planner
  |-- document ingestion + local FTS retrieval
  |-- study/task/calendar APIs
  |-- provenance boundary
  |-- AIProvider abstraction (optional, unconfigured)
  |
SQLite (WAL + foreign keys + FTS5)
```

The planner, date arithmetic, conflict checking, validation, persistence and security decisions are normal software. LLMs are reserved for future interpretation, tutoring, explanation and evidence-grounded reasoning.

## Why this stack

Python/FastAPI keeps AI/data work close to the application without requiring a heavy service topology. SQLite is appropriate for one person, cheap to back up, runs on a Raspberry Pi, and can later migrate to PostgreSQL if concurrency or scale demands it. FTS5 supplies a zero-cost local retrieval baseline before any embedding service is introduced.

## Evolution

Phase 2 can add local activity collectors as separate processes writing aggregated events. Phase 3 can add weekly planning and behavioral hypotheses. Phase 4 can integrate AdGuard/device filtering through explicit adapters. Phase 5 can add sleep/training/meal sources. Optional CV and the Architect Agent remain isolated later phases.


## Phase 2 telemetry boundary

Desktop/browser collectors emit minimal observation samples to `/api/activity/events/bulk`. Raw events remain separate from `activity_labels`, which are deterministic outputs of explicit user rules. Study analytics reads both layers but does not convert labels into personality claims. Raw telemetry has configurable retention; state inputs and study-session summaries are retained separately.
