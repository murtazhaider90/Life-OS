# Phase 1 architecture proposal

## Repository inspection result

No existing Life OS repository was present in the mounted workspace, and no matching repository was found among the connected GitHub repositories. Therefore this implementation starts as a new isolated local repository/branch rather than modifying unrelated projects.

## Phase 1 boundaries

Implement now: local access control, provenance-aware SQLite database, tasks, calendar, daily deterministic planner, study sessions, syllabus/document ingestion, local retrieval, explainable plan evidence, tests and core architecture/security/privacy documentation.

Defer: passive computer tracking, distraction classification, adaptive behavioral hypotheses, DNS filtering, sleep/wearable integrations, webcam/CV and autonomous code modification.

## Key decisions

- FastAPI + Python: one language for API, planning, RAG and future analytics/AI adapters.
- SQLite + WAL + FTS5: local, cheap, Raspberry-Pi-friendly, easy to back up, no server dependency for a single user.
- Server-rendered/lightweight browser UI first: avoids unnecessary frontend complexity in the foundation.
- Provider-neutral `AIProvider`: deterministic features run without AI credentials; vendor integrations can be added later.
- Provenance is a first-class table and source fields exist on user-facing operational records.
- Planner never asks an LLM to do arithmetic or conflict detection.
