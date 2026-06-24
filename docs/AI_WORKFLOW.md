# Process Record

This file is an honest process note for reviewers. It should stay accurate; do not edit it to imply the work was unaided.

## Build Trail

- The assignment was scoped around one deep public source, YC's public company directory, plus optional Hacker News and URL-list adapters.
- The pipeline is deterministic by default: sourcing, scoring, and recommendations can run without paid APIs.
- OpenAI enrichment is optional. When enabled, it rewrites memo prose through the Responses API while preserving evidence, scores, and calls.
- Generated sample output was produced by the CLI and committed so reviewers can inspect artifacts without rerunning.

## Design Decisions

- One source deep: YC has enough structured fields to produce traceable candidate records.
- Deterministic first: optional model calls polish writing, but do not own the investment decision.
- Traceable claims: every memo includes evidence links and source snippets. Missing founder background data is called out instead of invented.
- Small system: no database, queue, vector store, or frontend. The pipeline writes JSON and Markdown artifacts.

## AI Use Boundaries

AI assistance was used to scaffold and revise the codebase. The assignment explicitly rewards honest visibility into that workflow, so this repo does not attempt to hide it.

Before submission, add a short note in your own words covering:

- Which files you reviewed.
- Which design choices you agree with or changed.
- What you would improve with more time.

## Review Trail

The files that best show the work are:

- `venture_pipeline/sources/yc.py` for source scoping and normalization.
- `venture_pipeline/sources/url_list.py` for explicit URL input support.
- `venture_pipeline/analysis/scoring.py` for thesis-to-score logic.
- `venture_pipeline/analysis/heuristic.py` for memo reasoning without hidden facts.
- `venture_pipeline/analysis/llm.py` for bounded OpenAI enrichment.
- `outputs/sample-ai-agents-for-smbs/run_report.md` for a generated run summary.
- `outputs/sample-ai-agents-for-smbs/ai_trace.jsonl` for analyst mode per memo.
