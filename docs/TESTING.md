# TESTING

Automated tests currently cover:
- daily and weekly calendar-conflict avoidance;
- weekly task splitting and minimum-viable marking;
- dynamic replanning/version history and missed-block reporting;
- capacity shortfall and overdue-task scheduling;
- weak-topic evidence thresholds and insufficient-evidence behavior;
- weak-topic scheduling tie-breaks;
- study-session ordering and timezone validation;
- explicit-rule-only activity classification and raw-event retention;
- local course retrieval;
- morning briefing next-action behavior;
- weekly-review music minimum sample size and observational wording.

Future phases must continue adding adversarial RAG tests, contradiction/retirement tests for longer-lived inferences, authentication/deletion tests, prompt-injection cases, integration tests for filtering, and sensor-failure tests for health/context sources.
