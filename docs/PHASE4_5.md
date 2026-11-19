# Phase 4/5 — Context and interventions

This milestone adds optional context signals and explicit, reversible focus interventions.

## Context records

Life OS can now store:
- sleep start/end and optional self-rated quality;
- training time, duration, modality, and optional intensity;
- meal timestamps/type/size as context only;
- existing energy/focus check-ins.

Manual entries are `USER_ESTIMATE`. Non-manual sources are labelled `EXTERNAL_SOURCE`. The current-context service never silently treats missing sleep/state information as normal: when both primary signals are absent, planning load is `unknown_capacity`.

## Planning-load heuristic

The planning-load signal is deterministic and deliberately modest:
- recorded sleep under 6h: +2 load points;
- recorded sleep 6–7h: +1;
- recorded sleep quality <=2/5: +1;
- self-reported energy <=2/5: +2;
- self-reported focus <=2/5: +1;
- recorded intensity >=4/5 training within 12h: +1.

0 points with at least sleep/state evidence => `normal_capacity` (60-minute initial block).
1–2 => `moderate_capacity` (40 minutes).
3+ => `reduced_capacity` (25 minutes).
No sleep and no recent state input => `unknown_capacity` (neutral 45-minute default).

These are scheduling heuristics, not medical, sleep, recovery, or nutrition assessments.

## Focus mode / AdGuard Home

AdGuard Home credentials live only in environment variables. Life OS:
1. reads the current AdGuard Home user-rule list;
2. preserves every pre-existing rule;
3. adds exact rules for enabled Life OS focus domains;
4. logs the intervention and expiry time;
5. removes only exact Life OS rules when focus mode is released/expired.

Network-rule changes require explicit confirmation. Soft distraction recommendations are based only on activity events already labelled `distraction` by explicit user rules; the recommendation never auto-enables blocking.

The server checks active focus-mode expiry every 60 seconds when AdGuard Home is configured. An AdGuard outage does not stop the Life OS server.

## Dashboard

The local dashboard now supports:
- quick task creation and completion;
- energy/focus check-ins;
- sleep logging;
- weekly-plan generation;
- current planning-load display;
- focus-domain configuration and explicit focus-mode apply/release;
- normal task/calendar/next-action views.

Advanced controls remain available at `/docs`.
