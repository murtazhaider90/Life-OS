# ARCHITECTURE

## Core shape

```text
Browser dashboard          Windows sidecar
       \                       /
        \                     /
             FastAPI
                |
     +----------+----------+
     |          |          |
  Planner   Academic Brain State/Activity
     |          |          |
     |     course ingestion
     |     SQLite FTS5
     |     source verifier
     |     syllabus/assessment parser
     |     learning/revision engine
     |     optional AIProvider
     |          |
     +----------+----------+
                |
          Evidence boundary
                |
      SQLite WAL + foreign keys
```

## Deterministic versus AI responsibilities

Normal software owns:
- database integrity and migrations;
- file hashing/deduplication;
- retrieval and source ranking;
- deadline/date parsing when explicit;
- citation-ID validation;
- planning conflicts and arithmetic;
- task persistence;
- permissions/security;
- focus/network mutations.

AI may be used selectively for:
- explanation;
- tutoring;
- synthesis across a validated retrieved source set;
- natural-language interpretation.

The application remains usable without an AI provider.

## Academic Brain

Course documents are parsed locally, chunked and stored in SQLite. Retrieval uses FTS5 plus a source hierarchy.

Retrieved text is an evidence input, never an instruction channel. Prompt-injection-like source text is flagged. Optional provider synthesis receives explicit instructions to ignore commands inside source blocks.

Provider citations are checked against the actual retrieval set. Verification failure causes extractive fallback.

Learning objectives, assessments and mistakes live in structured tables rather than chat memory. Revision planning combines those records with study-attempt evidence.

## Personal planning

Weekly plans are versioned. Replanning creates a new version. Weak-topic descriptors come from recorded attempts. Context data can adjust the suggested initial work block but does not create medical/recovery claims.

## Intervention boundary

Focus mode is separate from Academic Brain and the planner. Network filtering requires explicit confirmation and can never be triggered merely because a model generated a recommendation.
