# Phase 3 — Planning intelligence

Phase 3 turns the Phase 1/2 data into deterministic weekly planning and evidence-backed descriptive insights.

## Weekly planning

`weekly_plans` are versioned. Generating or replanning a week supersedes the previous active version rather than mutating history.

The scheduler:
- respects hard calendar commitments;
- schedules only in verified free windows;
- splits large tasks into bounded work blocks;
- gives deadline pressure first priority;
- uses weak-topic evidence to break otherwise comparable scheduling ties;
- subtracts completed study-session minutes from remaining task duration during replanning;
- exposes capacity shortfall instead of pretending all work fits.

## Minimum viable week

A task enters the minimum viable week when at least one of these applies:
- it is due before the end of the week;
- it is the highest-ranked priority >=4 task for a module/general bucket;
- it maps to a topic currently classed `weak` and the task priority is >=3.

If none apply, the highest-ranked pending task is included so the minimum viable week is never empty when work exists.

This is a planning policy, not a measure of personal worth or effort.

## Weak-topic detection

Topic status uses recorded `study_attempts` only. Current transparent heuristics:
- `insufficient_evidence`: fewer than 2 attempts and fewer than 5 scored questions;
- `weak`: recorded accuracy <70% or mean confidence <=2/5;
- `requires_retrieval`: enough evidence exists and the last attempt was at least 7 days ago;
- `developing`: accuracy <85% or mean confidence <=3/5;
- `stable`: none of the above.

These thresholds are internal planning heuristics, not validated mastery scores.

## Dynamic replanning

A replan creates a new weekly-plan version from the requested `as_of` timestamp. Missed blocks are reported explicitly. Overdue work remains schedulable; a past deadline is treated as urgency, not as an impossible scheduling cutoff.

## Weekly review

The weekly review includes academic, behavioral, planning, and physical/context sections. Missing Phase 5 signals are returned as unavailable instead of inferred.

Music comparisons require at least 3 rated sessions with music on and 3 with music off. Results are observational and do not claim causation. Numeric inference confidence is a documented internal evidence heuristic, not a scientific probability.
