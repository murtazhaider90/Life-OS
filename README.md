# Personal AI Life OS — Academic Brain milestone

A local-first, single-user planning and learning system that combines a Windows voice/text sidecar, evidence-based scheduling, private course-material retrieval, revision intelligence and optional AI synthesis.

## Academic Brain

Academic Brain can ingest your university material and make it usable across the rest of Life OS.

Supported inputs:
- PDF
- Word (`.docx`)
- PowerPoint (`.pptx`)
- TXT / Markdown

It supports module handbooks, syllabi, lecture material, tutorials, problem sheets, worked examples, coursework briefs, marking criteria, lab material, personal notes and revision resources.

Academic Brain can:
- retrieve relevant passages with document/page metadata;
- answer questions from uploaded course material;
- detect explicit learning objectives;
- extract explicit assessment deadlines/weights when the document states them;
- expose conflicting source facts instead of silently choosing one;
- break coursework into concrete actions;
- build revision priorities from recorded attempts, explicit learning objectives and assessment deadlines;
- track mistakes;
- generate source-backed retrieval questions;
- surface weak and retrieval-due topics;
- create planner tasks only when you explicitly request task creation.

Missing information remains missing. A syllabus requirement, assessment rule or citation is never invented.

## Import a whole module folder

Preview first:

```powershell
python -m app.cli.import_course_folder "C:\University\Aerodynamics" --module "Aerodynamics" --academic-year "2026/27" --dry-run
```

Then ingest:

```powershell
python -m app.cli.import_course_folder "C:\University\Aerodynamics" --module "Aerodynamics" --academic-year "2026/27"
```

Subfolders named like `Week 3` are recorded as week metadata. Other subfolder names can become topic metadata.

You can also upload multiple files from the Academic Brain section on the local dashboard.

## Academic assistant commands

Examples:

```text
Explain boundary layer separation from my course material
What do my notes say about Bernoulli?
Quiz me on compressible flow
What are my weak topics?
Make a revision plan
Make a revision plan and create tasks
Break down assessment Wing Design Coursework
Break down assessment Wing Design Coursework and create tasks
Record mistake Aerodynamics | Boundary layers | Used the wrong pressure-gradient sign
```

The Windows sidecar remains available with **Ctrl + Alt + Space**.

## AI modes

By default Academic Brain works in **local extractive mode**. Retrieval, citations, syllabus structure, revision logic and task breakdown do not require a cloud model.

For richer synthesis/tutoring, Life OS has an optional provider-neutral chat-completions adapter configured through `LIFE_OS_AI_BASE_URL`, `LIFE_OS_AI_MODEL` and optional `LIFE_OS_AI_API_KEY`.

Even with a provider configured:
- retrieved course documents are untrusted evidence, never instructions;
- course-derived claims must use retrieved source IDs;
- invented source IDs are rejected;
- if provider synthesis fails verification, Life OS falls back to extractive mode.

## Run on Windows

```powershell
cd "C:\Users\Murtaza Haider\Life-OS"
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File .\windows\start_life_os.ps1
```

Dashboard: `http://127.0.0.1:8000`.

## Evidence boundary

Academic priority is:

```text
official handbook / syllabus / coursework / marking material
> lecturer material
> tutorials / worked examples
> personal notes
> general model knowledge (only when explicitly allowed)
```

Life OS distinguishes recorded facts/observations from AI recommendations. Academic Brain does not turn generated text into permanent course facts.
