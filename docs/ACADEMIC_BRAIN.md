# Academic Brain

## Purpose

Academic Brain turns the user's actual university material into a grounded learning system. It is not a generic chatbot with a module name pasted into the prompt.

The evidence chain is:

```text
course document
  -> local extraction
  -> metadata + chunks
  -> SQLite FTS retrieval
  -> validated source set
  -> optional AI synthesis
  -> citation validation
  -> answer / task / revision recommendation
```

## Ingestion

Supported file formats are PDF, TXT, Markdown, DOCX and PPTX.

Each course document stores:
- title
- module
- week
- topic
- document type
- source
- academic year
- original filename
- SHA-256
- ingestion timestamp

Chunks preserve the source document and page/slide number where available.

The dashboard supports multi-file upload. The CLI supports recursive whole-folder import:

```powershell
python -m app.cli.import_course_folder "C:\University\Aerodynamics" --module "Aerodynamics" --academic-year "2026/27" --dry-run
python -m app.cli.import_course_folder "C:\University\Aerodynamics" --module "Aerodynamics" --academic-year "2026/27"
```

## Source hierarchy

Retrieval uses deterministic source priorities:
1. handbook
2. syllabus / coursework specification / marking criteria
3. lecture material
4. tutorials / worked examples
5. lab material
6. revision material
7. personal notes
8. other

FTS relevance is used within the source-priority boundary.

This hierarchy does not silently resolve an actual conflict. Conflicting explicit dates or percentages are surfaced.

## Grounded Q&A

`POST /api/academic/ask` retrieves a bounded source set.

With no AI provider configured, Life OS returns a local extractive answer with source IDs.

With a provider configured, the provider receives only the user question plus retrieved source blocks and a strict system instruction. Every source-derived substantive claim is expected to cite a valid source ID such as `[S1]`.

Provider citations are validated against the actual retrieved set. Invented source IDs reject the synthesis and trigger extractive fallback.

General model knowledge is disabled by default. The caller must explicitly set `allow_general_knowledge=true`. General knowledge must be separately labelled and cannot inherit course citations.

## Prompt-injection boundary

Uploaded documents are evidence, not instructions.

Instruction-like text such as “ignore previous instructions”, attempts to redefine the assistant, or references to hidden/system prompts is flagged. Such sentences are excluded from extractive answers. The optional AI provider is explicitly told to ignore commands found inside retrieved SOURCE blocks.

## Learning objectives and assessments

Deterministic structure extraction looks for explicit learning-outcome language and explicit assessment facts.

Academic Brain can persist:
- learning objectives
- assessment title/type
- explicit deadline
- explicit percentage weighting
- source document/chunk/page
- marking-criteria excerpts

It does not infer that an item is assessed merely because a topic appears in lecture material.

## Coursework breakdown

Assessment breakdown produces concrete actions such as:
- build an explicit requirements checklist;
- address each available marking criterion;
- produce a complete first pass;
- audit the work against the brief;
- run a final submission-readiness check.

Planner tasks are created only with `create_tasks=true`. Created tasks are labelled `AI_RECOMMENDATION`, not fact.

## Revision engine

Revision priorities combine:
- recorded study-attempt evidence;
- weak/developing/retrieval-due status;
- explicit learning objectives with no measured attempt;
- explicit upcoming assessment deadlines.

A learning objective with no attempt becomes `unmeasured`, not “weak”.

## Mistakes

Mistakes are stored separately from attempts so recurring misconceptions can be reviewed without rewriting attempt history. A mistake remains unresolved until explicitly resolved.

## Quizzes

Current built-in quiz generation is retrieval practice: questions and answer keys are tied to uploaded source chunks. Answer keys are source excerpts, not fabricated reference answers.

## Limitations

- Scanned/image-only PDFs may have little or no extractable text; OCR is not currently built into the ingestion service.
- Extraction heuristics intentionally prefer false negatives over inventing syllabus structure.
- Local extractive mode is grounded but less conversational than an optional AI provider.
- Academic Brain does not currently parse mathematical diagrams or images embedded in slides as semantic content.
