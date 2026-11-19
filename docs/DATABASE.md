# DATABASE

SQLite uses foreign keys and WAL mode.

Core planning/learning tables:
- `evidence_records`
- `tasks`
- `calendar_events`
- `study_sessions`
- `plan_blocks`
- `weekly_plans`
- `weekly_plan_blocks`
- `study_attempts`
- `inferences`

Course knowledge:
- `course_documents`: document-level module/week/topic/type/source/year/filename/hash metadata.
- `course_chunks`: source-linked text chunks with page/slide metadata.
- `course_chunks_fts`: local FTS5 search index.
- `learning_objectives`: explicit extracted objectives linked back to document/chunk/page.
- `assessments`: explicit assessment metadata and available criteria/source references.
- `mistake_records`: structured learning mistakes and resolution state.

Behavior/context:
- `activity_events`, `activity_rules`, `activity_labels`, `user_state_inputs`
- `sleep_records`, `training_records`, `meal_records`
- `focus_domain_rules`, `intervention_events`

New Academic Brain structures are additive tables created with SQLAlchemy `create_all`; existing personal data is not rewritten.

Important provenance rules:
- uploaded course material and extracted explicit academic structure: `EXTERNAL_SOURCE`;
- manually entered assessments: `USER_ESTIMATE`;
- automatically created revision/coursework tasks: `AI_RECOMMENDATION`;
- recorded attempts/mistakes: observations unless explicitly sourced otherwise.
