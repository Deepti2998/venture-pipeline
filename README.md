# Venture Pipeline

Small, replayable investment triage pipeline for the Emergence take-home assignment.

The pipeline takes a seed topic, sources 10-20 startups from public data, runs a structured thesis-based analysis, and writes partner-skimmable memos with traceable evidence.

## Quick Start

```powershell
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12 --out outputs/sample-ai-agents-for-smbs
```

Outputs:

- `candidates.json`: normalized source records
- `analysis.json`: structured analysis and scoring
- `memos/*.md`: one memo per startup
- `run_report.md`: summary of calls, scores, warnings, and source coverage
- `ai_trace.jsonl`: records whether heuristic or LLM analysis was used

## Requirements

- Python 3.10+
- Public internet access to the YC OSS API
- Optional: `OPENAI_API_KEY` and `OPENAI_MODEL` if you want LLM prose enrichment

The default run does not require paid APIs. It uses a deterministic analyst so reviewers can run one command without credentials. If an OpenAI key is present and `--llm auto` is used, the pipeline asks the model to tighten the memo sections while keeping the same source evidence and score.

## Source Choice

Primary source: YC public company directory via `yc-oss/api`.

This intentionally goes deep on one source rather than shallow across many. The source gives company name, site, one-liner, long description, batch, status, stage, hiring, team size, industry, tags, and durable YC profile URL. That is enough to satisfy the assignment's sourcing fields while keeping claims traceable.

Optional source: Hacker News Algolia search. It is implemented behind `--sources yc,hn`, but the submitted sample uses YC only because the HN API can be flaky from some networks and the rubric explicitly allows one strong source.

## Common Commands

```powershell
# Run sample topic through the YC W25 feed
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --limit 12

# Search all YC public companies for a topic
python -m venture_pipeline run --topic "vertical AI agents for healthcare billing" --limit 15

# Force deterministic analysis even if an API key is set
python -m venture_pipeline run --topic "AI agents for SMBs" --yc-batch W25 --llm never

# Run tests
python -m unittest discover -s tests
```

## Submission Notes

Before submitting:

- Commit generated outputs so reviewers do not need to rerun.
- Record a five minute walkthrough showing one startup end-to-end.
- Add `chiragmakkar` and `hari@emsoft.com` as collaborators if the GitHub repo is private.
- Read `docs/AI_WORKFLOW.md` and add your own first-person notes if you want personal reflection. The file currently states what Codex generated and why; do not pretend it is a handwritten reflection.
