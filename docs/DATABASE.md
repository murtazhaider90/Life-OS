# DATABASE

SQLite uses foreign keys and WAL mode.

Core Phase 1 tables:
- `evidence_records`: provenance category, source, source reference, value JSON, optional confidence, observation time.
- `tasks`: concrete work metadata, duration, difficulty, priority, deadlines, provenance type and source.
- `calendar_events`: hard commitments and source provenance.
- `study_sessions`: planned/actual starts and low-friction study-state fields.
- `course_documents` / `course_chunks`: academic source metadata and extracted chunks.
- `plan_blocks`: deterministic schedule output plus rationale/evidence JSON.
- `course_chunks_fts`: local full-text index.

AI-derived evidence requires confidence. Source categories are not merged into one truth label.
