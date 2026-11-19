# TESTING

The full suite currently passes on Python 3.11 and Python 3.14. A separate Windows CI job verifies the timezone database, desktop sidecar import and PowerShell launcher syntax.

Academic Brain coverage includes:
- correct local course retrieval;
- no-evidence academic questions;
- document/page source metadata;
- source hierarchy;
- conflicting assessment percentages;
- avoiding false conflicts between a date and a percentage;
- prompt-injection-like document content;
- optional-provider untrusted-source prompting;
- rejection of invented provider citation IDs;
- deterministic syllabus learning-objective extraction;
- explicit assessment date/weight extraction;
- coursework breakdown and AI_RECOMMENDATION provenance;
- weak-topic revision prioritization;
- idempotent revision task creation;
- source-backed quiz generation;
- DOCX and PPTX text extraction;
- document content deduplication;
- Academic Brain side-assistant commands.

The wider suite also covers:
- daily/weekly conflict avoidance;
- capacity shortfall and replanning;
- activity classification/retention;
- context planning load;
- focus-rule ownership/expiry;
- voice/assistant command safety;
- Windows sidecar HTTP behavior.

Known future test areas include richer multi-document contradiction semantics, OCR/scanned-document fixtures, visual slide/diagram understanding and integration tests against real optional AI-provider endpoints.
