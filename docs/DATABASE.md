# DATABASE

SQLite uses foreign keys and WAL mode.

Core tables:
- `evidence_records`: provenance category, source, source reference, value JSON, optional confidence and observation time.
- `tasks`, `calendar_events`, `study_sessions`, `plan_blocks`.
- `course_documents`, `course_chunks`, `course_chunks_fts`.
- `activity_events`, `activity_rules`, `activity_labels`, `user_state_inputs`.
- `study_attempts`, `weekly_plans`, `weekly_plan_blocks`, `inferences`.

Phase 4/5 context/intervention tables:
- `sleep_records`: explicit start/end, optional quality, source and provenance.
- `training_records`: start, duration, optional intensity/modality, source and provenance.
- `meal_records`: timestamp/type/optional size and notes; no nutritional-quality inference.
- `focus_domain_rules`: user-selected focus domains plus an `adguard_rule_owned` flag so Life OS never removes a pre-existing matching user rule.
- `intervention_events`: focus-mode activation/release/expiry audit trail.

New Phase 4/5 data uses new tables, so existing Phase 3 SQLite databases are upgraded by normal `create_all` table creation without rewriting existing rows.
