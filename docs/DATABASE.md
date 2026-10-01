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


Phase 2 tables:
- `activity_events`: raw minimal app/domain/idle samples with OBSERVATION provenance.
- `activity_rules`: user-authored deterministic classification rules.
- `activity_labels`: derived classification plus its rule/basis, separate from raw telemetry.
- `user_state_inputs`: timestamped low-friction USER_ESTIMATE signals.

Phase 3 tables:
- `study_attempts`: module/topic/objective practice evidence including optional scored counts, confidence and difficulty.
- `weekly_plans`: versioned weekly plan headers, scheduling policy parameters, required/scheduled minutes and capacity shortfall.
- `weekly_plan_blocks`: concrete task blocks with minimum-viable marker, rationale and evidence JSON.
- `inferences`: provisional/developing evidence-backed hypotheses with confidence, evidence count, contradictory evidence, date range and status.
