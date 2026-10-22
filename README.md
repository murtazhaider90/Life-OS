# Personal AI Life OS — Phase 4/5 milestone

A local-first, single-user system for evidence-based planning, academic retrieval, privacy-minimal behavioral tracking, context-aware scheduling, and explicit focus interventions.

## What works now

- Provenance-aware tasks, calendar, study sessions, learning attempts, course-document retrieval, daily planning and versioned weekly planning.
- Weak-topic and retrieval-due heuristics from recorded attempts only.
- Dynamic replanning with missed-block and capacity-shortfall reporting.
- Morning briefing with one next action.
- Local app/domain activity sampling with explicit user rules for study/distraction/neutral.
- Sleep, training and meal context records.
- Deterministic planning-load signal that uses recorded sleep/state/training data and leaves missing data unknown.
- Dashboard forms for task creation, task completion, energy/focus check-ins, sleep logging and weekly-plan generation.
- Optional AdGuard Home focus mode with explicit confirmation, rule preservation, automatic expiry reconciliation and manual release.
- Focus-mode recommendation based only on explicitly-labelled distraction activity.
- Weekly context summaries alongside academic/behavioral/planning reviews.
- GitHub CI on Python 3.11 and 3.14.
- Provider-neutral `AIProvider`; core planning does not require a cloud AI vendor.

## Run locally on Windows

```powershell
cd "C:\Users\Murtaza Haider\Life-OS"
.venv\Scripts\Activate.ps1
git pull
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://127.0.0.1:8000`. Advanced API controls remain at `/docs`.

## Optional AdGuard Home

Leave the AdGuard settings blank unless you actually run AdGuard Home. When ready, put these in `.env`:

```text
LIFE_OS_ADGUARD_BASE_URL=http://192.168.1.10:3000
LIFE_OS_ADGUARD_USERNAME=...
LIFE_OS_ADGUARD_PASSWORD=...
```

Credentials are read from the environment and are not stored in the Life OS database.

## Evidence boundaries

Planning-load outputs are scheduling heuristics, not medical, sleep, nutrition, or recovery assessments. Missing sleep/state data produces `unknown_capacity`, not a fabricated normal state. Unlabelled app/site activity is not distraction. Network blocking never starts from an AI inference and requires an explicit user action.
