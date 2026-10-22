# ARCHITECTURE

## Core shape

```text
Browser dashboard
  |
FastAPI application
  |-- deterministic daily/weekly planner
  |-- morning briefing + planning-load context
  |-- document ingestion + local FTS retrieval
  |-- study/learning/activity/context APIs
  |-- explicit focus intervention service
  |-- AdGuard Home adapter (optional)
  |-- provenance boundary
  |-- AIProvider abstraction (optional, unconfigured)
  |
SQLite (WAL + foreign keys + FTS5)
```

Date arithmetic, scheduling conflicts, database integrity, provenance, access control and network-rule mutations are normal software. LLMs are reserved for future interpretation/tutoring/explanation and may not silently own those deterministic decisions.

## Local-first data

SQLite remains the source of truth for one-user operation. Phase 2 collectors send only minimal app/domain observations. Phase 4/5 context records are explicit user/external-source records and are not scraped from unrelated private content.

## Planning intelligence

Weekly plans are versioned. Replanning creates a new version. Weak-topic descriptors come from recorded study attempts. The current-context service adds a separate short-term planning-load signal for the first study block; it does not rewrite historical facts or make medical/recovery claims.

## Intervention boundary

Focus mode is a separate service from the planner. A recommendation can be produced from explicitly-labelled distraction observations, but network blocking requires explicit confirmation. AdGuard Home credentials are environment-only. The adapter fetches the current user-rule list, preserves it, and tracks ownership of rules Life OS itself adds before removing anything.

## Evolution

Future work can add real wearable/calendar/device adapters, notification delivery, stronger migrations, and the optional Architect Agent. Those integrations should plug into the existing provenance/context boundaries rather than bypassing them.
